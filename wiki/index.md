---
title: "Brain — home"
kind: meta
status: draft
updated: 2026-07-10
confidence: high
sources:
  - ../AGENTS.md
enola_intent:
  page:
    type: meta
    status: draft
    origin:
    - repo
---
# Brain — home

An empty brain shell — an LLM-maintained knowledge base awaiting its
organisation's content. Fill `brain.config.yml`, add per-repo
shelves under `wiki/<repo>/`, and the dashboard sections below
start filling in as the slash-command surface runs.

## What changed

<!-- home-section; maintained-by: /shape -->
- **2026-08-06** — **The standalone guarantee re-verified at zero.**
  A lineage sweep closed the denylist detector's three standing
  findings, all from the attention-board slice: the PRD's sources now
  cite this repo's own files (also the resolvable citation), and the
  config leak-guard test assembles its guard terms from halves so the
  guard never trips the denylist it serves. Detector and a raw
  tracked-file sweep both read zero.
- **2026-08-06** — **Intent compilation arrives in the kernel
  (0.31.0).** Every wiki page now carries a derived `enola_intent:`
  block — `brain.py intent stamp` maps the frontmatter pages already
  carry onto knowledge nodes, typed relation edges, page-to-code
  anchors, and origin channels, auto-restamped by the pre-commit
  hook and gated by the `intent-page-block` detector and preflight.
  `brain.py enola govern <target>` answers the reverse query —
  *which compiled pages govern this file?* — in both directions,
  and eight skills learn it at their natural moments. The verdict
  half is release-gated on the upstream intent standard
  (enola-labs/enola#197); until the pinned binary crosses it the
  blocks compile forward-compatibly. Instance birth re-stamps its
  filtered wiki, so adopters are born compiled. Read-first:
  [intent compilation](brain/topics/intent-compilation.md).
- **2026-08-04** — **Phase 2: the board takes a bet against its own
  safest option, and bounds the cost instead of arguing with it.**
  [ADR](brain/adrs/attention-board.md) for the
  [attention board](brain/prds/attention-board.md). Pre-flight found the
  fact that reframed the choice: connectors already **queue an inbox item
  per batch**, so the inbox is a uniform channel-agnostic surface over
  heterogeneous systems, and a board reading only the inbox would be
  channel-agnostic for free. The operator took the other bet — read
  `sources/<connector>/` **directly** — because cross-channel joins are
  the capability that makes a board better than a queue, and joins on
  producer summaries are joins on someone else's compression. That
  reintroduces per-channel coupling, which is the one thing this port
  exists to remove, so the ADR bounds it rather than disputes it: a thin
  reader per connector, every reader emitting **one** candidate shape,
  and the inbox as a **universal fallback** so a connector without a
  reader is shallow rather than invisible. Named failure test — if
  readers start growing per-connector *scoring* or *categories*, the
  containment failed and the decision is revisited, not patched.
  Weights land in configuration (a bad weight should be a config error,
  not a silent scoring bug) while the rationale and its dated revisions
  stay prose on a page. **The design is unproven against live data**:
  no connector is configured on this machine, so the reader interface
  will first be exercised against internal producers alone, and the
  first configured connector is the real test of whether one candidate
  shape suffices. An unconfigured shell still gets a board and is told
  how many connectors answered — "nothing found" and "nothing asked"
  must never render alike. Phase 2 — awaiting approval.
- **2026-08-04** — **The kernel collects and it queues; it has never
  triaged.** Phase 1 PRD for an [attention board](brain/prds/attention-board.md)
  — a daily capped, ranked briefing of what deserves the operator's
  day. The gap is precise: six `*-pull` connectors already snapshot
  GitHub, Notion, Slack, Datadog, Langfuse and code shape, and
  `wiki/_state/inbox/` already queues synthesis work for `/tend`. But
  **a queue cannot say which of forty items is worth displacing today's
  plan for** — its honest end state is empty, which makes it a good
  record of what is outstanding and a poor answer to what matters now.
  `/tend`'s own budget grammar (`/tend 3`, `/tend 15m`) is the tell:
  operators already ask for a subset and the tool can only give them
  the first N. The board therefore gets **its own store beside the
  inbox, not inside it** — cards leave by being dismissed, queue items
  leave by being done, and merging the two would trade away the
  no-backlog invariant silently. A sibling brain has run this shape
  daily long enough to learn what breaks, and the lessons that transfer
  are the negative ones (a board that accepts everything becomes a
  second backlog; an unexplained rank is untrustworthy; a channel that
  fails quietly makes the board lie by omission). What does not
  transfer is that brain's channel list, categories and weights — one
  team's remit at one company — so channels and categories come from
  `brain.config.yml`, whose connector registry is already the
  org-agnostic abstraction this needs. Also caught in pre-flight:
  `attention-calibration-operator-surface` is **not** prior art despite
  the name — it is superseded and about verdict grading, a false
  positive for anyone reading the shelf. Appetite medium; owner
  `viktor-daily-operator`. Phase 1 — awaiting approval before the ADR.
- **2026-08-04** — **The sweep was clean; the backlog behind it was
  three weeks deep.** `/sync` found nothing wrong — 182 sources across
  70 pages with none broken, validate ok, and zero findings across all
  fourteen reflection detectors. What it did find is that the scheduled
  ops had been producing output nobody committed: auto-refresh cluster
  scans stop at **2026-07-14 in git** and run to **2026-08-04 on
  disk**, and neither `wiki/_state/schedule.json` nor the inbox item
  set had ever been tracked at all. Twenty overlap scans, the schedule
  state, the inbox set and today's snapshot now land. Tracking the
  inbox items matters past tidiness: committed views are only
  deterministic when the item set is tracked, which is exactly what
  `_inbox_items(tracked_only=True)` assumes — so an untracked inbox
  makes the views gate non-reproducible between machines. The shape of
  this is familiar: an operation that runs, succeeds, writes its output
  and is never landed leaves no red anywhere, which is why it ran for
  three weeks. LOCAL_FIRST — local until promoted.
- **2026-08-04** — **The graph tier reaches parity with its own tool,
  and a check that could not fail is retired.** `baseline`, `check`,
  `coverage`, `explain`, `doctor` and a `history` family
  (`log`/`show`/`diff`/`blame`/`gc`) now run through `brain.py enola`.
  Every one degrades to a named skip — tested on a shell with no binary,
  no cluster and no configured repos, the default state of a fresh
  clone. `doctor` is exempt from the cluster guard on purpose: it asks
  whether *this checkout's* hooks fire, which needs nothing configured,
  and a fresh shell asking exactly that is the case it exists for.
  **`check` reports and never gates** — the graph is the ceiling, never
  the floor, so a gate fed by an optional tier would make every workflow
  conditional on an install the kernel cannot guarantee; its exit 3
  prints *treat as NOT ASKED, never as a pass*, held by two tests, one
  asserting the wrapper's own exit code and one that both phrases
  survive in source. **The defect found while wiring it is the better
  half:** `/sync` ran `enola generate && enola diff`, but `generate`
  re-records the receipts, so the diff compared a baseline against a
  snapshot taken seconds earlier and reported every repo `unchanged`
  **by construction**. Inherited from the parent instance, fixed there
  on 2026-08-03, and here it had never once fired. Order reversed.
  Session hooks are installed, which relaxes *pulled, never pushed* —
  recorded on the ADR rather than smoothed over, because the argument
  that won was that the alternative is a gate nobody remembers to run,
  which is precisely what the `/sync` step had been. 160 tests pass.
  LOCAL_FIRST — local until promoted.
- **2026-08-02** — **The views gate is satisfiable again, and the first
  verdict is on the record.** Three follow-ups. The custom-views design
  call, left open yesterday, is settled the right way round: I had
  assumed those views could be untracked, but the deployed UI links to
  `/_views/custom/engineer/`, `/pm/` and `/operator/`, so they must stay
  committed — which means the *render* has to be deterministic. The
  derived index now takes **tracked inbox items only**, so a committed
  view is a function of the repo rather than of one machine's queue, and
  the CI exemption I added under pressure is **reverted** — the gate is
  uniform again, with no special case. `brain.py inbox` reads the
  directory directly and is untouched, so local tending keeps its full
  queue. Second: the substrate's finding about the kernel's own code was
  **judged** — `tools/brain.py` at 186 top-level symbols against a repo
  median of 11, accepted with the reasoning that a single-file CLI is a
  defensible shape for a tool meant to be copied into a clone, but is
  the honest reason changes to it are hard to review. First real entry
  in either ledger, and `ledger-hygiene` was exercised against it in
  both directions. Third: `symbol-blindness` had shipped **untested
  against its actual purpose** — the kernel is Python-heavy so it never
  fires here; it now has tests on a Go-dominant repo where 93% of
  modules get file-level drift only, which is the shape it was written
  for.
- **2026-08-02** — **The substrates get consumers: 12 of 25 skills now
  consult them.** The port had shipped both substrates and *zero* skills
  using them — recreating in this kernel exactly the gap the sibling
  instance had described as "the explainers ran into a void". An operator
  question caught it: tooling at parity, consumption at zero. `/sync`
  gains an architecture-drift step that reports the finding **count** and
  never the list, because a list in a sweep's output is a backlog by
  another name. `wiki-ingest` gains a substrate-check on its two
  code-shape routing rows — confirmed claims cite the snapshot they were
  checked against, contradicted ones land annotated with a recorded
  verdict, and **no-signal is written as the default rather than the weak
  branch**, since the structure connector sees symbols only for Python
  and the graph tier may not be installed at all. `/shape` consults it in
  the Phase-1 deepdive and for blast radius in Phase 3, `/continue`
  before code leaves local, `/groom` gains three trigger rows, and
  `/ask`, `wiki-query`, `wiki-plan`, `review`, `zoom-out`,
  `wiki-overlap` and `wiki-coverage` each gain the consultation their own
  judgment step was already missing. Every wiring names **both tiers in
  order** — the connector first because it always answers, the graph
  second because it is allowed to be absent. That ordering is the
  kernel-shaped difference from the sibling, where a single binary-backed
  substrate could be assumed present.
- **2026-08-02** — **The structure connector gets findings, a verdict
  ledger, and a line in the contract.** Prompted by a comparison against
  a sibling brain that had adopted an external architecture-graph binary.
  Porting it would have been the obvious move and the wrong one: this
  kernel's connector deliberately chose *no network, no external binary,
  no LLM*, so a binary-backed port would contradict a recorded position
  rather than extend it. What travelled instead were the concepts — and
  three of them the connector already had in its own form (a snapshot
  fingerprint, drift against the previous snapshot, and a reconciler
  where a drift item clears once a page cites the snapshot that raised
  it). Three it lacked, and those landed: a deterministic **findings**
  layer over the existing facts (`oversized-package`, `god-file`,
  `symbol-blindness`), a **verdict ledger** that is write-on-judgment
  with no pending state, and the discipline that a finding is a
  candidate to verify rather than a verdict. First run against the
  kernel's own tree found a true thing — `tools/brain.py` declares **167
  top-level symbols** against a repo median of 10. `symbol-blindness` is
  the explainer that matters most: it reports what share of a repo the
  substrate *cannot* see past file level, because symbol visibility is
  Python-only, and a findings layer that reported only what it could see
  would be the more dangerous artefact. Deliberately **not** built: a
  blast-radius query, which needs a call graph the connector does not
  extract — pretending a symbol inventory could answer *what breaks if I
  change this* would be worse than declining. Also landed:
  `archived-liveness` and `ledger-hygiene` detectors (both red-green
  verified), scheduled-run health in `brain.py status` (a local timer
  failing is *less* visible than a red badge), a citation classifier that
  resolves repo-root and page-relative paths, `uv` support in
  `setup-local.sh` with requirements manifests, and a `/shape` Phase-2
  scope-coverage check. And **AGENTS.md now documents the structure
  substrate at all** — it mentioned it zero times while shipping it, the
  same gap the sibling brain had with its own graph; a consistency test
  now fails if any substrate the kernel ships goes undocumented.
- **2026-07-14** — **Built (0.30.0): specialized agents + a local
  emulation of the whole loop.** Two specialized spoke agents ship
  (`tools/agents/`): a drift-reconciler and an observability-triage
  agent (for emulated Sentry/Datadog/Langfuse), both deterministic —
  they wake, prep, and queue, never invoke an LLM.
  `tools/emulate-agentic.py` runs the entire agentic loop on one machine
  (real hub + spoke agents + producers → wakes → reactions), and
  `agent-key provision` wires any harness in as a spoke. No deployment.
- **2026-07-14** — **Built (0.29.0): the spoke client — hub-and-spoke,
  both halves.** `tools/brain-agent.py` is the missing client half: an
  agent in any harness can `emit` / `pull` / `subscribe` / `listen`
  against a hosted brain, mirroring the server's signing. The server
  gained `POST /api/events` (the agent write endpoint). Work can start
  in the brain, dispatch to an agent in its harness via a wake, run
  there, and land back — without the brain being a harness.
- **2026-07-14** — **Built (0.28.0): owner-subscription wake — the loop
  is closed.** The [event-driven epic](brain/epics/event-driven-agent-triggers.md)
  is complete. Subscribe to a thread/repo/producer and a matching event
  wakes the owner with a signed webhook hint (seq + ref, no payload)
  through an SSRF guard, capped per event, with the cursor as the
  at-least-once backstop. An agent's action now wakes the agents who
  care, end to end.
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
- [Two tiers over the same repos](brain/adrs/structure-findings-and-verdict-ledger.md)
  — an always-available in-kernel connector with findings and a
  verdict ledger, plus an optional binary-backed graph for the
  questions it cannot answer, decided 2026-08-02.
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
- [Attention relevance model](brain/attention-relevance-model.md) — the metric `/attention` ranks by; weights live in `brain.config.yml`, the reasoning lives here
- [Org — methodology + cross-product](org/index.md)
- Per-repo shelves arrive as you add them: `wiki/<repo>/index.md`
