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
