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

# Chat rows (per wiki/brain/adrs/chat-print-mode-bridge.md): one data
# row per harness naming its print-mode invocation and continuation
# form. Print modes bill to the operator's existing subscription and
# honour the repo's project config (skills, permissions, MCP) — the
# conversation drives the same mechanism the terminal would. A
# harness without a print mode gets no chat row, never TUI scraping.
CHAT_CLIS = [
    # acceptEdits: chat turns are operator-initiated work in the
    # operator's own repo — file edits auto-accept so the chat can
    # build; bash stays gated by the project allowlist.
    {"name": "claude", "bin": "claude",
     "first_args": ["--permission-mode", "acceptEdits", "-p"],
     "continue_args": ["--permission-mode", "acceptEdits", "-p",
                       "--continue"]},
    {"name": "codex", "bin": "codex",
     "first_args": ["exec"], "continue_args": ["exec"]},
    {"name": "cursor", "bin": "cursor-agent",
     "first_args": ["-p"], "continue_args": ["-p"]},
    {"name": "opencode", "bin": "opencode",
     "first_args": ["run"], "continue_args": ["run", "--continue"]},
]

_chat_continuing: set = set()

# API-key environment variables that flip harness CLIs from
# subscription billing to metered API billing. The app strips these
# from every harness subprocess (chat and terminal) by default, so a
# turn can only ever bill the operator's logged-in plan — the
# billing guard from the chat-print-mode-bridge ADR's amendment.
# Opt back in via brain.config.yml `chat: { allow_api_keys: true }`.
API_KEY_ENV_VARS = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    "OPENAI_API_KEY", "OPENAI_ORG_ID",
    "CURSOR_API_KEY", "OPENCODE_API_KEY",
)


def billing_safe_env(allow_api_keys: bool = False) -> dict:
    env = dict(os.environ)
    if not allow_api_keys:
        for var in API_KEY_ENV_VARS:
            env.pop(var, None)
    return env


def _allow_api_keys() -> bool:
    try:
        import yaml
        config = pathlib_config = None
        from pathlib import Path
        cfg_path = Path(__file__).resolve().parent.parent / "brain.config.yml"
        if cfg_path.exists():
            config = yaml.safe_load(cfg_path.read_text()) or {}
            return bool((config.get("chat") or {}).get("allow_api_keys"))
    except Exception:
        pass
    return False


def run_chat_message(harness: str, message: str, cwd: str,
                     timeout: int = 600,
                     registry: list | None = None) -> dict:
    """One chat turn: spawn the harness's print mode with the message.

    Blocking by design in v1 (an agent turn legitimately runs
    minutes); the caller shows progress. Continuation state is
    per-server-lifetime: the first turn opens a session in the repo,
    later turns continue it where the harness supports that.
    """
    import shutil
    rows = registry if registry is not None else CHAT_CLIS
    row = next((r for r in rows if r["name"] == harness), None)
    if row is None:
        return {"ok": False, "reply": f"unknown chat harness: {harness}"}
    if not shutil.which(row["bin"]):
        return {"ok": False,
                "reply": f"{row['bin']} is not on PATH — install the "
                         f"harness or pick another"}
    args = (row["continue_args"] if harness in _chat_continuing
            else row["first_args"])
    try:
        res = subprocess.run(
            [row["bin"], *args, message],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
            env=billing_safe_env(_allow_api_keys()))
    except subprocess.TimeoutExpired:
        return {"ok": False,
                "reply": "(the agent is taking too long — the turn was "
                         "stopped; the terminal toggle handles long "
                         "operations better)"}
    if res.returncode == 0:
        _chat_continuing.add(harness)
        return {"ok": True,
                "reply": res.stdout.strip() or "(empty reply)"}
    return {"ok": False,
            "reply": (res.stderr.strip() or res.stdout.strip()
                      or f"harness exited {res.returncode}")[:4000]}


class PtySession:
    """One terminal: the operator's login shell on a PTY pair."""

    def __init__(self):
        shell = os.environ.get("SHELL", "/bin/bash")
        self.master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            [shell, "-l", "-i"],
            stdin=slave, stdout=slave, stderr=slave,
            start_new_session=True,
            env={**billing_safe_env(_allow_api_keys()),
                 "TERM": "xterm-256color"},
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
                          page_count: int,
                          views: list | None = None,
                          chat_rows: list | None = None) -> str:
    chat_rows = chat_rows if chat_rows is not None else CHAT_CLIS
    chat_options = "".join(
        f'<option value="{r["name"]}">{r["name"]}</option>'
        for r in chat_rows)
    term_buttons = "".join(
        f'<button onclick="spawn(\'{h["name"]}\')">{h["name"]}</button>'
        for h in harnesses)
    view_links = "".join(
        f'<button onclick="nav(\'/_views/custom/{v}/\')">{v}</button>'
        for v in (views or []))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>brain</title>
<link rel="stylesheet" href="/workbench/assets/xterm.css">
<style>
 :root {{ color-scheme: light dark; }}
 body {{ margin: 0; font: 14px/1.45 system-ui, sans-serif;
        display: flex; height: 100vh; }}
 button, select, textarea {{ font: inherit; }}
 #leftwrap {{ flex: 1 1 55%; display: flex; flex-direction: column;
              min-width: 20rem; }}
 #nav {{ padding: .35rem .6rem; display: flex; gap: .4rem;
        align-items: center; border-bottom: 1px solid #8884; }}
 #nav button {{ padding: .15rem .6rem; cursor: pointer; }}
 #strip {{ margin-left: auto; opacity: .75; font-size: .85em; }}
 #left {{ flex: 1; border: 0; }}
 #right {{ flex: 1 1 45%; display: flex; flex-direction: column;
          border-left: 1px solid #8884; min-width: 22rem; }}
 #chatbar {{ padding: .4rem .6rem; display: flex; gap: .4rem;
            align-items: center; border-bottom: 1px solid #8884; }}
 #msgs {{ flex: 1; overflow-y: auto; padding: .8rem; display: flex;
         flex-direction: column; gap: .6rem; }}
 .msg {{ max-width: 92%; padding: .5rem .7rem; border-radius: .6rem;
        white-space: pre-wrap; overflow-wrap: anywhere; }}
 .me {{ align-self: flex-end;
       background: color-mix(in srgb, currentColor 12%, transparent); }}
 .agent {{ align-self: flex-start;
          background: color-mix(in srgb, currentColor 6%, transparent); }}
 .agent.busy {{ opacity: .6; font-style: italic; }}
 .agent code {{ background: color-mix(in srgb, currentColor 10%, transparent);
               padding: 0 .25em; border-radius: 3px; font-size: .92em; }}
 .agent a {{ color: inherit; }}
 #chips {{ display: flex; gap: .4rem; flex-wrap: wrap; }}
 #chips button {{ padding: .2rem .6rem; border-radius: 1rem;
                 cursor: pointer; opacity: .85; }}
 #composer {{ display: flex; gap: .4rem; padding: .6rem;
             border-top: 1px solid #8884; }}
 #input {{ flex: 1; resize: none; padding: .45rem .6rem;
          border-radius: .5rem; border: 1px solid #8886;
          background: transparent; color: inherit; }}
 #term {{ display: none; height: 45%; min-height: 12rem;
         padding: .3rem; background: #000;
         border-top: 1px solid #8884; }}
 #termbar {{ display: none; padding: .3rem .6rem; gap: .4rem;
            border-top: 1px solid #8884; align-items: center; }}
 body.termon #term, body.termon #termbar {{ display: flex; }}
</style></head><body>
<div id="leftwrap">
 <div id="nav">
   <button onclick="nav('/')">knowledge</button>
   <button onclick="nav('/dash')">status</button>
   {view_links}
   <span id="strip">…</span>
 </div>
 <iframe id="left" src="/"></iframe>
</div>
<div id="right">
 <div id="chatbar">
   <select id="harness">{chat_options}</select>
   <span style="opacity:.6">chat runs in this brain, on your
   subscription</span>
   <button style="margin-left:auto" onclick="toggleTerm()"
           title="advanced: raw terminal">⌄ terminal</button>
 </div>
 <div id="msgs">
   <div class="msg agent">Ask me anything about this brain — or tell
me what to do. I can tend the queue, capture decisions, search,
and shape work. The knowledge pane updates as I change things.</div>
   <div id="chips">
     <button onclick="ask('What needs attention right now?')">what
needs attention?</button>
     <button onclick="ask('What changed recently, in a few bullets?')">what
changed?</button>
     <button onclick="ask('Give me a quick tour of what this brain knows.')">give
me a tour</button>
   </div>
 </div>
 <div id="composer">
   <textarea id="input" rows="2" autofocus
     placeholder="ask or instruct — Enter to send, Shift+Enter for a new line"></textarea>
   <button id="send" onclick="send()">send</button>
 </div>
 <div id="termbar"><span>open in:</span>{term_buttons}</div>
 <div id="term"></div>
</div>
<script src="/workbench/assets/xterm.js"></script>
<script src="/workbench/assets/addon-fit.js"></script>
<script>
 const TOKEN = "{token}";
 function nav(url) {{ document.getElementById('left').src = url; }}
 // ---- chat ----
 const msgs = document.getElementById('msgs');
 const input = document.getElementById('input');
 function bubble(cls, text) {{
   const d = document.createElement('div');
   d.className = 'msg ' + cls;
   d.textContent = text;
   msgs.appendChild(d);
   msgs.scrollTop = msgs.scrollHeight;
   return d;
 }}
 // markdown-lite for agent replies: escape first, then bold /
 // inline-code / links. Structure survives via pre-wrap.
 function mdlite(text) {{
   const esc = text.replace(/&/g, '&amp;').replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;');
   return esc
     .replace(/`([^`\\n]+)`/g, '<code>$1</code>')
     .replace(/\\*\\*([^*\\n]+)\\*\\*/g, '<b>$1</b>')
     .replace(/\\[([^\\]\\n]+)\\]\\((https?:[^)\\s]+)\\)/g,
              '<a href="$2" target="_blank">$1</a>');
 }}
 function ask(text) {{ input.value = text; send(); }}
 async function send() {{
   const text = input.value.trim();
   if (!text) return;
   input.value = '';
   bubble('me', text);
   const busy = bubble('agent busy', 'thinking…');
   document.getElementById('send').disabled = true;
   try {{
     const r = await fetch('/workbench/chat?token=' + TOKEN, {{
       method: 'POST',
       headers: {{'Content-Type': 'application/json'}},
       body: JSON.stringify({{
         harness: document.getElementById('harness').value,
         message: text }}),
     }});
     const data = await r.json();
     busy.classList.remove('busy');
     busy.innerHTML = mdlite(data.reply || '(no reply)');
   }} catch (e) {{
     busy.classList.remove('busy');
     busy.textContent = '(request failed: ' + e + ')';
   }}
   document.getElementById('send').disabled = false;
   input.focus();
 }}
 input.addEventListener('keydown', (e) => {{
   if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); send(); }}
 }});
 window.addEventListener('load', () => input.focus());
 // ---- ambient strip + live reload ----
 let last = 0;
 async function tick() {{
   try {{
     const r = await fetch('/workbench/status');
     const s = await r.json();
     document.getElementById('strip').textContent =
       (s.fails ? '✗ ' + s.fails + ' failing · ' :
        s.warns ? '− ' + s.warns + ' notice · ' : '✓ healthy · ')
       + (s.inbox ? s.inbox + ' to tend' : 'queue clear');
     if (last && s.mtime > last) nav(document.getElementById('left').src);
     last = s.mtime;
   }} catch (e) {{}}
 }}
 tick(); setInterval(tick, 8000);
 // ---- terminal (advanced toggle; PTY connects lazily) ----
 let term = null, ws = null;
 function toggleTerm() {{
   document.body.classList.toggle('termon');
   if (term || !document.body.classList.contains('termon')) return;
   term = new Terminal({{fontSize: 13, scrollback: 5000}});
   const fit = new FitAddon.FitAddon();
   term.loadAddon(fit);
   term.open(document.getElementById('term'));
   fit.fit();
   ws = new WebSocket(
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
     if (ws && ws.readyState === 1)
       ws.send(JSON.stringify({{type: 'resize', cols: term.cols,
                                rows: term.rows}}));
   }}).observe(document.getElementById('term'));
 }}
 function spawn(name) {{
   if (ws && ws.readyState === 1)
     ws.send(JSON.stringify({{type: 'spawn', harness: name}}));
   if (term) term.focus();
 }}
</script></body></html>"""
