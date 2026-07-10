"""Tests for the workbench PTY bridge + install-agent adapters
(per wiki/brain/adrs/workbench-pty-bridge.md)."""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402
import workbench as wb  # noqa: E402


def test_ws_accept_key_rfc_vector():
    # RFC 6455 § 1.3 worked example.
    assert wb.ws_accept_key("dGhlIHNhbXBsZSBub25jZQ==") == \
        "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_terminal_clis_shape():
    names = [r["name"] for r in wb.TERMINAL_CLIS]
    assert names == sorted(set(names)), "registry rows must be unique+sorted"
    for row in wb.TERMINAL_CLIS:
        assert row["bin"] and isinstance(row["args"], list)


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


def test_workbench_refuses_serving_mode():
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--workbench", "--port", "8987"],
        env={**os.environ, "BRAIN_SERVING": "1"},
        capture_output=True, text=True, timeout=15)
    assert proc.returncode == 1
    assert "structurally excluded" in proc.stderr


def test_workbench_refuses_non_loopback():
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--workbench", "--host", "0.0.0.0", "--port", "8987"],
        capture_output=True, text=True, timeout=15)
    assert proc.returncode == 1
    assert "non-loopback" in proc.stderr


@pytest.mark.skipif(
    not (REPO / "ui/node_modules/@xterm/xterm").exists(),
    reason="xterm assets not installed")
def test_pty_round_trip_over_websocket():
    port = 8988
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"),
         "serve", "--workbench", "--port", str(port)],
        stderr=subprocess.PIPE)
    try:
        import urllib.error
        import urllib.request
        page = None
        last_exc = None
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                page = urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/workbench",
                    timeout=5).read().decode()
                break
            except (urllib.error.URLError, ConnectionError) as exc:
                last_exc = exc
                if proc.poll() is not None:
                    break
                time.sleep(0.3)
        if page is None:
            server_err = ""
            if proc.poll() is not None:
                server_err = proc.stderr.read().decode()[:1500]
            raise AssertionError(
                f"serve --workbench never became ready: {last_exc!r}; "
                f"server rc={proc.poll()} stderr={server_err!r}")
        import re
        token = re.search(r"token=([A-Za-z0-9_-]+)", page).group(1)

        s = socket.create_connection(("127.0.0.1", port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        s.sendall((f"GET /workbench/pty?token={token} HTTP/1.1\r\n"
                   f"Host: localhost:{port}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                   f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
        assert b"101" in s.recv(4096).split(b"\r\n")[0]

        def send(payload):
            data = json.dumps(payload).encode()
            mask = os.urandom(4)
            masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            header = bytes([0x81])
            n = len(data)
            if n < 126:
                header += bytes([0x80 | n])
            else:
                header += bytes([0x80 | 126]) + struct.pack(">H", n)
            s.sendall(header + mask + masked)

        def exact(n):
            buf = b""
            while len(buf) < n:
                c = s.recv(n - len(buf))
                if not c:
                    raise ConnectionError
                buf += c
            return buf

        def recv_frame():
            b1, b2 = exact(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", exact(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", exact(8))[0]
            return b1 & 0x0F, exact(n)

        send({"type": "input", "data": " echo WB_$((7*6))\n"})
        deadline = time.time() + 10
        out = ""
        while time.time() < deadline:
            op, payload = recv_frame()
            if op != 1:
                continue
            msg = json.loads(payload)
            if msg.get("type") == "data":
                out += msg["data"]
                if "WB_42" in out:
                    break
        assert "WB_42" in out, f"no echo through the PTY; got {out[-200:]!r}"
        send({"type": "kill"})
        s.close()
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


def test_run_chat_message_with_stub_registry():
    stub = [{"name": "echo", "bin": "echo",
             "first_args": ["first:"], "continue_args": ["cont:"]}]
    wb._chat_continuing.discard("echo")
    r1 = wb.run_chat_message("echo", "hello", cwd=str(REPO), registry=stub)
    assert r1["ok"] and r1["reply"] == "first: hello"
    r2 = wb.run_chat_message("echo", "again", cwd=str(REPO), registry=stub)
    assert r2["ok"] and r2["reply"] == "cont: again", \
        "second turn must use the continuation form"
    wb._chat_continuing.discard("echo")


def test_run_chat_message_rejects_unknown_and_missing():
    r = wb.run_chat_message("nope", "x", cwd=str(REPO), registry=[])
    assert not r["ok"] and "unknown" in r["reply"]
    r = wb.run_chat_message(
        "ghost", "x", cwd=str(REPO),
        registry=[{"name": "ghost", "bin": "no-such-bin-xyz",
                   "first_args": [], "continue_args": []}])
    assert not r["ok"] and "PATH" in r["reply"]


def test_chat_rows_shape():
    names = [r["name"] for r in wb.CHAT_CLIS]
    assert names == sorted(set(names))
    for row in wb.CHAT_CLIS:
        assert row["bin"] and isinstance(row["first_args"], list)
        assert isinstance(row["continue_args"], list)


def test_workbench_page_is_chat_first():
    html = wb.render_workbench_page("tok", wb.TERMINAL_CLIS, 40,
                                    ["engineer"], wb.CHAT_CLIS)
    assert "composer" in html and "toggleTerm" in html
    assert html.index("msgs") < html.index('id="term"'), \
        "chat renders before the terminal"
    assert 'value="claude"' in html
