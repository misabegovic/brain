"""Tests for the app page + install-agent adapters (per
wiki/brain/adrs/mcp-cli-surface.md: no embedded
terminal — the app is the rendered knowledge under an ambient strip)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def test_install_agent_idempotent_and_preserving(tmp_path):
    # Existing unrelated JSON keys survive the merge.
    cursor_cfg = tmp_path / ".cursor" / "mcp.json"
    cursor_cfg.parent.mkdir()
    cursor_cfg.write_text(json.dumps(
        {"mcpServers": {"other": {"command": "keep-me"}}}))
    assert brain.install_agent("cursor", tmp_path) == "wrote"
    assert brain.install_agent("cursor", tmp_path) == "unchanged"
    data = json.loads(cursor_cfg.read_text())
    assert data["mcpServers"]["other"]["command"] == "keep-me"
    assert data["mcpServers"]["brain"]["command"] == "python3"


def test_install_agent_toml_fence_replaces_not_duplicates(tmp_path):
    toml = tmp_path / ".codex" / "config.toml"
    toml.parent.mkdir()
    toml.write_text('[model]\nname = "keep"\n')
    assert brain.install_agent("codex", tmp_path) == "wrote"
    assert brain.install_agent("codex", tmp_path) == "unchanged"
    text = toml.read_text()
    assert text.count(brain.AGENT_SENTINEL_OPEN) == 1
    assert '[model]' in text and 'keep' in text
    assert "[mcp_servers.brain]" in text


def test_app_page_has_no_terminal():
    """The embedded terminal is gone: no websocket, no xterm, no
    harness-launch buttons — knowledge iframe + strip only."""
    html = brain.render_app_page(["engineer"])
    for gone in ("WebSocket", "xterm", "/pty", "spawn(", 'id="term"'):
        assert gone not in html, f"terminal remnant in app page: {gone}"
    assert 'id="strip"' in html and 'id="page"' in html
    assert ">briefing</button>" in html and ">engineer</button>" in html


def test_serving_mode_hides_app_page():
    port = 8987
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--port", str(port)],
        env={**os.environ, "BRAIN_SERVING": "1"}, stderr=subprocess.PIPE)
    try:
        import urllib.error
        import urllib.request
        code = None
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                code = urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api", timeout=5).status
                break
            except (urllib.error.URLError, ConnectionError):
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        assert code == 200, "server never became ready"
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{port}/workbench", timeout=5)
            raise AssertionError("app page must not mount in serving mode")
        except urllib.error.HTTPError:
            pass
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_app_page_serves_locally():
    port = 8988
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--port", str(port)], stderr=subprocess.PIPE)
    try:
        import urllib.error
        import urllib.request
        page = None
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                page = urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/workbench",
                    timeout=5).read().decode()
                break
            except (urllib.error.URLError, ConnectionError):
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        assert page is not None, "app page never became ready"
        assert 'id="strip"' in page
        status = json.loads(urllib.request.urlopen(
            f"http://127.0.0.1:{port}/workbench/status",
            timeout=5).read())
        for key in ("inbox", "fails", "warns", "mtime"):
            assert key in status
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_ui_route_serves_rendered_wiki():
    port = 8992
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--port", str(port)], stderr=subprocess.PIPE)
    try:
        import urllib.error
        import urllib.request
        deadline = time.time() + 15
        status = None
        while time.time() < deadline:
            try:
                status = urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/ui/", timeout=5).status
                break
            except (urllib.error.URLError, ConnectionError):
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        assert status == 200, "rendered wiki should serve at /ui/"
        page = urllib.request.urlopen(
            f"http://127.0.0.1:{port}/ui/brain/roadmap/",
            timeout=5).read().decode()
        assert "roadmap" in page.lower()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_version_flag():
    out = subprocess.run(
        [sys.executable, str(REPO / "tools" / "brain.py"), "--version"],
        capture_output=True, text=True, timeout=10)
    assert out.returncode == 0
    assert out.stdout.strip() == \
        f"brain {(REPO / 'VERSION').read_text().strip()}"


def test_page_context_briefing():
    ctx = brain.page_context("brain/roadmap.md")
    assert "brain/index.md" in ctx["backlinks"]
    assert any("adrs" in o for o in ctx["outbound"])
    rendered = brain.render_page_context("brain/roadmap.md")
    assert "backlinks:" in rendered


def test_lint_page_flags_broken_link(tmp_path):
    class _Args:
        path = ""

    rogue = REPO / "wiki" / "_test_lint_page.md"
    rogue.write_text("---\ntitle: t\nkind: meta\nstatus: draft\n"
                     "updated: 2026-07-10\nsources: []\n---\n"
                     "[bad](./no-such-page.md)\n")
    try:
        _Args.path = str(rogue)
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert brain.cmd_lint_page(_Args()) == 0
        assert "broken link" in buf.getvalue()
    finally:
        rogue.unlink()


def test_no_pty_module_ships():
    """The kernel must not carry a PTY/websocket bridge anywhere —
    the decision is structural absence, not a disabled flag."""
    assert not (REPO / "tools" / "workbench.py").exists()
    text = (REPO / "tools" / "brain.py").read_text()
    for gone in ("openpty", "Sec-WebSocket", "TERMINAL_CLIS",
                 "billing_safe_env"):
        assert gone not in text, f"PTY remnant in brain.py: {gone}"


def test_ui_action_endpoint_queues_inbox_item():
    import urllib.request
    port = 8993
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--port", str(port)], stderr=subprocess.PIPE)
    created = []
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api", timeout=5)
                break
            except OSError:
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/act",
            data=json.dumps({"action": "comment",
                             "target": "wiki/brain/roadmap.md",
                             "note": "test comment"}).encode(),
            headers={"X-Brain-Act": "1",
                     "Content-Type": "application/json"},
            method="POST")
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
        item_id = resp["queued"]
        created.append(item_id)
        item = json.loads(
            (REPO / "wiki" / "_state" / "inbox" / f"{item_id}.json")
            .read_text())
        assert item["produced_by"] == "ui-action"
        assert "test comment" in item["summary"]
        # Without the custom header the request is refused (CSRF guard).
        bare = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/act",
            data=b'{"action":"comment","note":"x"}', method="POST")
        try:
            urllib.request.urlopen(bare, timeout=5)
            raise AssertionError("action without header must 403")
        except urllib.error.HTTPError as e:
            assert e.code == 403
    finally:
        for iid in created:
            (REPO / "wiki" / "_state" / "inbox" / f"{iid}.json").unlink(
                missing_ok=True)
        proc.terminate()
        proc.wait(timeout=5)


def test_ui_action_absent_in_serving_mode():
    import urllib.request
    port = 8994
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--port", str(port)],
        env={**os.environ, "BRAIN_SERVING": "1"}, stderr=subprocess.PIPE)
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api", timeout=5)
                break
            except OSError:
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/act",
            data=b'{"action":"comment","note":"x"}',
            headers={"X-Brain-Act": "1"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=5)
            raise AssertionError("act must not mount in serving mode")
        except urllib.error.HTTPError as e:
            assert e.code == 405
    finally:
        proc.terminate()
        proc.wait(timeout=5)
