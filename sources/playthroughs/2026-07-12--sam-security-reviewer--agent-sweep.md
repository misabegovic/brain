---
persona: sam-security-reviewer
scenario: serving-mode + interactive-channel adversarial security sweep
version: 0.19.3
date: 2026-07-12
executed_by: "claude (fable 5) — agent"
---

# Sam walks the brain's serving plane — adversarial sweep

I am Sam. I review tools before my organisation runs them, and I
assume every README overstates. My method is adversarial reading:
start the servers, enumerate what listens, and try the things the
docs say are impossible. I read `SECURITY.md` last, to check it
against what I actually found. My winning moment is a claimed
guarantee I *fail* to break after honestly trying — structural
absence beats gated presence. My blocking points: any listener
that executes shell input; a read-only property that depends on an
operator remembering a flag; audit logging the audited thing can
switch off.

The product is at 0.19.3. A live server runs on `:8765`. Two HTTP
serving surfaces exist per the docs — the app/JSON server
(`brain.py serve`, mounts `/workbench` + `/api/act` outside serving
mode) and the MCP HTTP transport (`brain-mcp.py --http`). Both are
supposed to bind loopback and, in serving deployments, sit behind
an identity-aware proxy with no auth of their own. Let's see.

## Attack surface enumeration

The live server is loopback-bound, as claimed:

```
$ ss -tlnp | grep 8765
LISTEN 0  5  127.0.0.1:8765  0.0.0.0:*  users:(("python3",pid=2196414,fd=3))
```

Root answers 200. Good — something's alive to probe.

## Probe 1 — the interactive channel `/api/act`

The docs (UI § "The interactive channel", ADR amendment
2026-07-12) claim the UI's *only* write surface is the inbox, that
the endpoint requires a custom `X-Brain-Act` header whose presence
forces a CORS preflight the server never grants (so a hostile web
page cannot fire it cross-origin), and that it never mounts in
serving mode. Three claims. I try to break each.

**T1 — POST without the custom header (a cross-origin "simple"
request looks exactly like this):**

```
$ curl -si -X POST http://localhost:8765/api/act \
    -H "Content-Type: application/json" \
    -d '{"action":"comment","target":"test","note":"sam probe no header"}'
HTTP/1.0 403 Forbidden
...
{
  "error": "missing action header"
}
```

403. The write is refused. A cross-origin page can't attach
`X-Brain-Act` without tripping a preflight, and this server grants
no CORS. **Holds.**

**T2 — forged non-loopback Host header, with a valid action header:**

```
$ curl -si -X POST http://localhost:8765/api/act \
    -H "Host: evil.example.com" -H "X-Brain-Act: 1" \
    -H "Content-Type: application/json" \
    -d '{"action":"comment","target":"x","note":"y"}'
HTTP/1.0 403 Forbidden
...
{ "error": "host not allowed" }
```

403 `host not allowed`. The endpoint validates the `Host` header
against a loopback allow-list before it will act — a DNS-rebinding
page whose `Host` is its own domain is rejected. **Holds.**

**T3 — wrong method (GET):** returns 404 (falls through to the
rendered wiki's not-found). The write path is POST-only; no read
verb reaches it.

**T4 — correct use should queue an inbox item (the documented happy
path):**

```
$ curl -si -X POST http://localhost:8765/api/act -H "X-Brain-Act: 1" \
    -H "Content-Type: application/json" \
    -d '{"action":"comment","target":"security-review","note":"sam adversarial probe 2026-07-12"}'
...
{ "queued": "ui-comment-20260712-144654" }
```

And it landed as exactly one inbox JSON, nothing more:

```
$ cat wiki/_state/inbox/ui-comment-20260712-144654.json
{
  "id": "ui-comment-20260712-144654",
  "kind": "custom",
  "summary": "operator comment on security-review: \"sam adversarial probe 2026-07-12\"",
  "route": "/tend ui-comment-20260712-144654",
  "priority": "normal",
  "source": "security-review",
  "produced_by": "ui-action",
  "produced_at": "2026-07-12"
}
```

This is the whole write capability: append one inbox item tagged
`produced_by: ui-action`. There is no path where `/api/act` writes
an arbitrary file or runs a command. The action verb is validated
against a two-item allow-list; `note`/`target` are length-clamped
and only ever land inside a JSON string. **T5** (`"action":"rm-rf"`)
returns `400 unknown action`; **T6** (non-JSON body) returns `400
bad action body`. No shell anywhere near this input. *Would I have
given up here?* No — this is the opposite of a give-up point: I
tried to find write capability hiding behind a read-only label and
found the label honest. (I marked my probe item done afterward so I
left no litter in the operator's tend queue.)

## Probe 2 — serving mode (the load-bearing claim)

Sam's core scenario. The claim is that serving mode's guarantees
hold *by construction*, not by an operator remembering a flag. I
start a second instance in serving mode on a non-default port, plus
both flavours of the MCP HTTP transport:

```
$ BRAIN_SERVING=1 BRAIN_PORT=8788 python3 tools/brain.py serve &
$ BRAIN_SERVING=1 python3 tools/brain-mcp.py --http --port 8790 &   # serving
$ python3 tools/brain-mcp.py --http --port 8791 &                   # non-serving control
$ ss -tlnp | grep -E "8788|8790|8791"
LISTEN ... 127.0.0.1:8788 ...
LISTEN ... 127.0.0.1:8790 ...
LISTEN ... 127.0.0.1:8791 ...
```

All three bind `127.0.0.1` — loopback only, not `0.0.0.0`. Good.

**S1 — `/workbench` in serving mode must not mount:**

```
$ curl -si http://localhost:8788/workbench
HTTP/1.0 404 Not Found
```

404. In serving mode the workbench branch is never registered — the
`workbench` flag is computed once from `BRAIN_SERVING` at startup
and the route simply doesn't exist. **Holds.**

**S2 — POST `/api/act` in serving mode, valid header + valid body,
i.e. the strongest write attempt I can make:**

```
$ curl -si -X POST http://localhost:8788/api/act -H "X-Brain-Act: 1" \
    -H "Content-Type: application/json" \
    -d '{"action":"comment","target":"x","note":"serving-mode write attempt"}'
HTTP/1.0 405 Method Not Allowed
...
{ "error": "read-only" }
```

405 `read-only`. This is the winning-moment shape: it's not that
the write ran and got rejected by a check — the write branch is
*absent*. The `if workbench and path == "/api/act"` guard short-circuits
on the flag, so POST falls straight through to the read-only 405.
Structural absence, not gated presence. **Holds.**

**S3 — `/workbench/status`:** 404 in serving mode vs 200 on the
non-serving `:8765`. Confirms the difference is the mode, not a
missing build.

## Probe 3 — the MCP HTTP transport

**M1 — initialize works** (POST /mcp, stateless JSON-RPC):

```
$ curl -s -X POST http://localhost:8790/mcp -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05",...,"serverInfo":{"name":"brain","version":"0.1.0"}}}
```

**M2 — cross-origin POST with a hostile Origin (DNS-rebinding
simulation):**

```
$ curl -si -X POST http://localhost:8790/mcp -H "Origin: https://evil.example.com" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
HTTP/1.0 403 Forbidden
{ "error": "origin not allowed" }
```

403. A cross-origin browser page is blocked. **Holds.**

**M3 — GET /mcp:** 405 (stateless POST-only). **M-tools —
`tools/list`** returns only read tools: `brain_search`,
`brain_get_page`, `brain_stats`, `brain_overlaps`, `brain_efforts`,
`brain_active_repos`, `brain_status`, `brain_verify_claims`. There
is *no write tool on the MCP surface at all* — nothing to protect
because nothing mutates.

**E1/E2 — ai-suggestion exclusion in serving mode.** Serving mode
must hide `ai-suggestions/` from page reads. I hit `brain_get_page`
for an ai-suggestions path on both instances:

```
serving  :8790  → error: ai-suggestions are drafts pending human review
                          and are not part of the serving corpus
non-serv :8791  → error: page not found: brain/ai-suggestions/adrs/whatever.md
```

The serving refusal fires on the *path*, before the file is even
looked up — so it holds whether or not the draft exists. The
non-serving control would happily serve it. **Holds.**

**E3 — path traversal:** `brain_get_page` with
`../../../etc/passwd` →

```
error: path escapes wiki/: ../../../etc/passwd
```

The candidate is resolved and checked `relative_to(WIKI)` before
any read. **Holds.**

**Search exclusion — the positive proof.** I authored my own
ai-suggestion (this sweep's deliverable) and searched for it on
both MCP instances:

```
SERVING     :8790 → MATCHES for my ai-suggestion: NONE (excluded); total results: 9
NON-SERVING :8791 → MATCHES: ['brain/ai-suggestions/adrs/sam-uniform-loopback-host-guard.md']; total results: 10
```

Serving mode returns the page count minus my draft; non-serving
includes it. The `ai-suggestions/` path is the signal, filtered out
of both search results and read context in serving mode. **Holds.**

## Probe 4 — shell input on any listener

Sam's hardest blocking point: a listener that executes shell input.
The only subprocess reachable from an HTTP handler is `/search` on
the app server, which shells to mempalace. I checked the call site:

```
out = subprocess.run(["mempalace", "search", q], ...)
```

Argv form, no `shell=True`. The user's `q` is a single argv element
— it cannot break out into a shell. No listener executes shell
input. Since 0.15.0 the kernel ships no PTY bridge and spawns no
harness subprocess, and I found none. **Holds.**

## Reading SECURITY.md last (Sam's method)

Now I check the doc against what I found. `SECURITY.md` claims: the
serving surfaces carry no auth of their own and run read-only
behind a proxy (I confirmed no write tools, no mutation path); the
app page executes no shell and no websocket and is structurally
excluded from serving deployments (confirmed at S1/S2); the kernel
ships no PTY bridge and spawns no harness subprocess (confirmed —
none found); connector credentials are read-only-scoped (out of
scope for this HTTP sweep; not probed). Every claim I *could* test
against the running product held. `SECURITY.md` does not overstate.

## Verdict and the one hardening step

No give-up point. No blocking finding. Every documented guarantee
survived an honest attempt to break it — the winning-moment
outcome. But there is always a next hardening step, and I found one
by comparing the two surfaces rather than reading either in
isolation:

The two HTTP surfaces defend against DNS-rebinding with *different*
single mechanisms. The app/JSON server validates the `Host` header
against a loopback allow-list (T2, S-routes). The MCP HTTP
transport validates the `Origin` header — and only when an `Origin`
is present (a missing `Origin` is allowed) — with no `Host` check
(M2). Each is individually reasonable for a loopback-bound service
behind a proxy, and nothing is broken today. But because they
differ, the anti-rebinding property cannot be stated once for "the
brain's serving plane"; it has to be argued surface by surface, and
the MCP transport's defense leans entirely on browsers volunteering
an `Origin` where the app surface's `Host` allow-list does not.

That asymmetry is the single most valuable hardening opportunity
this sweep surfaced. I filed it as an AI-suggested ADR:
`wiki/brain/ai-suggestions/adrs/sam-uniform-loopback-host-guard.md`
— adopt one shared loopback `Host`-header check across both HTTP
serving surfaces so the guarantee holds by construction and can be
described in `SECURITY.md` as a single property.
