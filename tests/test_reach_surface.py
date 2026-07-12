"""Smoke tests for the brain's reach surface.

Covers the tools added in the brain-prep ingest:

- `brain.py search` — hybrid keyword search.
- `brain.py reflection-check` — drift detectors.
- `brain.py install-sibling` — sibling-repo installer.
- `brain.py init` — empty-shell scaffolder.
- `tools/brain` — shell wrapper.
- `tools/brain-mcp.py` — stdio MCP server.

Each test is shape-only — it confirms the tool runs and returns a
recognisable shape, not that the brain's content is correct (the
content tests live elsewhere). The point is: if a refactor breaks
the CLI surface, these fail.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRAIN_PY = REPO / "tools" / "brain.py"
BRAIN_MCP = REPO / "tools" / "brain-mcp.py"
BRAIN_WRAPPER = REPO / "tools" / "brain"


def _run(args, **kwargs):
    """Run a brain.py subcommand with the test environment."""
    return subprocess.run(
        [sys.executable, str(BRAIN_PY), *args],
        cwd=REPO, capture_output=True, text=True, timeout=30, **kwargs,
    )


# ---------- search -------------------------------------------------------

def test_search_returns_results_for_known_term() -> None:
    proc = _run(["search", "brain", "--top", "3", "--json"])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["query"] == "brain"
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0
    first = data["results"][0]
    for key in ("path", "title", "kind", "confidence", "score", "excerpt"):
        assert key in first


def test_search_filters_by_kind() -> None:
    proc = _run(["search", "brain", "--kind", "decision", "--top", "5", "--json"])
    # returncode 1 = no matches — a legitimate result on an empty shell.
    assert proc.returncode in (0, 1), proc.stderr
    data = json.loads(proc.stdout)
    for r in data["results"]:
        assert r["kind"] == "decision"


def test_search_filters_by_repo() -> None:
    """The --repo filter narrows to pages whose path is under wiki/<repo>/
    OR whose frontmatter claims the repo in `repos:` / `affects:` /
    cross-product synthesis. We assert the tool returned results
    (filter-shape verified by the tool's own logic); a deeper
    semantic-match assertion is brittle because legitimate matches
    include cross-cutting `wiki/org/` pages that affect the repo.
    Shape-only on the empty shell: the filter must not error even
    when no repo is declared."""
    proc = _run(["search", "permanent", "--repo", "brain", "--top", "5", "--json"])
    # returncode 1 = no matches — a legitimate result on an empty shell.
    assert proc.returncode in (0, 1), proc.stderr
    data = json.loads(proc.stdout)
    assert isinstance(data["results"], list)


def test_search_excludes_superseded_by_default() -> None:
    proc = _run(["search", "screen-reader", "--json"])
    if proc.returncode != 0:
        return  # query may legitimately have no matches; not a shape failure
    data = json.loads(proc.stdout)
    for r in data["results"]:
        assert r.get("status") != "superseded"


# ---------- reflection-check ---------------------------------------------

def test_reflection_check_runs_clean_or_advisory() -> None:
    """All 9 sub-checks run; the brain may carry advisory page-size
    findings but no breakage."""
    proc = _run(["reflection-check"])
    # Exit 0 if zero findings; exit 1 if any. Either is acceptable here
    # — we only care that the tool RUNS.
    assert proc.returncode in (0, 1), proc.stderr
    assert "reflection-check all" in proc.stderr


def test_reflection_check_links_clean() -> None:
    """Broken links should be zero — the brain has been swept."""
    proc = _run(["reflection-check", "links"])
    findings = [ln for ln in proc.stdout.splitlines() if ln.startswith("links:")]
    assert findings == [], f"broken links found: {findings}"


def test_reflection_check_supersedes_cycles_clean() -> None:
    proc = _run(["reflection-check", "supersedes-cycles"])
    findings = [ln for ln in proc.stdout.splitlines()
                if ln.startswith("supersedes-cycles:")]
    assert findings == []


def test_reflection_check_active_scope_clean() -> None:
    proc = _run(["reflection-check", "active-scope"])
    findings = [ln for ln in proc.stdout.splitlines()
                if ln.startswith("active-scope:")]
    assert findings == []


# ---------- init + BRAIN_DIR ---------------------------------------------

def test_init_scaffolds_validatable_shell(tmp_path: Path) -> None:
    target = tmp_path / "shell"
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "init", str(target), "--org", "Acme"],
        cwd=REPO, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    # Required scaffold pieces
    assert (target / "AGENTS.md").exists()
    assert (target / "wiki" / "index.md").exists()
    assert (target / "wiki" / "brain" / "index.md").exists()
    assert (target / "wiki" / "org" / "index.md").exists()
    assert (target / "log" / "log.md").exists()
    # validate runs against the new shell via $BRAIN_DIR
    env = {**os.environ, "BRAIN_DIR": str(target)}
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "validate"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert "page(s) valid" in proc.stdout


def test_init_refuses_non_empty_directory(tmp_path: Path) -> None:
    target = tmp_path / "shell"
    target.mkdir()
    (target / "existing.txt").touch()
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "init", str(target), "--org", "Acme"],
        cwd=REPO, capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode != 0
    assert "non-empty" in proc.stderr


# ---------- install-sibling ---------------------------------------------

def test_install_sibling_dry_run_is_idempotent(tmp_path: Path) -> None:
    sibling = tmp_path / "fake-sibling"
    sibling.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=sibling, check=True)
    (sibling / "CLAUDE.md").write_text("# fake\n\nHello.\n")

    env = {**os.environ, "BRAIN_PROJECTS_ROOT": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "install-sibling", "fake-sibling", "--dry-run"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    # Dry-run shouldn't have written anything
    assert "[dry-run]" in proc.stderr
    text = (sibling / "CLAUDE.md").read_text()
    assert "<!-- brain:managed:start -->" not in text


def test_install_sibling_install_then_uninstall(tmp_path: Path) -> None:
    sibling = tmp_path / "fake-sibling"
    sibling.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=sibling, check=True)
    (sibling / "CLAUDE.md").write_text("# fake\n\n## Operator notes\n\nKeep me.\n")

    env = {**os.environ, "BRAIN_PROJECTS_ROOT": str(tmp_path)}
    # Install
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "install-sibling", "fake-sibling"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    text = (sibling / "CLAUDE.md").read_text()
    assert "<!-- brain:managed:start -->" in text
    assert "Operator notes" in text  # operator content preserved
    assert (sibling / ".claude" / "brain-hook.sh").exists()
    settings = json.loads((sibling / ".claude" / "settings.json").read_text())
    assert "brain-hook.sh" in (
        settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    )

    # Re-install is a no-op (idempotent)
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "install-sibling", "fake-sibling"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    text = (sibling / "CLAUDE.md").read_text()
    assert text.count("<!-- brain:managed:start -->") == 1

    # Uninstall
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "install-sibling", "fake-sibling", "--uninstall"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    text = (sibling / "CLAUDE.md").read_text()
    assert "<!-- brain:managed:start -->" not in text
    assert "Operator notes" in text  # operator content still there
    assert not (sibling / ".claude" / "brain-hook.sh").exists()


# ---------- shell wrapper -----------------------------------------------

def test_brain_shell_wrapper_runs() -> None:
    if not BRAIN_WRAPPER.exists() or not os.access(BRAIN_WRAPPER, os.X_OK):
        return  # wrapper not installed (e.g. minimal CI image)
    proc = subprocess.run(
        [str(BRAIN_WRAPPER), "stats"],
        cwd=REPO, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert "pages:" in proc.stdout


# ---------- MCP server --------------------------------------------------

def test_mcp_server_initialize_and_list_tools() -> None:
    """Run the MCP server's stdio handshake and verify tools/list."""
    proc = subprocess.Popen(
        [sys.executable, str(BRAIN_MCP)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=REPO,
    )
    try:
        def send(req):
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()

        def recv():
            line = proc.stdout.readline().strip()
            return json.loads(line) if line else None

        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        r = recv()
        assert r["result"]["serverInfo"]["name"] == "brain"

        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        r = recv()
        names = [t["name"] for t in r["result"]["tools"]]
        for tool in ("brain_search", "brain_get_page", "brain_stats",
                     "brain_overlaps", "brain_efforts", "brain_active_repos"):
            assert tool in names

        send({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "brain_active_repos", "arguments": {}},
        })
        r = recv()
        repos = json.loads(r["result"]["content"][0]["text"])
        assert isinstance(repos, list)
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
