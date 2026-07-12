"""Tests for the serving slice: MCP HTTP transport + serving-mode
guardrails (ai-suggestions exclusion, query audit log)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "brain_mcp", REPO / "tools" / "brain-mcp.py")
brain_mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain_mcp)


def test_serving_mode_flag(monkeypatch):
    monkeypatch.delenv("BRAIN_SERVING", raising=False)
    assert brain_mcp.serving_mode() is False
    monkeypatch.setenv("BRAIN_SERVING", "1")
    assert brain_mcp.serving_mode() is True


def test_get_page_rejects_ai_suggestions_in_serving_mode(monkeypatch):
    monkeypatch.setenv("BRAIN_SERVING", "1")
    with pytest.raises(ValueError, match="serving corpus"):
        brain_mcp.tool_brain_get_page(
            {"path": "brain/ai-suggestions/adrs/x.md"})
    monkeypatch.delenv("BRAIN_SERVING")
    # Outside serving mode the same path only fails on existence.
    with pytest.raises(ValueError, match="not found"):
        brain_mcp.tool_brain_get_page(
            {"path": "brain/ai-suggestions/adrs/x.md"})


def test_audit_log_appends_in_serving_mode(monkeypatch):
    log = REPO / "log" / "queries.log"
    before = log.read_text() if log.exists() else ""
    monkeypatch.setenv("BRAIN_SERVING", "1")
    try:
        brain_mcp.audit_query("brain_search", {"query": "test-audit"})
        lines = log.read_text().splitlines()
        entry = json.loads(lines[-1])
        assert entry["tool"] == "brain_search"
        assert entry["args"]["query"] == "test-audit"
    finally:
        if before:
            log.write_text(before)
        else:
            log.unlink(missing_ok=True)


def test_audit_log_silent_outside_serving_mode(monkeypatch):
    monkeypatch.delenv("BRAIN_SERVING", raising=False)
    log = REPO / "log" / "queries.log"
    existed = log.exists()
    brain_mcp.audit_query("brain_stats", {})
    assert log.exists() == existed


def test_http_transport_round_trip():
    port = 8978
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain-mcp.py"),
         "--http", "--port", str(port)],
        stderr=subprocess.PIPE)
    try:
        time.sleep(1.0)

        def post(body: dict, headers: dict | None = None):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/mcp",
                data=json.dumps(body).encode(),
                headers=headers or {})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read() or b"{}")

        status, init = post({"jsonrpc": "2.0", "id": 1,
                             "method": "initialize", "params": {}})
        assert status == 200
        assert init["result"]["serverInfo"]["name"] == "brain"

        status, tools = post({"jsonrpc": "2.0", "id": 2,
                              "method": "tools/list"})
        names = {t["name"] for t in tools["result"]["tools"]}
        assert "brain_search" in names

        with pytest.raises(urllib.error.HTTPError) as exc:
            post({"jsonrpc": "2.0", "id": 3, "method": "ping"},
                 {"Origin": "https://evil.example"})
        assert exc.value.code == 403
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_brain_serve_helpers_exclude_suggestions(monkeypatch):
    """brain.py's shared serving-mode exclusion covers pages.json
    (collect_pages_data) and search, matching the MCP."""
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "tools"))
    import brain
    monkeypatch.setenv("BRAIN_SERVING", "1")
    assert brain.serving_mode() is True
    assert brain._suggestion_path("brain/ai-suggestions/adrs/x.md") is True
    assert brain._suggestion_path("brain/adrs/x.md") is False
    paths = {e["path"] for e in brain.collect_pages_data()}
    assert not any("/ai-suggestions/" in ("/" + p) for p in paths), (
        "serving-mode pages.json must exclude ai-suggestion drafts")


def test_mcp_host_guard_is_uniform():
    """The MCP HTTP surface refuses a non-loopback Host, matching
    brain.py serve (Sam uniform-host-guard finding)."""
    import subprocess
    import sys as _sys
    import time
    import urllib.error
    import urllib.request
    from pathlib import Path as _P
    repo = _P(__file__).resolve().parent.parent
    port = 8796
    proc = subprocess.Popen(
        [_sys.executable, str(repo / "tools" / "brain-mcp.py"),
         "--http", "--port", str(port)], stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 12
        body = b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
        while time.time() < deadline:
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/mcp", data=body,
                    headers={"Host": "localhost", "Content-Type":
                             "application/json"}, method="POST")
                urllib.request.urlopen(req, timeout=3)
                break
            except urllib.error.HTTPError:
                break
            except OSError:
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        # Forged Host → 403.
        forged = urllib.request.Request(
            f"http://127.0.0.1:{port}/mcp", data=body,
            headers={"Host": "evil.example.com", "Content-Type":
                     "application/json"}, method="POST")
        try:
            urllib.request.urlopen(forged, timeout=3)
            raise AssertionError("forged Host must be refused")
        except urllib.error.HTTPError as e:
            assert e.code == 403
    finally:
        proc.terminate()
        proc.wait(timeout=5)
