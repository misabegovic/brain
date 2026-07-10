---
title: "Brain — state"
kind: reference
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../AGENTS.md
---

# Brain — state

Where the brain itself was, is, and wants to be. `/capture brain`
routes brain-self observations (workflow gaps, schema rough edges)
into the sections below.

## Cross-level context

*(none yet)*

## Past

- **2026-07-10** — kernel extracted as a standalone, client-agnostic
  shell: schema, tools, skills, personas, UI, CI, tests; content
  layers start empty.

## Now

- **Standing constraint (operator, 2026-07-10):** this repository is
  the tool's own project, permanently — `active_repos` stays empty
  here; the brain dogfoods itself. Adoption for real projects
  happens in separate instances of this kernel. The doctor's
  "unconfigured shell" warning is expected here forever.

- **Topics + regenerative schema live (0.10.0, 2026-07-10).**
  Discussion threads as first-class pages; constraints +
  implementation-memory in the permanent layer; Fowler synthesis on
  the methodology shelf; one topic open.

- **Every read is a briefing (0.9.0, 2026-07-10).** Page reads
  carry graph context; wiki saves get instant lint feedback; audit
  lines carry `by:` attribution; the rendered wiki owns the local
  server root (stress-test fix) and works styled inside the
  workbench — verified in a real browser session.

- **Work happens inside the brain (0.8.0, 2026-07-10).** The
  rendered wiki serves at `/ui` on the local server; the workbench
  navigates dashboard/wiki/views beside the terminal; stale builds
  self-heal via the change signal; sidebar mirrors the shelves;
  `VERSION` + `--version` ship. First operator lesson recorded.

- **Hosting profile is live (0.7.0, 2026-07-10).** `deploy/`
  (Dockerfile, entrypoint, compose on non-default ports) +
  `railway.toml`; per-instance isolation (env ports, hashed timer
  units — this checkout's timer migrated). Emulated locally beside
  the client brain with zero contention. Codeplain captured on the
  competitor shelf ($3M seed; spec-regeneration thesis = the
  brain's mission #1, validated commercially).

- **The workbench is live (0.6.x, 2026-07-10).** `brain workbench`:
  terminal beside the rendered brain, harness launches, live
  reload; `install-agent` registered all four harnesses in this
  checkout. Verified end-to-end (websocket handshake + PTY echo +
  serving-mode refusal in tests).

- **Serving software is ready (0.6 software half, 2026-07-10).**
  MCP over streamable HTTP, serving-mode guardrails (suggestion
  exclusion + query audit log), and the Datasette pilot over the
  derived index. Deployment (host + identity proxy) is the
  remaining operator choice.

- **Composable views are live (0.5.0, 2026-07-10).** Derived
  SQLite index (FTS5) rebuilt on every views run; SQL view specs in
  `views/` render to `wiki/_views/custom/` (engineer / pm /
  operator examples); `brain.py query` for ad-hoc read-only SQL;
  Datadog + Langfuse connectors with state extracts. Full trail:
  pitch → deepdive → PRD → ADR → build, all human-gated inline.

- **Pruning + deepening are live (0.4.0, 2026-07-10).**
  `brain.py links` health views; `inbox-refresh` now queues
  per-kind half-life crossings, orphans, research picks (low
  confidence × high centrality), and coverage gaps. Three research
  items are pending on the shell's own hub ADRs.

- **Connectors are live (0.3.0, 2026-07-10).** GitHub (releases +
  merged-PR batches, sibling-remote auto-discovery), Notion
  (watched-page re-snapshots on `last_edited`), Slack (per-channel
  daily transcripts) — all pull-only snapshot-writers per the
  connector contract ADR, no-ops until `connectors:` +  `.env`
  tokens are set. New batches queue inbox items for `/tend`.

- **The hands-off surface is live (0.2.x, 2026-07-10).**
  `brain.py setup` (one-command idempotent bootstrap), `brain.py
  doctor` (health checklist with fixing commands), `serve /dash`
  (server-rendered ops page: health + tend queue + quick start),
  and the `brain tend` / `brain dash` wrapper verbs. Terminal users
  bootstrap with one command; non-terminal users read the dashboard.
- **Queue-and-tend is live (0.2.0, 2026-07-10).** Deterministic
  producers accumulate per-item JSON into `wiki/_state/inbox/`
  (`inbox-refresh` op: cursor diffs, half-life crossings, link
  health; operator-defined producers via
  `tools/producers/example-producer.sh` + a `brain-schedule.yml`
  entry). `/tend` digests in-session; a session-start hook surfaces
  the one-line summary. The local timer installs via
  `tools/install-timer.sh` — not yet installed on any machine.

- Empty shell awaiting an organisation's content. `brain.config.yml`
  declares no active repos yet.
- Every scheduled operation degrades to a clean no-op on the empty
  shell; the state-refresh ops (`security-scan`, `issues-pull`)
  bootstrap their repo maps from `brain.config.yml` on first run.
- `reflection-check internal-refs` enforces the standalone
  guarantee: every repo-path reference in the kernel surface must
  resolve inside the repo.
- Deadline tracking is generic: `wiki/_state/deadlines.json` holds
  named dates (compliance, renewals, launches); the weekly
  `deadline-countdown` op refreshes days-left.

## Perceived

*(no Now-vs-Perceived gaps recorded yet)*

## Target



- Adopt for a project: fill `brain.config.yml`, author team/user
  personas, run the first `/in` ingest.
- The 0.x arc per [roadmap.md](roadmap.md) (operator intent captured
  2026-07-10): scheduled autonomy (0.2) → connector snapshot-writers
  for Slack / Notion / GitHub (0.3) → pruning + deepening with a
  research loop (0.4) → a read-only grounded chat plane for people
  outside the product (0.5) → the self-hosting profile that carries
  it (0.6). Local-first stays the default operating mode throughout.

## Open threads

*(none yet — `/capture brain` appends here)*
