"""Tests for the 0.3 connector contract (pull-only snapshot-writers).

Live API paths are exercised manually; these tests pin the contract
mechanics: no-op when unconfigured, immutable dedup snapshot writes,
cursor round-trip, and watched-repo discovery parsing.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def _git_repo(path: Path, files: dict[str, str]) -> None:
    """Init a throwaway git repo with the given tracked files."""
    path.mkdir(parents=True, exist_ok=True)
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", "init", "-q"], cwd=path, env=env, check=True)
    for rel, content in files.items():
        p = path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=path, env=env, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=path, env=env, check=True)


def test_connectors_noop_when_unconfigured():
    assert brain._connector_github_pull() == 0
    assert brain._connector_notion_pull() == 0
    assert brain._connector_slack_pull() == 0


def test_connector_config_reads_yaml_section():
    cfg = brain._connector_config("github")
    assert isinstance(cfg, dict)
    assert brain._connector_config("no-such-connector") == {}


def test_snapshot_write_is_immutable_dedup():
    rel = "_test/snapshot--t1.md"
    path = REPO / "sources" / "_test-connector" / rel
    try:
        first = brain._snapshot_write("_test-connector", rel, "t", "body one")
        assert first is not None and first.exists()
        assert "body one" in first.read_text()
        assert first.read_text().startswith("---\n")
        second = brain._snapshot_write("_test-connector", rel, "t", "body two")
        assert second is None, "existing snapshots must never be rewritten"
        assert "body one" in first.read_text()
    finally:
        if path.exists():
            path.unlink()
            path.parent.rmdir()
            path.parent.parent.rmdir()


def test_connector_cursors_round_trip():
    assert not brain.CONNECTOR_CURSORS.exists(), (
        "test assumes no live connector cursors; adjust if configured"
    )
    try:
        brain._write_connector_cursors({"github": {"o/r": {"last_pull": "2026-01-01"}}})
        data = brain._read_connector_cursors()
        assert data["github"]["o/r"]["last_pull"] == "2026-01-01"
    finally:
        brain.CONNECTOR_CURSORS.unlink(missing_ok=True)


def test_env_reads_dotenv_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("T_CONNECTOR_TOKEN", raising=False)
    assert brain._env("T_CONNECTOR_TOKEN") == ""
    monkeypatch.setenv("T_CONNECTOR_TOKEN", "from-env")
    assert brain._env("T_CONNECTOR_TOKEN") == "from-env"


# --- structure connector (0.21) --------------------------------------

def test_structure_connector_noops_when_unconfigured():
    # active_repos is empty on the dogfooding instance and no structure
    # repos are configured, so the connector is a clean no-op.
    assert brain._structure_targets() == []
    assert brain._connector_structure_pull() == 0


def test_extract_structure_is_exact_and_deterministic(tmp_path):
    repo = tmp_path / "r"
    _git_repo(repo, {
        "pkg/main.py": "import os\n\ndef run():\n    pass\n\nclass Engine:\n    pass\n",
        "pkg/util.py": "def helper():\n    return 1\n",
        "web/app.js": "export function boot() {}\n",
        "README.md": "# docs\n",
    })
    facts = brain._extract_structure(repo)
    # Only source files count as modules; docs are ignored.
    assert facts["modules"] == ["pkg/main.py", "pkg/util.py", "web/app.js"]
    assert facts["packages"] == {"pkg": 2, "web": 1}
    # Python symbols are exact (sorted); JS gets file-level tracking only.
    assert facts["symbols"] == {
        "pkg/main.py": ["Engine", "run"], "pkg/util.py": ["helper"]}
    assert "web/app.js" not in facts["symbols"]
    # The snapshot id is stable across identical extractions.
    assert brain._structure_snapshot_id(facts) == \
        brain._structure_snapshot_id(brain._extract_structure(repo))


def test_structure_drift_reports_module_and_symbol_deltas():
    prev = {"modules": ["a.py"], "packages": {".": 1},
            "symbols": {"a.py": ["f"]}}
    cur = {"modules": ["a.py", "b.py"], "packages": {".": 2},
           "symbols": {"a.py": ["f", "g"], "b.py": ["h"]}}
    drift = brain._structure_drift(prev, cur)
    assert "+ module b.py" in drift
    assert "+ a.py :: g" in drift
    assert "+ b.py :: h" in drift
    removed = brain._structure_drift(cur, prev)
    assert "- module b.py" in removed
    assert "- a.py :: g" in removed
    # No change → no drift.
    assert brain._structure_drift(prev, prev) == []


def test_reconcile_clears_drift_only_when_snapshot_is_cited(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    inbox = tmp_path / "inbox"
    wiki.mkdir()
    inbox.mkdir()
    monkeypatch.setattr(brain, "WIKI", wiki)
    monkeypatch.setattr(brain, "INBOX_DIR", inbox)
    cited = "sources/structure/r/snap--abc123.md"
    (wiki / "arch.md").write_text(
        "---\ntitle: t\nkind: reference\nstatus: living\n"
        f"updated: 2026-07-14\nsources:\n  - {cited}\n---\n\nbody\n")

    def _drift_item(source):
        return json.dumps({
            "id": "structure-drift-r", "kind": "ingest", "summary": "x",
            "route": "", "priority": "normal", "source": source,
            "produced_by": "structure-pull", "produced_at": "2026-07-14"})

    # Cited snapshot → drift reconciled (cleared).
    (inbox / "structure-drift-r.json").write_text(_drift_item(cited))
    assert brain._reconcile_structure_drift() == 1
    assert not (inbox / "structure-drift-r.json").exists()

    # Un-cited snapshot → drift survives (still needs a human/tend).
    (inbox / "structure-drift-r.json").write_text(
        _drift_item("sources/structure/r/snap--zzz999.md"))
    assert brain._reconcile_structure_drift() == 0
    assert (inbox / "structure-drift-r.json").exists()


def test_structure_pull_snapshots_then_flags_drift(tmp_path, monkeypatch):
    target = tmp_path / "proj"
    _git_repo(target, {"pkg/mod.py": "def one():\n    pass\n"})
    monkeypatch.setattr(
        brain, "_connector_config",
        lambda name: {"repos": [str(target)]} if name == "structure" else {})
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    monkeypatch.setattr(brain, "INBOX_DIR", inbox)
    monkeypatch.setattr(brain, "CONNECTOR_CURSORS", tmp_path / "cursors.json")
    snapdir = brain.REPO / "sources" / "structure" / "proj"
    try:
        # First pull: one snapshot, no drift (no baseline yet).
        assert brain._connector_structure_pull() == 0
        assert len(list(snapdir.glob("snap--*.md"))) == 1
        assert not list(inbox.glob("structure-drift-*.json"))

        # Re-run with no code change: dedup holds, still one snapshot.
        assert brain._connector_structure_pull() == 0
        assert len(list(snapdir.glob("snap--*.md"))) == 1

        # Add a symbol, commit, pull again: new snapshot + drift item.
        (target / "pkg" / "mod.py").write_text(
            "def one():\n    pass\n\n\ndef two():\n    pass\n")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        subprocess.run(["git", "add", "-A"], cwd=target, env=env, check=True)
        subprocess.run(["git", "commit", "-qm", "y"], cwd=target, env=env,
                       check=True)
        assert brain._connector_structure_pull() == 0
        assert len(list(snapdir.glob("snap--*.md"))) == 2
        drift = inbox / "structure-drift-proj.json"
        assert drift.exists()
        item = json.loads(drift.read_text())
        assert item["produced_by"] == "structure-pull"
        assert "structural change" in item["summary"]
    finally:
        shutil.rmtree(snapdir, ignore_errors=True)
        parent = brain.REPO / "sources" / "structure"
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
