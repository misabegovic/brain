---
persona: sam-security-reviewer
scenario: serving-mode probe + local-surface /api/act probe + build-time escaping
version: 0.19.3
date: 2026-07-12
---

# Sam — adversarial verification of the serving-profile guarantees

Sam reviews the brain before his org would expose it. Method:
start the real servers inside the worktree, enumerate routes, try
the things the docs say are impossible, and read `SECURITY.md`
last. Everything below was executed against localhost servers Sam
started; no output is imagined.

Servers started (all bound to `127.0.0.1` only — confirmed via
`ss -tlnp`):

- `BRAIN_SERVING=1 BRAIN_PORT=8803 python3 tools/brain.py serve` — serving-mode HTTP API.
- `BRAIN_SERVING=1 python3 tools/brain-mcp.py --http --port 8813` — serving-mode MCP (log line confirmed `[serving mode]`).
- `BRAIN_PORT=8804 python3 tools/brain.py serve` — local-mode HTTP API (workbench mounted).

## 1. Serving-mode probe — `brain.py serve` (8803)

**Expectation:** `/workbench` must not mount; `POST /api/act` must
be refused; ai-suggestions excluded from any reachable read path.

The workbench gate is structural, not configuration discipline:
`workbench = os.environ.get("BRAIN_SERVING") != "1"` (`brain.py`
line 1275). With `BRAIN_SERVING=1` the whole `/workbench` and
`/api/act` branches are unreachable.

- `GET /workbench` → **HTTP 404** (`unknown endpoint`). Not mounted.
- `GET /workbench/status` → **HTTP 404**. Not mounted.
- `POST /api/act` with `X-Brain-Act: 1` → **HTTP 405** `read-only`.
- `POST /api/act` with correct `Host: localhost` **and** `X-Brain-Act: 1`
  → still **HTTP 405** `read-only`. The header can't re-open the
  endpoint; the branch does not exist in serving mode.

Both hold **by construction** — Sam's winning condition for these two.

**But** — the ai-suggestions exclusion does **not** hold on this
surface. Sam planted a marked draft
(`wiki/brain/ai-suggestions/adrs/sam-probe-secret.md`, body carrying
`LEAK_CANARY_9F3B`), ran `brain.py views`, refreshed the cache, and probed:

- `GET /pages.json` → the draft's path appears (`occurrences: 1`).
- `GET /pages/brain/ai-suggestions/adrs/sam-probe-secret.md` →
  **HTTP 200**, body returned, `LEAK_CANARY_9F3B` present. Full draft leaked.
- `GET /views/by-kind` → lists the draft.
- `BRAIN_SERVING=1 python3 tools/brain.py search 'Sam Probe Secret' --json`
  → results include `brain/ai-suggestions/adrs/sam-probe-secret.md`.

`BRAIN_SERVING` is referenced exactly once in `tools/brain.py`
(line 1275, the workbench gate). The `/pages/`, `/pages.json`,
`/views/*` handlers and `cmd_search` apply **no** ai-suggestions
filter in serving mode. The exclusion the MCP section documents
("ai-suggestions are excluded from search and page reads") is
implemented only in `brain-mcp.py`, not in the `serve` JSON API or
the search CLI.

*Would I have given up here?* Not blocked — these drafts carry a
visible AI-suggested banner and the plane sits behind a proxy — but
Sam flags it: a guarantee that reads as surface-wide is enforced on
one of three read surfaces.

## 1b. Serving-mode probe — MCP over HTTP (8813)

**Expectation:** read-only tools only; ai-suggestions excluded;
origin checks; calls audited; no write path.

- `tools/list` → 8 tools: `brain_search`, `brain_get_page`,
  `brain_stats`, `brain_overlaps`, `brain_efforts`,
  `brain_active_repos`, `brain_status`, `brain_verify_claims`.
  **No write tool exists.**
- `brain_get_page` on the planted draft → `isError: true`,
  "ai-suggestions are drafts pending human review and are not part
  of the serving corpus". **Excluded.**
- `brain_search` for the canary → path absent, canary absent. **Excluded.**
- `POST /mcp` with `Origin: https://evil.example.com` → **HTTP 403**
  `origin not allowed`.
- `POST /mcp` with `Origin: http://localhost:3000` → **HTTP 200**.
- `tools/call` for a fabricated `brain_write_page` → `-32602 unknown tool`.
- `GET /mcp` → **HTTP 405**.

Query audit log: after the two known-tool calls, `log/queries.log`
held exactly two JSON lines (the `brain_get_page` on the
ai-suggestion **and** the `brain_search`), including the refused
ai-suggestion read — attempted access is audited even when denied.
`git check-ignore log/queries.log` confirms it is git-ignored.
`audit_query` keys solely off the server-side `BRAIN_SERVING` env
with no request-controlled path — **the audited client cannot
disable it.** Sam's hard block ("audit logging that can be disabled
by the thing being audited") is not triggered.

Minor: `tools/call` for an *unknown* tool returns before
`audit_query` (`brain-mcp.py` line 366 vs 371), so tool-name probing
of nonexistent tools is not logged. Known-tool calls, including
denied ones, are logged.

## 2. Local-surface probe — `/api/act` (8804)

`GET /workbench` → **HTTP 200** here (workbench mounts in local
mode — the intended contrast). Then the write endpoint:

- No `X-Brain-Act` header → **HTTP 403** `missing action header`.
- `Host: evil.example.com` + `X-Brain-Act: 1` → **HTTP 403** `host not allowed`.
- `Host: attacker.com`, no act header → **HTTP 403** `host not allowed` (host checked first).
- Valid headers, non-JSON garbage body → **HTTP 400** `bad action body`.
- Valid JSON, `action: "rm -rf /"` → **HTTP 400** `unknown action` (allow-list is `execute`/`comment`).
- Missing `action` key → **HTTP 400** `bad action body`.
- ~100 KB body (read caps at 64 KB, `min(n, 65536)`) → **HTTP 400**, no crash.
- Lying `Content-Length: 10` with longer body → **HTTP 400**, no crash.
- Valid `action: execute` → **HTTP 200** `{"queued": "ui-execute-…"}`;
  one inbox item written (the UI's only documented write surface).

All three servers answered normally after the garbage volley
(`:8803` 404, `:8804` 200, `:8813` 405 to a bare `/`). No crash, no
hang. The custom-header requirement forces a CORS preflight this
server never grants — a hostile web page cannot fire `/api/act`
cross-origin.

## Build-time HTML escaping (briefing / cards)

Sam checked whether a page-derived title/summary could inject HTML
into the built UI. `grep -rn "set:html" ui/src` → **zero matches.**
Astro auto-escapes every `{expr}` interpolation; `Card.astro`
renders `{title}` and `{summary}` as escaped expressions. An
HTML-looking title/summary is escaped in the built markup. (The
page *body* is markdown rendered rich via `<Content />` — rich HTML
there is by design, corpus-authored; out of scope for the
title/summary question.)

Note for the static-UI serving surface: `ui/src/pages/[...slug].astro`
`getStaticPaths` (lines 12–20) builds a page for **every** docs
entry with no filter; `content.config.ts` and `serve.mjs` carry no
`BRAIN_SERVING` handling. So the built static site (a named serving
surface in `SECURITY.md`) renders ai-suggestion drafts as browsable
pages too — same surface-inconsistency as §1.

## Subprocess / shell surface

`grep shell=True` → only `cmd_schedule` (lines 5576/5596), executing
operator-declared `brain-schedule.yml` handlers via the CLI. **Not
reachable from any HTTP request handler.** The serve `/search`
endpoint spawns `mempalace` in argv form (no `shell=True`), so
request input is never handed to a shell. Sam's hard block ("any
listener that executes shell input") is not triggered. Consistent
with `SECURITY.md`: no PTY bridge, no harness subprocess.

## Verdict

Sam does **not** block. The guarantees `SECURITY.md` actually
makes hold by construction: workbench excluded in serving mode,
`/api/act` never mounts in serving mode, no write tools on the MCP,
no shell/PTY on any listener, localhost binding, audit log the
client can't disable. The one gap worth an operator decision: the
ai-suggestions serving-mode exclusion is enforced only on the MCP
surface, not on the `brain.py serve` JSON API, the search CLI, or
the static-UI build — three read surfaces that a reasonable adopter
would expect to behave identically under `BRAIN_SERVING=1`.

## Cleanup

Planted draft removed, the `ui-execute-*` inbox item removed,
`wiki/_views/pages.json` restored to its committed state (a
pre-existing token-count drift, unrelated to this walk), all three
servers stopped. Worktree left clean.
