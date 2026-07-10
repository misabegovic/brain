"""Workbench PTY bridge — loopback-only, stdlib-only.

Per wiki/brain/adrs/workbench-pty-bridge.md: terminal sessions keyed
by id (create/input/resize/kill/data/exit), spawning the operator's
own login shell; a minimal RFC-6455 slice (text frames, client
masking, ping/pong, close) carries JSON messages to the browser; a
per-process token plus a Host check gate every connection. Harness
launches are rows in TERMINAL_CLIS — commands are written to the PTY
directly so launch lines never enter shell history, and the one
user-influenced token is single-quoted. This module is mounted by
`brain.py serve --workbench` and is structurally absent from serving
deployments.
"""

from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
import pty
import secrets
import shlex
import struct
import subprocess
import termios
import threading

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# One row per harness: how to launch it inside the shell. The command
# is written to the PTY (prefixed with a space so even
# history-preserving shells with HIST_IGNORE_SPACE skip it), then the
# shell replaces itself back after exit via the trailing exec.
TERMINAL_CLIS = [
    {"name": "claude", "bin": "claude", "args": []},
    {"name": "codex", "bin": "codex", "args": []},
    {"name": "cursor", "bin": "cursor-agent", "args": []},
    {"name": "opencode", "bin": "opencode", "args": []},
]

SESSION_TOKEN = secrets.token_urlsafe(24)


class PtySession:
    """One terminal: the operator's login shell on a PTY pair."""

    def __init__(self):
        shell = os.environ.get("SHELL", "/bin/bash")
        self.master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            [shell, "-l", "-i"],
            stdin=slave, stdout=slave, stderr=slave,
            start_new_session=True,
            env={**os.environ, "TERM": "xterm-256color"},
        )
        os.close(slave)

    def write(self, data: str) -> None:
        os.write(self.master, data.encode())

    def launch_harness(self, name: str) -> bool:
        row = next((r for r in TERMINAL_CLIS if r["name"] == name), None)
        if row is None:
            return False
        cmd = shlex.join([row["bin"], *row["args"]])
        # Leading space: bypass history on HIST_IGNORE_SPACE shells.
        self.write(f" {cmd}\n")
        return True

    def resize(self, cols: int, rows: int) -> None:
        winsz = struct.pack("HHHH", max(2, rows), max(2, cols), 0, 0)
        fcntl.ioctl(self.master, termios.TIOCSWINSZ, winsz)

    def read(self, n: int = 65536) -> bytes:
        return os.read(self.master, n)

    def alive(self) -> bool:
        return self.proc.poll() is None

    def kill(self) -> None:
        if self.alive():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        os.close(self.master)


def ws_accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + WS_GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def ws_send(sock, payload: str, opcode: int = 0x1) -> None:
    data = payload.encode() if isinstance(payload, str) else payload
    header = bytes([0x80 | opcode])
    n = len(data)
    if n < 126:
        header += bytes([n])
    elif n < 65536:
        header += bytes([126]) + struct.pack(">H", n)
    else:
        header += bytes([127]) + struct.pack(">Q", n)
    sock.sendall(header + data)


def _recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("peer closed")
        buf += chunk
    return buf


def ws_recv(sock) -> tuple[int, bytes]:
    """One frame → (opcode, payload). Client frames must be masked."""
    b1, b2 = _recv_exact(sock, 2)
    opcode = b1 & 0x0F
    masked = b2 & 0x80
    n = b2 & 0x7F
    if n == 126:
        n = struct.unpack(">H", _recv_exact(sock, 2))[0]
    elif n == 127:
        n = struct.unpack(">Q", _recv_exact(sock, 8))[0]
    mask = _recv_exact(sock, 4) if masked else b"\x00" * 4
    payload = bytearray(_recv_exact(sock, n))
    for i in range(len(payload)):
        payload[i] ^= mask[i % 4]
    return opcode, bytes(payload)


def handle_ws_connection(handler) -> None:
    """Upgrade an http.server request to a PTY websocket session.

    `handler` is the BaseHTTPRequestHandler mid-GET. Token and Host
    were already checked by the caller. Runs until the socket or the
    shell dies; owns exactly one PtySession.
    """
    key = handler.headers.get("Sec-WebSocket-Key", "")
    handler.wfile.write(
        b"HTTP/1.1 101 Switching Protocols\r\n"
        b"Upgrade: websocket\r\nConnection: Upgrade\r\n"
        b"Sec-WebSocket-Accept: " + ws_accept_key(key).encode()
        + b"\r\n\r\n")
    handler.wfile.flush()
    sock = handler.connection
    session = PtySession()
    stop = threading.Event()

    def pump_output():
        try:
            while not stop.is_set() and session.alive():
                data = session.read()
                if not data:
                    break
                ws_send(sock, json.dumps(
                    {"type": "data",
                     "data": data.decode("utf-8", "replace")}))
        except (OSError, ConnectionError):
            pass
        finally:
            try:
                ws_send(sock, json.dumps({"type": "exit"}))
                ws_send(sock, b"", opcode=0x8)
            except (OSError, ConnectionError):
                pass

    pump = threading.Thread(target=pump_output, daemon=True)
    pump.start()
    try:
        while session.alive():
            opcode, payload = ws_recv(sock)
            if opcode == 0x8:  # close
                break
            if opcode == 0x9:  # ping → pong
                ws_send(sock, payload, opcode=0xA)
                continue
            if opcode != 0x1:
                continue
            try:
                msg = json.loads(payload)
            except json.JSONDecodeError:
                continue
            kind = msg.get("type")
            if kind == "input":
                session.write(msg.get("data", ""))
            elif kind == "resize":
                session.resize(int(msg.get("cols", 80)),
                               int(msg.get("rows", 24)))
            elif kind == "spawn":
                session.launch_harness(str(msg.get("harness", "")))
            elif kind == "kill":
                break
    except (ConnectionError, OSError):
        pass
    finally:
        stop.set()
        session.kill()


def render_workbench_page(token: str, harnesses: list[dict],
                          page_count: int) -> str:
    buttons = "".join(
        f'<button onclick="spawn(\'{h["name"]}\')">{h["name"]}</button>'
        for h in harnesses)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>brain · workbench</title>
<link rel="stylesheet" href="/workbench/assets/xterm.css">
<style>
 :root {{ color-scheme: light dark; }}
 body {{ margin: 0; font: 14px system-ui, sans-serif; display: flex;
        height: 100vh; }}
 #left {{ flex: 1 1 55%; border: 0; min-width: 20rem; }}
 #right {{ flex: 1 1 45%; display: flex; flex-direction: column;
          border-left: 1px solid #8884; }}
 #bar {{ padding: .4rem .6rem; display: flex; gap: .4rem;
        align-items: center; border-bottom: 1px solid #8884; }}
 #bar button {{ font: inherit; padding: .15rem .6rem; cursor: pointer; }}
 #bar .hint {{ opacity: .6; margin-left: auto; font-size: .85em; }}
 #term {{ flex: 1; min-height: 0; padding: .3rem; background: #000; }}
</style></head><body>
<iframe id="left" src="/dash"></iframe>
<div id="right">
 <div id="bar">
   <span>open in:</span>{buttons}
   <span class="hint">{page_count} pages · auto-reloads on wiki changes</span>
 </div>
 <div id="term"></div>
</div>
<script src="/workbench/assets/xterm.js"></script>
<script src="/workbench/assets/addon-fit.js"></script>
<script>
 const term = new Terminal({{fontSize: 13, scrollback: 5000}});
 const fit = new FitAddon.FitAddon();
 term.loadAddon(fit);
 term.open(document.getElementById('term'));
 fit.fit();
 const ws = new WebSocket(
   `ws://${{location.host}}/workbench/pty?token={token}`);
 ws.onmessage = (e) => {{
   const m = JSON.parse(e.data);
   if (m.type === 'data') term.write(m.data);
   if (m.type === 'exit') term.write('\\r\\n[session ended]\\r\\n');
 }};
 ws.onopen = () => {{
   ws.send(JSON.stringify({{type: 'resize', cols: term.cols,
                            rows: term.rows}}));
   term.focus();
 }};
 term.onData(d => ws.send(JSON.stringify({{type: 'input', data: d}})));
 new ResizeObserver(() => {{
   fit.fit();
   if (ws.readyState === 1)
     ws.send(JSON.stringify({{type: 'resize', cols: term.cols,
                              rows: term.rows}}));
 }}).observe(document.getElementById('term'));
 function spawn(name) {{
   ws.send(JSON.stringify({{type: 'spawn', harness: name}}));
   term.focus();
 }}
 let last = 0;
 setInterval(async () => {{
   try {{
     const r = await fetch('/workbench/changed');
     const t = (await r.json()).mtime;
     if (last && t > last) document.getElementById('left').src += '';
     last = t;
   }} catch (e) {{}}
 }}, 2000);
</script></body></html>"""
