#!/usr/bin/env python3
"""brain-agent — the spoke client for a hosted brain's event tier.

The brain is the hub (memory + coordination); a harness runs the agent.
This is the missing half that lets an agent *in any harness* participate
in the event loop: emit signed events, pull from its cursor, subscribe
to what it cares about, and be woken when a matching event lands.

It is stdlib-only and holds no brain logic — it mirrors the server's
signing (per wiki/brain/adrs/per-agent-identity.md and
owner-subscription-wake.md) and talks HTTP to a `BRAIN_HOSTED=1` brain.

Config from the environment:
  BRAIN_URL           the hosted brain, e.g. https://brain.example.com
  BRAIN_AGENT_ID      this agent's id (issued by `brain.py agent-key issue`)
  BRAIN_AGENT_SECRET  the agent's key secret (never commit it)

Usage:
  brain-agent emit --kind drift --ref repo:brain
  brain-agent subscribe --pattern 'repo:*' --wake-url http://127.0.0.1:9999/wake
  brain-agent unsubscribe --pattern 'repo:*'
  brain-agent pull                       # verified events since the cursor
  brain-agent listen --port 9999         # receive wakes; pull + hand off
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import http.server
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CURSORS = Path(os.environ.get("BRAIN_AGENT_CURSORS",
                              str(Path.home() / ".brain-agent-cursors.json")))


def _cfg() -> tuple[str, str, str]:
    url = os.environ.get("BRAIN_URL", "").rstrip("/")
    agent = os.environ.get("BRAIN_AGENT_ID", "")
    secret = os.environ.get("BRAIN_AGENT_SECRET", "")
    if not (url and agent and secret):
        sys.exit("set BRAIN_URL, BRAIN_AGENT_ID, and BRAIN_AGENT_SECRET")
    return url, agent, secret


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _hmac(secret: str, message: str) -> str:
    return hmac.new(bytes.fromhex(secret), message.encode(),
                    hashlib.sha256).hexdigest()


def _sign_event(secret: str, agent: str, kind: str, ref: str, ts: str) -> str:
    canon = json.dumps({"agent": agent, "kind": kind, "ref": ref, "ts": ts},
                       sort_keys=True, separators=(",", ":"))
    return _hmac(secret, canon)


def _post(url: str, headers: dict, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          **headers}, method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"brain rejected the request ({e.code}): "
                 f"{e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        sys.exit(f"could not reach the brain: {e}")


def _cursor_key(url: str, agent: str) -> str:
    return f"{url}#{agent}"


def _cursor_get(url: str, agent: str) -> int:
    if CURSORS.exists():
        try:
            return int(json.loads(CURSORS.read_text()).get(
                _cursor_key(url, agent), 0))
        except (json.JSONDecodeError, ValueError):
            pass
    return 0


def _cursor_set(url: str, agent: str, seq: int) -> None:
    data = {}
    if CURSORS.exists():
        try:
            data = json.loads(CURSORS.read_text())
        except json.JSONDecodeError:
            pass
    data[_cursor_key(url, agent)] = int(seq)
    CURSORS.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def emit(kind: str, ref: str) -> dict:
    url, agent, secret = _cfg()
    ts = _now()
    sig = _sign_event(secret, agent, kind, ref, ts)
    return _post(f"{url}/api/events", {"X-Agent-Id": agent},
                 {"kind": kind, "ref": ref, "ts": ts, "sig": sig})


def pull(advance: bool = True) -> list[dict]:
    url, agent, secret = _cfg()
    since = _cursor_get(url, agent)
    ts = _now()
    sig = _hmac(secret, f"read:{since}:{ts}")
    req = urllib.request.Request(
        f"{url}/api/events?since={since}",
        headers={"X-Agent-Id": agent, "X-Agent-Ts": ts, "X-Agent-Sig": sig})
    try:
        evs = json.loads(urllib.request.urlopen(req, timeout=15).read())["events"]
    except urllib.error.HTTPError as e:
        sys.exit(f"pull rejected ({e.code}): {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        sys.exit(f"could not reach the brain: {e}")
    if evs and advance:
        _cursor_set(url, agent, max(e["seq"] for e in evs) + 1)
    return evs


def cmd_emit(args) -> int:
    r = emit(args.kind, args.ref)
    print(f"emitted {args.kind} → {args.ref} (seq={r.get('seq')})")
    return 0


def cmd_subscribe(args) -> int:
    ref = json.dumps({"p": args.pattern, "u": args.wake_url},
                     sort_keys=True, separators=(",", ":"))
    r = emit("subscribe", ref)
    print(f"subscribed to {args.pattern!r} → {args.wake_url} (seq={r.get('seq')})")
    return 0


def cmd_unsubscribe(args) -> int:
    ref = json.dumps({"p": args.pattern, "u": ""},
                     sort_keys=True, separators=(",", ":"))
    emit("subscribe", ref)
    print(f"unsubscribed from {args.pattern!r}")
    return 0


def cmd_pull(args) -> int:
    evs = pull(advance=not args.no_advance)
    if args.json:
        print(json.dumps(evs, indent=2))
    else:
        for e in evs:
            print(f"  seq={e['seq']} {e['kind']:8} by {e['agent']} → {e['ref']}")
        if not evs:
            print("(no new events)")
    return 0


def cmd_listen(args) -> int:
    """Run a webhook receiver: verify each wake, pull the new events, and
    hand them off (print, and optionally run --on-wake). The wake is only
    a hint — the pull is what delivers content, so a missed wake is caught
    up by the next pull."""
    url, agent, secret = _cfg()

    class _Wake(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            try:
                n = int(self.headers.get("Content-Length") or 0)
                w = json.loads(self.rfile.read(min(n, 8192)))
                ok = hmac.compare_digest(
                    _hmac(secret, f"wake:{w['seq']}:{w['ref']}"),
                    w.get("sig", ""))
            except (ValueError, KeyError, json.JSONDecodeError):
                self.send_response(400)
                self.end_headers()
                return
            self.send_response(200 if ok else 401)
            self.end_headers()
            if not ok:
                print("wake: bad signature, ignored", file=sys.stderr)
                return
            print(f"woken: {w['ref']} (seq {w['seq']}) — pulling")
            for e in pull():
                print(f"  seq={e['seq']} {e['kind']} by {e['agent']} → {e['ref']}")
                if args.on_wake:
                    subprocess.run(args.on_wake, shell=True, check=False,
                                   env={**os.environ, "BRAIN_EVENT": json.dumps(e)})

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer((args.host, args.port), _Wake)
    print(f"listening for wakes on http://{args.host}:{args.port}/  "
          f"(agent {agent} on {url})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="brain-agent",
                                 description="spoke client for a hosted brain")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit", help="append a signed event")
    e.add_argument("--kind", required=True)
    e.add_argument("--ref", required=True)
    e.set_defaults(func=cmd_emit)
    s = sub.add_parser("subscribe", help="wake on events matching a pattern")
    s.add_argument("--pattern", required=True)
    s.add_argument("--wake-url", dest="wake_url", required=True)
    s.set_defaults(func=cmd_subscribe)
    u = sub.add_parser("unsubscribe", help="drop a subscription")
    u.add_argument("--pattern", required=True)
    u.set_defaults(func=cmd_unsubscribe)
    p = sub.add_parser("pull", help="verified events since the cursor")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-advance", action="store_true")
    p.set_defaults(func=cmd_pull)
    ln = sub.add_parser("listen", help="receive wakes; pull + hand off")
    ln.add_argument("--host", default="127.0.0.1")
    ln.add_argument("--port", type=int, default=9999)
    ln.add_argument("--on-wake", dest="on_wake", default="",
                    help="shell command to run per new event (BRAIN_EVENT set)")
    ln.set_defaults(func=cmd_listen)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
