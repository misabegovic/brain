---
title: "Brain — home"
kind: meta
status: draft
updated: 2026-07-10
confidence: high
sources:
  - ../AGENTS.md
---

# Brain — home

An empty brain shell — an LLM-maintained knowledge base awaiting its
organisation's content. Fill `brain.config.yml`, add per-repo
shelves under `wiki/<repo>/`, and the dashboard sections below
start filling in as the slash-command surface runs.

## What changed

<!-- home-section; maintained-by: /shape -->
- **2026-07-12** — first two unattended days: both local timer runs
  finished clean (1.0 criterion #2: 2/7). Dogfooding finding: the
  inherited CI cron was a second runner auto-committing divergent
  state — disarmed to manual-dispatch per the queue-and-tend ADR
  (amendment recorded). Accumulation committed; inbox honestly
  empty (grace period).
- **2026-07-10** — **0.13.1: market-readiness.** Apache-2.0 adopted
  (operator pick); CHANGELOG / CONTRIBUTING / SECURITY / NOTICE;
  `pyproject.toml` packaging; first tagged release; docs-publish
  workflow ready (gated on repo visibility). Name deferred by the
  operator — [topic](brain/topics/market-readiness-gaps.md)
  partially settled.
- **2026-07-10** — **market-readiness gaps opened as a topic.** Six
  repo-verified gaps between the kernel and a credible market entry
  ([topic](brain/topics/market-readiness-gaps.md)): no LICENSE, a
  generic un-ownable name, no releases/tags, no public docs, no
  install artifact, no community files. Each queued as a
  `market-gap-*` inbox item; license and name are operator
  decisions, the rest sequence behind them.
- **2026-07-10** — **competitive positioning drawn.** The kernel's
  market position synthesised at
  [org/competitive-positioning.md](org/competitive-positioning.md):
  LLM-maintained knowledge substrates as the category, positioned
  against open-knowledge (editor-first), Codeplain (codegen
  platform), and plain wikis/Notion (no agent mechanism) — the
  governance rail, queue-and-tend economics, instance birth,
  harness independence, and chat-as-interface named as the moat.
- **2026-07-10** — **0.12.2: the billing guard.** Harness
  subprocesses (chat + terminal) have API-key env vars stripped by
  construction — a turn can only bill the logged-in subscription;
  `chat.allow_api_keys` opts back in; doctor warns when keys are
  present. Verified: this machine had no keys set, so all session
  turns were subscription-billed. Recorded as an amendment on the
  [chat ADR](brain/adrs/chat-print-mode-bridge.md).
- **2026-07-10** — **0.12.1: persona-playthrough upgrades.** Three
  personas driven through the live UI (newcomer / operator / PM);
  fixes: composer autofocus, markdown-lite bubbles, suggestion
  chips. Chat continuity verified across turns; the agent in the
  chat flagged the session's own uncommitted diff unprompted.
- **2026-07-10** — **0.12.0 shipped: the chat-first app.** Bare
  `brain` opens one window: conversation (print-mode bridge, on
  your subscription — [ADR](brain/adrs/chat-print-mode-bridge.md)),
  live knowledge beside it, ambient status, terminal behind a
  toggle. Verified with a real chat turn driving the mechanism.
- **2026-07-10** — **0.11.0 shipped: instance birth.** `init --full`
  births a working instance from the kernel manifest (mechanism +
  kernel trail cross; dogfood never does), verified by its own gates
  and a suite test. The **1.0 gate** is settled as five observable
  criteria ([topic](brain/topics/one-point-oh-criteria.md)) —
  birth (passing), a self-running week, a real-data loop, cold-start
  onboarding, all-green at tag.
- **2026-07-10** — tend sweep 2: the epic ADR, the roadmap, and the
  operator-lessons shelf verified against the shipped mechanism and
  promoted to `confidence: high`; queue cleared. Standing constraint
  recorded: this repo is the tool's own project, permanently — real
  adoption happens in separate instances. The sweep also earned the
  mechanism's **first dogfooding amendment**: the research picker now
  skips policy-tier kinds (topics, pitches, initiatives) and gives
  pages a 7-day grace period — recorded on the
  [queue-and-tend ADR](brain/adrs/queue-and-tend-inbox.md).
- **2026-07-10** — **0.10.0 shipped: topics + the regenerative
  schema.** `kind: topic` discussion threads (dated, attributed,
  graduating into ADRs), Fowler's
  [Phoenix Architecture ingested](org/methodology/regenerative-software.md),
  and two new permanent pages per repo: `constraints.md` and
  `implementation-memory.md`. First
  [topic](brain/topics/regenerative-schema-extensions.md) is open.
- **2026-07-10** — **0.9.0 shipped: every read is a briefing.**
  Graph-context page reads (`brain.py page` + MCP), write-time
  lint feedback on wiki saves, `by:` attribution in the audit log —
  and the UI stress test's structural fix: the rendered wiki now
  owns the local server's root, styled and navigable inside the
  workbench.
- **2026-07-10** — **0.8.0 shipped: work happens inside the brain.**
  Rendered wiki at `/ui`, workbench navigation
  (dashboard ↔ wiki ↔ views), self-healing UI rebuilds, a sidebar
  that mirrors the shelves, `VERSION`/`--version`, and the first
  [operator lesson](org/operator-lessons.md).
- **2026-07-10** — **0.7.0 shipped: hosting.** One infra-agnostic
  image (`deploy/`), Railway reference config, env-selected public
  surface; instance isolation (env ports + hashed timer units)
  verified by emulation beside the client brain. Codeplain ($3M
  seed, spec-regeneration) captured on the
  [competitor shelf](org/competitors/codeplain/index.md).
- **2026-07-10** — **harness workbench shipped (0.6.x).**
  `brain workbench` puts your harness terminal beside the rendered
  brain (loopback PTY bridge, one-click launches, live reload);
  `install-agent` wires claude / cursor / codex / opencode to the
  brain's MCP. Full trail:
  [PRD](brain/prds/harness-workbench.md) ·
  [ADR](brain/adrs/workbench-pty-bridge.md).
- **2026-07-10** — tend sweep: the deepening picker's three research
  items digested — both hub ADRs verified against the shipped
  mechanism and promoted to `confidence: high` (verification note in
  `sources/research/`); the workbench-pitch item cleared as moot by
  its graduation.
- **2026-07-10** — pitch captured + deepdived:
  [harness workbench](brain/pitches/harness-workbench.md) — terminal
  in the brain's local UI with per-harness launch/config adapters,
  studied against open-knowledge's implementation. Pre-bet.
- **2026-07-10** — **0.6 software half shipped: the serving plane.**
  MCP streamable-HTTP transport, `BRAIN_SERVING=1` guardrails
  (ai-suggestions excluded, query audit log), and the Datasette
  pilot over the derived index. Deployment/SSO remains the
  operator's infra choice.
- **2026-07-10** — **0.5.0 shipped: composable role-fit views.**
  Derived SQLite index + FTS5 riding every views run; SQL view
  specs in `views/` rendering to
  [custom views](_views/custom/engineer.md); `brain.py query`;
  Datadog + Langfuse connectors. Full /shape trail:
  [PRD](brain/prds/composable-role-views.md) ·
  [ADR](brain/adrs/sql-views-over-derived-index.md).
- **2026-07-10** — the views bet's
  [ADR](brain/adrs/sql-views-over-derived-index.md) landed: SQL over
  a derived disposable index, shorthands compile to SQL, index rides
  the views pipeline.
- **2026-07-10** — views pitch **graduated on the operator's bet**:
  [PRD](brain/prds/composable-role-views.md) landed; ADR + build
  follow in the same cycle.
- **2026-07-10** — views pitch **deepdived**: five research notes
  in `sources/research/` (SQLite/FTS5 mechanics incl. a live
  prototype at 19 ms / 304 KB, Datasette pilot recommendation,
  prior-art lessons from Obsidian Bases / Steampipe / Logseq,
  Datadog + Langfuse API specifics) woven into the
  [pitch](brain/pitches/composable-role-views.md) — decision-ready.
- **2026-07-10** — pitch captured:
  [composable role-fit views](brain/pitches/composable-role-views.md)
  — per-role view assemblies over connector data (incl. proposed
  Datadog / Langfuse connectors). Pre-bet; awaiting the operator's
  call.
- **2026-07-10** — **0.4.0 shipped: pruning + deepening.**
  `brain.py links` link-graph health, per-kind half-life scanning,
  orphan detection, the research picker (low confidence × high
  centrality), and coverage-gap items — all deterministic
  `inbox-refresh` producers feeding `/tend`.
- **2026-07-10** — **0.3.0 shipped: connectors.** GitHub / Notion /
  Slack pull connectors under one
  [snapshot-writer contract](brain/adrs/connector-snapshot-contract.md) —
  immutable dedup snapshots into `sources/`, cursors, inbox items
  out, never a wiki write; all no-op until configured.
- **2026-07-10** — **hands-off surface shipped (0.2.x).**
  One-command `brain.py setup`, a `doctor` health checklist, a
  server-rendered ops dashboard at `serve /dash`, and `brain tend` /
  `brain dash` wrapper verbs — terminal users bootstrap in one
  command; the dashboard covers everyone else.
- **2026-07-10** — **0.2.0 shipped: queue-and-tend.**
  `brain.py inbox` (per-item queue at `wiki/_state/inbox/`), the
  `inbox-refresh` producer op, the [`/tend`](brain/adrs/queue-and-tend-inbox.md)
  skill, session-start surfacing, a local-timer installer, and a
  custom-producer template. Decision recorded as an accepted ADR.
- **2026-07-10** — roadmap detail: the inbox is an open producer
  contract (per-item JSON + `brain.py inbox add`, operator-defined
  cron producers welcome), and agent-independence is a cross-cutting
  principle — gates in git/CI, credential-scoped connectors,
  per-harness adapters over one canonical protocol set.
- **2026-07-10** — 0.x arc revised to the **queue-and-tend** model
  per operator constraint: no scheduled LLM invocation — cron
  accumulates deterministic work into an inbox, the operator's normal
  terminal sessions digest it via a `/tend` skill; external access
  goes MCP-first (consumers bring their own agent and inference).
- **2026-07-10** — operator intent for the 0.x arc captured
  (self-maintenance, connectors, pruning/deepening, external chat) —
  see [brain/roadmap.md](brain/roadmap.md); the open-knowledge study
  is snapshotted in `sources/conversations/`.
- **2026-07-10** — kernel hardening from the ADR review: the
  client-specific compliance countdown became a generic
  `deadline-countdown` op over `wiki/_state/deadlines.json`, the
  state-refresh schedule ops now bootstrap from `brain.config.yml`
  and no-op cleanly on an empty shell, and a new `internal-refs`
  reflection detector enforces the standalone guarantee.
- **2026-07-10** — kernel decision trail ported: 11 brain-meta ADRs,
  the authoring guidance page, and the org methodology shelf
  (way-of-working, development playbook, superpowers) landed in
  sanitized, organisation-agnostic form. The shell is now fully
  standalone — every internal reference resolves.

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Open initiatives

<!-- home-section; maintained-by: /shape -->
- [Brain roadmap — the 0.x arc](brain/roadmap.md) — **0.2 through
  0.8 shipped**; the arc from the operator's original intent is
  complete. What remains is adoption: point it at a project.

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Recent decisions

<!-- home-section; maintained-by: /shape -->
- [SQL views over a derived index](brain/adrs/sql-views-over-derived-index.md)
  — the composable-views bet, decided 2026-07-10.
- [Workbench PTY bridge](brain/adrs/workbench-pty-bridge.md) — the
  harness-workbench bet, decided 2026-07-10.
- [Kernel ADR trail](brain/index.md#adrs) — 11 mechanism decisions
  (shape pitches, epics, deepdive pre-flight, parallelism, zoom-out,
  home shape, UI substrate, operator lessons, competitor intel)
  recorded 2026-07-10 as ports from the origin deployment.

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Drift surface

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no /groom run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Insights now

<!-- home-section: empty; maintained-by: /feedback -->
*(empty — no /feedback run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Brain trajectory

<!-- home-section; maintained-by: /groom -->
- The 0.x arc is recorded at [brain/roadmap.md](brain/roadmap.md):
  scheduled autonomy → connectors (Slack / Notion / GitHub) →
  pruning + deepening → read-only chat plane → self-hosting profile.
  Governance rail unchanged throughout; local-first stays default.

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Curated picks

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no /groom run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Where to find things

- [Brain — meta level](brain/index.md)
- [Org — methodology + cross-product](org/index.md)
- Per-repo shelves arrive as you add them: `wiki/<repo>/index.md`
