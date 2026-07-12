#!/usr/bin/env python3
"""brain-mcp — Model Context Protocol server exposing the brain's synthesis
layer to MCP-aware clients (Claude Code, Claude Desktop, Cursor, etc.).

Per `wiki/brain/ai-suggestions/prds/brain-mcp-server.md`. Implements a
minimal stdio MCP server with a small read-only tool surface. The brain
is **never** mutated through MCP — every tool here is read-side.

Tools exposed:

- `brain_search(query, top, repo, kind, include_superseded)` — hybrid
  search over the wiki/ synthesis layer.
- `brain_get_page(path)` — fetch the body of a wiki page by relative
  path (e.g. "<repo>/permanent/architecture.md").
- `brain_stats()` — corpus-level counters (page count by kind, by
  confidence, by repo).
- `brain_overlaps()` — list cross-team overlap pages under
  `wiki/_overlaps/`.
- `brain_efforts()` — list in-flight efforts from `wiki/_state/efforts/`.
- `brain_active_repos()` — list repos with active wiki shelves.

Designed to be standalone and portable: only stdlib imports + a thin
shell-out to brain.py for the search command (so improvements to
`brain.py search` immediately propagate without a duplicate
implementation).

Register with Claude Code:

    claude mcp add brain --scope user -- python3 \\
        ~/projects/brain/tools/brain-mcp.py

The MCP protocol is JSON-RPC 2.0 over stdio. This implementation
handles `initialize`, `tools/list`, `tools/call`. Everything else
returns a `MethodNotFound` error gracefully.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Locate the brain repo. The conventional install puts brain-mcp.py at
# <BRAIN>/tools/brain-mcp.py, so the parent of this script's parent is
# <BRAIN>. The BRAIN_DIR env var overrides for unconventional installs.
SCRIPT = Path(__file__).resolve()
BRAIN_DIR = Path(os.environ.get("BRAIN_DIR") or SCRIPT.parent.parent)
WIKI = BRAIN_DIR / "wiki"
BRAIN_PY = BRAIN_DIR / "tools" / "brain.py"

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "brain"
SERVER_VERSION = "0.1.0"


# ---------- tool implementations ----------------------------------------

def serving_mode() -> bool:
    """BRAIN_SERVING=1 marks a deployment that serves people outside
    the product: ai-suggestions are excluded from the corpus (the
    path is the primary signal, per governance) and every tool call
    is appended to the query audit log."""
    return os.environ.get("BRAIN_SERVING", "") == "1"


def audit_query(tool: str, args: dict) -> None:
    if not serving_mode():
        return
    import datetime as _dt
    log_path = BRAIN_DIR / "log" / "queries.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
             "tool": tool,
             "args": {k: str(v)[:200] for k, v in (args or {}).items()}}
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def tool_brain_search(args: dict) -> str:
    query = args.get("query") or ""
    if not query:
        raise ValueError("'query' is required")
    cmd = [sys.executable, str(BRAIN_PY), "search", query, "--json"]
    if "top" in args:
        cmd += ["--top", str(int(args["top"]))]
    if "repo" in args and args["repo"]:
        cmd += ["--repo", args["repo"]]
    if "kind" in args and args["kind"]:
        cmd += ["--kind", args["kind"]]
    if args.get("include_superseded"):
        cmd += ["--include-superseded"]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=10, cwd=BRAIN_DIR
    )
    out = proc.stdout or proc.stderr or "{}"
    if serving_mode():
        try:
            data = json.loads(out)
            data["results"] = [r for r in data.get("results", [])
                               if "ai-suggestions/" not in r.get("path", "")]
            out = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            pass
    return out


def tool_brain_get_page(args: dict) -> str:
    path = args.get("path") or ""
    if not path:
        raise ValueError("'path' is required")
    if serving_mode() and "ai-suggestions/" in path:
        raise ValueError(
            "ai-suggestions are drafts pending human review and are "
            "not part of the serving corpus")
    candidate = (WIKI / path).resolve()
    try:
        candidate.relative_to(WIKI)
    except ValueError:
        raise ValueError(f"path escapes wiki/: {path}")
    if not candidate.exists():
        raise ValueError(f"page not found: {path}")
    body = candidate.read_text()
    # Every read is a briefing (per the open-knowledge study): append
    # the page's graph context via brain.py, so agents see backlinks,
    # edges, and recent activity without extra calls.
    ctx = subprocess.run(
        [sys.executable, str(BRAIN_PY), "page", path, "--context-only"],
        capture_output=True, text=True, timeout=10, cwd=BRAIN_DIR)
    context = ctx.stdout.strip()
    if serving_mode() and context:
        context = "\n".join(
            ln for ln in context.splitlines()
            if "ai-suggestions/" not in ln)
    return body + ("\n\n" + context if context else "")


def tool_brain_stats(_args: dict) -> str:
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "stats"],
        capture_output=True, text=True, timeout=10, cwd=BRAIN_DIR,
    )
    return proc.stdout or proc.stderr or "(no output)"


def tool_brain_overlaps(_args: dict) -> str:
    overlaps_dir = WIKI / "_overlaps"
    if not overlaps_dir.exists():
        return "[]"
    out = []
    for p in sorted(overlaps_dir.rglob("*.md")):
        rel = p.relative_to(WIKI)
        if rel.name.startswith("_"):
            continue
        title = ""
        text = p.read_text()
        m = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
        if m:
            title = m.group(1).strip().strip('"')
        out.append({"path": str(rel), "title": title})
    return json.dumps(out, indent=2)


def tool_brain_efforts(_args: dict) -> str:
    efforts_dir = WIKI / "_state" / "efforts"
    if not efforts_dir.exists():
        return "[]"
    out = []
    for p in sorted(efforts_dir.glob("*.json")):
        try:
            record = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        out.append({
            "slug": record.get("slug") or p.stem,
            "phase": record.get("phase"),
            "spawned_at": record.get("spawned_at"),
            "status": record.get("status"),
            "targets": record.get("targets") or [],
            "notes": record.get("notes"),
        })
    return json.dumps(out, indent=2)


def tool_brain_verify_claims(args: dict) -> str:
    page = args.get("page") or ""
    if not page:
        raise ValueError("'page' is required")
    cmd = [sys.executable, str(BRAIN_PY), "verify-claims", page, "--json"]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=15, cwd=BRAIN_DIR,
    )
    return proc.stdout or proc.stderr or "{}"


def tool_brain_status(_args: dict) -> str:
    proc = subprocess.run(
        [sys.executable, str(BRAIN_PY), "status"],
        capture_output=True, text=True, timeout=10, cwd=BRAIN_DIR,
    )
    return proc.stdout or proc.stderr or "(no output)"


def tool_brain_active_repos(_args: dict) -> str:
    out = []
    for child in sorted(WIKI.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name in {"org", "brain", "insights"}:
            continue
        if (child / "index.md").exists():
            out.append(child.name)
    return json.dumps(out)


# ---------- MCP plumbing ------------------------------------------------

TOOL_HANDLERS = {
    "brain_search": tool_brain_search,
    "brain_get_page": tool_brain_get_page,
    "brain_stats": tool_brain_stats,
    "brain_overlaps": tool_brain_overlaps,
    "brain_efforts": tool_brain_efforts,
    "brain_active_repos": tool_brain_active_repos,
    "brain_status": tool_brain_status,
    "brain_verify_claims": tool_brain_verify_claims,
}

TOOL_SCHEMAS = [
    {
        "name": "brain_search",
        "description": (
            "Hybrid search over the brain's synthesis layer (wiki/). Returns "
            "ranked pages with path, title, kind, confidence, score, excerpt. "
            "Use this BEFORE walking sibling-repo source for any question "
            "about architecture, conventions, decisions, or initiatives."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "search terms"},
                "top": {"type": "integer", "description": "max results (default 10)"},
                "repo": {
                    "type": "string",
                    "description": "filter to pages about/affecting this repo (e.g. 'app')",
                },
                "kind": {
                    "type": "string",
                    "enum": ["reference", "initiative", "decision", "entity",
                             "meta", "overlap", "insight", "epic"],
                    "description": "filter to pages of this kind",
                },
                "include_superseded": {
                    "type": "boolean",
                    "description": "include superseded/archived pages (default false)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "brain_get_page",
        "description": (
            "Fetch the full body of a wiki page by its wiki-relative path "
            "(e.g. '<repo>/permanent/architecture.md'). Use after "
            "brain_search to load a candidate page."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "wiki-relative path, e.g. 'org/cross-product/authorization.md'",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "brain_stats",
        "description": "Corpus-level counters: pages by kind, confidence, repo.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "brain_overlaps",
        "description": "List cross-team overlap pages from wiki/_overlaps/.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "brain_efforts",
        "description": "List in-flight parallel efforts from wiki/_state/efforts/.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "brain_active_repos",
        "description": "List repo names that have active wiki shelves under wiki/<repo>/.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "brain_status",
        "description": (
            "Brain-wide status dashboard. Surfaces corpus stats + security / "
            "deadlines / issues / sync-cursors / efforts / AI-suggestion "
            "backlog from wiki/_state/. Useful for one-shot health check."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "brain_verify_claims",
        "description": (
            "Extract verifiable claims (paths, version-pins, identifiers) "
            "from a wiki page and emit a structured manifest the consumer "
            "can verify against sibling-repo source. Mechanical checks "
            "(file existence, line ranges) run in-tool; semantic claims "
            "(content / behaviour) are flagged with `needs-verification` "
            "for the LLM consumer to read the cited file via Read tool "
            "and judge."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "description": "wiki-relative path, e.g. '<repo>/state.md'",
                },
            },
            "required": ["page"],
        },
    },
]


def jsonrpc_response(req_id, result=None, error=None) -> dict:
    msg = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def handle_request(req: dict) -> dict | None:
    method = req.get("method")
    params = req.get("params") or {}
    req_id = req.get("id")

    if method == "initialize":
        return jsonrpc_response(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "notifications/initialized":
        return None  # notification — no response

    if method == "tools/list":
        return jsonrpc_response(req_id, {"tools": TOOL_SCHEMAS})

    if method == "tools/call":
        name = params.get("name") or ""
        arguments = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return jsonrpc_response(req_id, error={
                "code": -32602, "message": f"unknown tool: {name}",
            })
        try:
            audit_query(name, arguments)
            text = handler(arguments)
            return jsonrpc_response(req_id, {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            })
        except Exception as exc:
            return jsonrpc_response(req_id, {
                "content": [{"type": "text", "text": f"error: {exc}"}],
                "isError": True,
            })

    if method == "ping":
        return jsonrpc_response(req_id, {})

    if method == "shutdown":
        return jsonrpc_response(req_id, {})

    if req_id is not None:
        return jsonrpc_response(req_id, error={
            "code": -32601, "message": f"method not found: {method}",
        })
    return None


def serve_http(host: str, port: int) -> int:
    """Streamable-HTTP transport (stateless mode): POST /mcp carries
    one JSON-RPC message, the response is plain JSON. Notifications
    get 202. Localhost by default; a deployment puts an
    identity-aware proxy in front — this process has no auth of its
    own and no write tools to protect. Host and Origin are both
    checked against a loopback allow-list to block DNS-rebinding —
    the same guard tools/brain.py serve applies, so the anti-rebinding
    property holds identically on both HTTP surfaces (Sam
    uniform-host-guard finding, 2026-07-12)."""
    import http.server
    import socketserver

    class Handler(http.server.BaseHTTPRequestHandler):
        def _reply(self, code: int, body: dict | None = None):
            data = json.dumps(body).encode() if body is not None else b""
            self.send_response(code)
            if data:
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if data:
                self.wfile.write(data)

        def log_message(self, fmt, *args):
            sys.stderr.write(f"[brain-mcp] {fmt % args}\n")

        def _loopback_host(self) -> bool:
            # Anti-DNS-rebinding: the Host header must name loopback
            # (or be absent, for direct-IP tooling) — mirrors
            # brain.py serve's allow-list exactly.
            host_hdr = (self.headers.get("Host") or "").split(":")[0]
            return host_hdr in ("localhost", "127.0.0.1", "::1", "")

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") not in ("", "/mcp"):
                self._reply(404, {"error": "POST /mcp"})
                return
            if not self._loopback_host():
                self._reply(403, {"error": "host not allowed"})
                return
            origin = self.headers.get("Origin", "")
            if origin and not re.match(
                    r"https?://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
                self._reply(403, {"error": "origin not allowed"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length))
            except (ValueError, json.JSONDecodeError):
                self._reply(400, {"error": "bad JSON-RPC body"})
                return
            response = handle_request(req)
            if response is None:
                self._reply(202)
            else:
                self._reply(200, response)

        def do_GET(self):  # noqa: N802
            self._reply(405, {"error": "streamable HTTP: POST /mcp "
                                       "(stateless mode; no SSE stream)"})

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    with Server((host, port), Handler) as httpd:
        mode = " [serving mode]" if serving_mode() else ""
        sys.stderr.write(f"[brain-mcp] http://{host}:{port}/mcp{mode}\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="brain MCP server")
    ap.add_argument("--http", action="store_true",
                    help="streamable-HTTP transport instead of stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("BRAIN_MCP_PORT", 8766)))
    opts = ap.parse_args()
    if opts.http:
        return serve_http(opts.host, opts.port)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stderr.write(f"[brain-mcp] bad JSON: {line!r}\n")
            continue
        response = handle_request(req)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
