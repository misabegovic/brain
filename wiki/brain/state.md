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

- **A deterministic structure connector ships (0.22.0,
  2026-07-14).** A sixth built-in connector snapshots a target repo's
  code shape — the source-file inventory + package counts
  (language-agnostic, exact) and Python top-level symbols (exact via
  `ast`) — with no network, no external binary, and no LLM. It writes
  an immutable snapshot to `sources/structure/`, diffs against the
  previous snapshot, and queues an architectural-drift inbox item when
  the code moved (`architecture.md` may be stale) — a strict upgrade
  over the git-name-only cursor diff. Drift auto-clears by citation:
  the item resolves once a wiki page cites the snapshot that raised it
  (the reconciler the RFC found missing). Guards land as code:
  scrubbed env, read-only git with a git-clean post-condition, a
  secret-scan before the immutable write, structural-only summaries,
  brain-computed filenames. Vendor-neutral by construction — the brain
  computes the facts itself, so nothing depends on a pre-1.0 extractor
  binary. Ships **off** (`connectors.structure.repos: []`); this
  dogfooding instance has no active sibling repos to point at. Second
  of the three ingest-driven builds (the Enola pattern).

- **The link graph carries per-edge provenance (0.21.0,
  2026-07-14).** `brain.py` emits one tagged edge list to
  `wiki/_views/graph.json` — EXTRACTED for authored links and
  `depends_on`, INFERRED for machine-suggested links (shared
  `repos:`/`affects:`) — plus AMBIGUOUS node flags (a low-confidence
  page ≥2 others lean on). `/graph/` renders it (solid authored /
  dashed-faint suggested edges, ⚑ dashed AMBIGUOUS nodes with a
  legend); the UI now reads that one list instead of re-deriving an
  untagged graph, closing the two-implementation gap. MCP page reads
  surface the same tags (an agent sees which links are suggested, not
  authored, and whether a page is AMBIGUOUS), and serving mode strips
  ai-suggestion nodes *and* every edge touching one before any
  read/render. The first of the three ingest-driven builds
  ([three ideas](ai-suggestions/prds/edge-provenance-tags.md), Graphify
  borrow); deterministic, no LLM in the producer.

- **PR mode is the operating mode (2026-07-12).** The operator
  removed `LOCAL_FIRST` from this brain's `.env`: agents work on
  feature branches, every change lands via PR with CI green, and
  `/shape` outputs need human-approved review before merge. Named
  deviations from the local-first period (inline-approved ADRs to
  the accepted shelf, direct pushes) are closed going forward.

- **The standalone guarantee grew teeth (0.19.3, 2026-07-12).**
  internal-refs now reads UI source strings (the onboarding-deck
  leak class) — and caught a dangling ADR reference on arrival —
  and a machine-local, never-committed denylist
  (`.reflection-denylist`, `BRAIN_DENYLIST` override) lets an
  operator flag client terms without shipping them.

- **Onboarding is built in (0.19.0, 2026-07-12).** The deck teaches
  the current product (incl. a first-session tutorial); the README
  points to it; every shelf home doubles as a generated project
  overview for team onboarding. A leftover origin-org repo
  description in the old deck was caught and removed.

- **The briefing is two-way (0.18.0, 2026-07-12).** Type filters +
  pagination, dashboard/trail/graph read surfaces, and the
  interactive channel: queue/comment clicks become inbox items
  (`produced_by: ui-action`) the next tend session digests —
  humans still act through their agent; the click just hands the
  agent work faster. The presentation-layer bet closes with its
  within-appetite remainders delivered.

- **The briefing is the UI (0.17.0, 2026-07-12).** Complete UI
  rewrite on the operator's bet: Starlight out, purpose-built Astro
  app in — the root is the partner's briefing (attention verdicts,
  bets, discussions, orientation), pages carry lifecycle chrome and
  executive summaries, and the tend loop judges connector signal
  (`inbox judge`/`grade`, routine-by-default). Follow-ups within
  appetite: trail timeline, link-graph visual.

- **The playthrough loop is live (0.16.0, 2026-07-12).** Synthetic
  users walk every release: personas in
  `.claude/personas/users/`, `/playthrough` protocol, transcripts
  at `sources/playthroughs/`, findings as confidence-capped
  insights, sweeps queued per version bump. First walk (Noor,
  cold-start) fixed two setup/first-run defects in-session.

- **Surfaces settled at MCP + CLI (0.15.0, 2026-07-12).** The
  embedded terminal removed by superseding ADR
  ([mcp-cli-surface](adrs/mcp-cli-surface.md)) the same week as the
  chat pane: the PTY bridge, websocket slice, xterm assets, and
  launch registry are gone. The app page is the rendered knowledge
  under the ambient strip; the operator's harness runs in their own
  terminal over MCP. The billing guard degrades to a `doctor`
  warning (nothing app-spawned remains to strip).

- **Surfaces simplified (0.14.0, 2026-07-12).** MCP + CLI +
  terminal; the chat pane removed by superseding ADR on the
  operator's call. Strip, entry point, install-agent, billing
  guard retained.

- **The chat builds (0.13.0, 2026-07-10).** Chat turns can author
  (acceptEdits); the positioning page and the market-gaps topic
  were built through the chat by the nested agent, gates-clean.
  Six market-readiness items queued; license + name await the
  operator.

- **The chat-first app is live (0.12.0, 2026-07-10).** Conversation
  as the interface on the operator's picks (registry / toggle /
  full collapse); a real turn verified end-to-end. The mechanism's
  vocabulary is now a power-user concern.

- **Instance birth is live (0.11.0, 2026-07-10).** One command
  births a gate-passing instance; the contamination boundary is an
  explicit manifest; 1.0 criteria settled (birth passes; the rest
  need calendar time + a real adoption).

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
  another local brain instance with zero contention.

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
