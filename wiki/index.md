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
- **2026-07-14** — **Shaped (child 2): owner-subscription wake.** The
  epic's headline win — subscribe to a thread/repo/producer and a
  matching event wakes the owner. PRD + [ADR](brain/adrs/owner-subscription-wake.md)
  landed on the operator's webhook pick: signed subscribe events + a
  guarded webhook hint (seq + ref, never a payload), the cursor as the
  at-least-once backstop. Build next — closes the loop.
- **2026-07-14** — **Built (0.27.0): per-agent identity + a signed
  event stream.** The [event-driven epic's](brain/epics/event-driven-agent-triggers.md)
  first child ships — the agentic-future backbone. A hosted brain
  (`BRAIN_HOSTED=1`) authenticates agents with per-agent HMAC keys and
  a signed append-only event stream (`wiki/_state/events`) they read
  cursors over; the auth boundary rejects forged appends at write time
  and drops tampered lines on read. Local-first byte-for-byte
  unchanged. Only owner-subscription wake (child 2) remains.
- **2026-07-14** — **ADR (child 1 bet): per-agent identity on a signed,
  append-only event stream.** The operator picked a new append-only
  event stream under `wiki/_state/events` (over tombstoned inbox items
  and audit-log fan-out) for cursor stability; the auth boundary rejects
  forged appends at write time and verifies attribution on read.
  [ADR](brain/adrs/per-agent-identity.md) + PRD graduated to living;
  awaiting the build.
- **2026-07-14** — **PRD (child 1): per-agent identity for a hosted
  brain.** The epic's first child and true first dependency — a minimal
  identity layer to authenticate and attribute agents, plus the choice
  of where signed events durably live (the inbox is not append-only).
  [Draft PRD](brain/prds/per-agent-identity.md) awaiting approval before
  its ADR.
- **2026-07-14** — **Bet placed: event-driven triggers for multi-agent
  work.** The pitch graduated into an
  [epic](brain/epics/event-driven-agent-triggers.md) — the brain's
  first. Children spawn in dependency order: per-agent identity first
  (the one new component hosting forces), then owner-subscription wake.
- **2026-07-14** — **Pitch: event-driven triggers for multi-agent
  work.** The 4-agent session's topic graduated into a pre-bet Shape Up
  [pitch](brain/pitches/event-driven-agent-triggers.md) — an agentic
  future where an agent's action wakes the agents who care, via a
  read-side fan-out over the brain's existing records (never a
  scheduler). Awaiting a bet; on a bet it becomes an epic (per-agent
  identity first, then owner-subscription wake).
- **2026-07-14** — **Live 4-agent session on the brain.** Three agents
  chatted in a channel while a fourth ran the brain and pushed events
  between them — dogfooding the conversation surface for real
  multi-agent work. It produced a topic:
  [event-driven triggers for multi-agent work](brain/topics/event-driven-multi-agent.md).
  Agreed shape: read-side fan-out over the append-only inbox (notify is
  a wake hint, not a scheduler); authenticated per-agent identity is the
  one new component hosting forces; MVP is owner-subscription wake.
- **2026-07-14** — **Built: graph & connector as page trust signals
  (0.26.0).** The provenance graph and structure connector were
  agent-facing plumbing invisible to users. Now every page shows how
  many pages rely on it, and an "⚑ Uncertain but load-bearing" banner
  on low-confidence pages others depend on; a repo page surfaces
  structure drift inline once a repo is configured. Answers "how does
  this reflect for our users."
- **2026-07-14** — **Built: topics lead with an executive brief
  (0.25.0).** Arriving to weigh in on a topic no longer means reading
  the whole discussion first. The page opens with the summary, a
  "what's being decided" callout (the Question), and the Respond
  control; the full discussion collapses behind one toggle. Also fixed:
  the compose box now stays hidden until you open it.
- **2026-07-14** — **Built: one unified collaboration control
  (0.24.0).** Comment, queue, and post-to-thread were scattered across
  cards, pages, and channels with no way to edit or undo them. Now a
  single control appears everywhere with full CRUD — comment / queue /
  post plus **edit** and **unqueue** of your own pending items — all
  backed by the inbox. New `edit`/`remove` actions and a `/api/pending`
  read support it.
- **2026-07-14** — **Built: an async conversation surface over the
  inbox (0.23.0).** A `/channels/` surface renders every topic as a
  channel; each topic grows a Thread panel with a compose box. A post
  is an inbox write (the inbox-only-write invariant holds) and the
  agent replies in-thread on the next tend. Async by construction — no
  live chat, no scheduled LLM. The RFC's objections answered as code:
  server-stamped attribution (unforgeable by a browser page), post
  text fenced as untrusted data before it reaches the agent, and the
  write endpoint withheld in serving mode. Third of the three
  ingest-driven builds — the one the RFC had marked no-go, built to
  the RFC's own standard.
- **2026-07-14** — **Built: a deterministic structure connector
  (0.22.0).** A sixth built-in connector snapshots a repo's code shape
  (source-file inventory + package counts, exact; Python top-level
  symbols via `ast`) — no network, no external binary, no LLM — and
  turns architectural drift into inbox items via a baseline diff.
  Drift auto-clears by citation once a wiki page cites the snapshot
  that raised it. Vendor-neutral (the brain computes the facts
  itself), guarded (scrubbed env, read-only git, secret-scan,
  structural-only summaries), and shipped off — this instance has no
  active sibling repos. Second of the three ingest-driven builds.
- **2026-07-14** — **Built: the link graph carries per-edge
  provenance (0.21.0).** `brain.py` emits one tagged edge list to
  `wiki/_views/graph.json` — authored links/`depends_on` are
  EXTRACTED, machine-suggested links are INFERRED — with AMBIGUOUS
  flags on low-confidence pages the graph leans on.
  [`/graph/`](brain/topics/three-ideas-compose.md) renders solid vs
  dashed edges and flags AMBIGUOUS nodes, the UI reads the one list
  (no more two-implementation gap), MCP page reads expose the tags,
  and serving mode strips draft nodes and their edges. First of the
  three ingest-driven builds; the corrected design the RFC landed.
- **2026-07-14** — **RFC: the "one loop" synthesis didn't survive
  review.** Five personas deepdived
  [the topic](brain/topics/three-ideas-compose.md); unanimous verdict:
  the loop framing is an overfit narrative (the pieces touch disjoint
  graphs; the real bus is the inbox, which exists). Revised to three
  independent bets — connector (drift) gated, conversation surface a
  no-go on prompt-injection + settled-decision grounds, provenance
  tags standalone with a corrected design. The review dismantling the
  synthesis is the value.
- **2026-07-14** — **synthesis: the three ideas are one loop.** A
  [topic](brain/topics/three-ideas-compose.md) ties the async
  conversation surface, the deterministic structure connector, and
  edge-provenance tags into a single arc: provenance is the
  connective tissue (connector → EXTRACTED, synthesis → INFERRED,
  drift → AMBIGUOUS, conversation resolves it). Sequence it
  provenance → connector → conversation; the conversation surface
  earns its build only after the other two make it worth it.
- **2026-07-14** — **ingested Graphify; deepdive + benefit suggestion.**
  A four-agent deepdive of
  [Graphify](https://github.com/Graphify-Labs/graphify) — a
  code-graph tool with an optional LLM doc layer, a viral (~85k-star,
  pre-1.0, hype-heavy) near-peer. It mostly *validates* the brain
  (token thesis, deterministic/LLM split, provenance discipline). One
  genuinely-new borrow: per-edge provenance tags
  ([suggestion](brain/ai-suggestions/prds/edge-provenance-tags.md)),
  deterministic, rendered on the existing /graph/ SVG. Full deepdive
  in `sources/research/2026-07-14--graphify-llm-knowledge-graph.md`.
- **2026-07-14** — **ingested Enola; deepdive + benefit suggestion.**
  A four-agent directed-research deepdive of
  [Enola](https://github.com/enola-labs/enola) — a deterministic,
  LLM-free code-structure extractor. It's the brain's inverse: it
  extracts the *what*, the brain synthesizes the *why*. Strongest
  fit is a deterministic structure *connector*
  ([suggestion](brain/ai-suggestions/prds/deterministic-structure-connector.md))
  that turns architecture drift into inbox items — gated on the
  tool's pre-1.0 solo maturity. Full deepdive in
  `sources/research/2026-07-14--enola-deterministic-architecture-extractor.md`.
- **2026-07-13** — **AI-suggestion: an async conversation surface.**
  On the operator's Slack-shaped-UI question, a draft
  ([suggestion](brain/ai-suggestions/prds/conversation-surface-over-inbox.md))
  proposes threaded channels over the existing inbox — topics as
  channels, replies during tend, an Activity tab — explicitly *not*
  the chat pane the brain removed twice. `confidence: low`, awaiting
  review.
- **2026-07-12** — **personal-data guard wired into the harness.** A
  `commit-msg` git hook + a `/pr` check
  ([`brain.py check-no-personal-data`], [ADR](brain/adrs/no-personal-data-in-public-artifacts.md))
  reject session URLs and account-tied links in commit messages and
  PR bodies — deterministically, so no harness directive can leak
  them. Setup installs the hook; a PR template + CONTRIBUTING note
  carry the human-facing convention. Every born instance inherits it.
- **2026-07-12** — **delivered: operator-trust fixes (Viktor cluster).**
  Producer death is now first-class health — a heartbeat lets
  `doctor` fail distinctly when the accumulation loop stalls, and
  the app strip says "producers stalled" instead of a calm "queue
  clear". Recurring tend items gain `inbox ack` (suppress until the
  page actually changes — no metadata falsified); `inbox
  pending-grades` and a sample-sized dashboard stat make the
  attention-calibration loop legible.
- **2026-07-12** — **delivered: serving-mode hardening (Sam cluster).**
  The ai-suggestions draft exclusion now holds on every read surface
  in serving mode — the `brain.py serve` JSON API, `pages.json`,
  `/views/*`, the `search` CLI, and a serving-mode static UI build —
  not just the MCP. And the MCP HTTP surface gained the same loopback
  `Host`-header guard `brain.py serve` uses, so anti-DNS-rebinding
  holds by construction on both. SECURITY.md states each property
  once.
- **2026-07-12** — **delivered: reader-trust fixes (Priya cluster).**
  Generated reading lists and the trail now mark superseded status
  and render human titles instead of raw slugs; custom/role views
  read like briefs (title links, purpose-first, human empty states,
  generation note demoted to a footer); a build-time render-proof
  fails the UI build if any AI-suggestion page loses its trust
  banner. Three draft summaries fixed.
- **2026-07-12** — **playthrough sweep: 8 AI-suggestions for review.**
  A three-persona sweep (Viktor / Priya / Sam, six agent runs)
  walked the product and landed eight `confidence: low` drafts under
  [brain/ai-suggestions](brain/index.md#ai-suggestions-drafts-for-human-review)
  plus a serving-mode insight. All security guarantees held under
  Sam's adversarial probe.
- **2026-07-12** — **0.19.4: fixed a governance misreport.** `doctor`
  and `/dash` read `LOCAL_FIRST` by substring, matching the
  commented `.env.example` boilerplate — so they reported
  "local-first" after the flag was removed. Now anchored to the
  canonical line test. Found by the Viktor daily-operator
  playthrough.
- **2026-07-12** — **0.19.3: PR mode + detector teeth.** The
  operator removed LOCAL_FIRST — every change now lands via PR with
  CI green. The internal-refs detector reads UI source strings
  (catching a dangling deck reference immediately) and a
  machine-local denylist closes the client-term leak class without
  the terms ever entering the repo.
- **2026-07-12** — **the repo is public.** The visibility gap on the
  [market-readiness topic](brain/topics/market-readiness-gaps.md)
  closes; security reports now go through GitHub private
  vulnerability reporting (personal email removed from SECURITY.md
  and packaging; repo-local git author switched to the noreply
  address).
- **2026-07-12** — **0.19.1: the delegated cold-start.** The
  operator delegated the 1.0 gate's cold-start test; the full
  tutorial ran against a born instance with a real OSS ingest
  (transcript at
  `sources/playthroughs/2026-07-12--delegated-cold-start--instance-tutorial.md`;
  criteria 3 + 4 evidence on the
  [topic](brain/topics/one-point-oh-criteria.md)). Fixed en route:
  CI ran pytest before the UI build (main is green again), the
  empty-brain guidance never fired on born instances, and `setup`
  now ends with the next command verified to work. The
  [insight](insights/quickstart-third-command-fragility.md) is
  acted on.
- **2026-07-12** — **0.19.0: onboarding surfaces.** The deck
  rewritten to the current product (+ first-session tutorial);
  README points at it; shelf homes render generated Project
  overviews (reading path, open work, freshness, honest gaps) —
  [ADR amendment](brain/adrs/human-legible-presentation-layer.md).
  The refresh caught a leftover origin-org repo description in the
  old deck (standalone guarantee).
- **2026-07-12** — **0.18.0: the briefing becomes two-way.**
  Filters + pagination, `/dashboard/` + `/trail/` + `/graph/`, and
  the interactive channel — queue/comment clicks on any card or
  page become inbox items the next tend digests
  ([ADR amendment](brain/adrs/human-legible-presentation-layer.md)).
  The presentation-layer bet closes.
- **2026-07-12** — **0.17.0: the briefing is the UI.** The
  presentation-layer bet shipped as a complete UI rewrite
  ([PRD](brain/prds/human-legible-presentation-layer.md) ·
  [ADR](brain/adrs/human-legible-presentation-layer.md)): the app's
  root is now the brain's judgement — Needs you / In flight / On
  the table + orientation — with executive summaries in the schema,
  lifecycle chrome on every page, and attention verdicts
  (`inbox judge`/`grade`) from the tend loop. The Priya playthrough
  caught three defects in-session, including five shipped PRDs
  still claiming in-flight.
- **2026-07-12** — **pitch on the table: human-legible presentation
  layer.** Big appetite, awaiting the operator's bet
  ([pitch](brain/pitches/human-legible-presentation-layer.md)):
  Shape Up-native opinionated UI, attention triage in the tend
  loop, summaries as schema. The Ruby/Rust rewrite question was
  answered no in the same conversation (capture cited in the
  pitch).
- **2026-07-12** — **0.16.0: the persona playthrough loop.** User
  personas for the brain-as-product
  ([PRD](brain/prds/persona-playthrough-loop.md) ·
  [ADR](brain/adrs/persona-playthrough-loop.md)): `/playthrough`
  executes scenarios for real, transcripts snapshot to
  `sources/playthroughs/`, findings become `confidence: low`
  insights until a human confirms, and every version bump queues a
  sweep. The dogfood walk (Noor, cold-start) caught two defects —
  non-tty setup auto-consent and a raw-JSON first-run app pane —
  both fixed in-session, plus one open
  [insight](insights/quickstart-third-command-fragility.md).
- **2026-07-12** — **0.15.0: surfaces settle at MCP + CLI.** The
  embedded terminal removed on the operator's call
  ([superseding ADR](brain/adrs/mcp-cli-surface.md)) — it was an
  arrangement of windows, not a capability, and the kernel's
  largest security surface. The app page is now the rendered
  knowledge under the ambient strip; the billing guard degrades to
  a `doctor` warning. The
  [topic](brain/topics/chat-surface-necessity.md) is settled twice
  over.
- **2026-07-12** — **0.14.1: license changed to MIT** (operator
  direction; revised from Apache-2.0 pre-any-public-release).
  NOTICE removed, packaging metadata updated,
  [topic](brain/topics/market-readiness-gaps.md) amended.
- **2026-07-12** — **0.14.0: surfaces simplified.** The chat pane
  removed on the operator's call
  ([superseding ADR](brain/adrs/mcp-cli-terminal-surface.md)) —
  MCP + CLI + terminal cover it better; strip, entry point,
  install-agent, billing guard kept. The
  [topic](brain/topics/chat-surface-necessity.md) is settled.
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
  studied against prior art in the space. Pre-bet.
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
  see [brain/roadmap.md](brain/roadmap.md); the prior-art study
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
- [MCP + CLI surface](brain/adrs/mcp-cli-surface.md) — the
  embedded terminal retires; surfaces settle, decided 2026-07-12.
- [Workbench PTY bridge](brain/adrs/workbench-pty-bridge.md) — the
  harness-workbench bet, decided 2026-07-10; superseded 2026-07-12.
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
