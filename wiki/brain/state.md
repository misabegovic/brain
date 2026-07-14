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

- **The spoke client lands — hub-and-spoke, both halves (0.29.0,
  2026-07-14).** On the operator's hub-and-spoke direction (the brain is
  the coordination + memory hub; the harness stays the execution spoke),
  `tools/brain-agent.py` is the missing client half of the event tier: a
  stdlib-only client an agent in *any* harness runs to `emit` signed
  events, `pull` verified events from its cursor, `subscribe` to what it
  cares about, and `listen` for wakes (verify → pull → hand off, with an
  `--on-wake` command hook). It mirrors the server's signing and talks
  HTTP to a `BRAIN_HOSTED` brain (config via `BRAIN_URL` /
  `BRAIN_AGENT_ID` / `BRAIN_AGENT_SECRET`). The server gained the
  matching agent write endpoint (`POST /api/events`, authenticated, any
  event kind) alongside the UI's `/api/act`. Work can now start in the
  brain (an event), dispatch to an agent in its harness (a wake), run
  there, and land back in the brain (a signed event) — without the brain
  being a harness. Next: deploy the hub, then one specialized agent
  (a drift-reconciler) as proof.

- **The event-driven loop is closed — owner-subscription wake ships
  (0.28.0, 2026-07-14).** The [event-driven epic](epics/event-driven-agent-triggers.md)
  is complete. An agent subscribes to a thread, repo, or producer
  (`subscribe --agent --pattern --wake-url`, a signed subscribe event on
  the child-1 stream); when a matching event lands, the hosted tier
  wakes the owner with a **webhook hint** — the event's seq + ref,
  signed with the subscriber's own key, never a payload — fired off the
  request path in a daemon thread. An **SSRF guard** vets every
  agent-supplied URL (rejects loopback/private/link-local/reserved and
  non-http(s); refused the cloud-metadata endpoint in tests;
  `BRAIN_WAKE_ALLOW_LOOPBACK=1` relaxes only loopback for same-host
  dev). Delivery is at-least-once and best-effort — a failed webhook is
  logged and dropped, and the per-agent cursor catches the agent up on
  its next read. Fan-out capped at 32/event; the wake never invokes the
  agent; local-first has no subscriptions and fires nothing. An agent's
  action now wakes the agents who care, end to end.

- **Per-agent identity + a signed event stream ship (0.27.0,
  2026-07-14).** The first build of the [event-driven epic](epics/event-driven-agent-triggers.md)
  — the agentic-future backbone. A hosted brain (`BRAIN_HOSTED=1`) now
  authenticates agents: per-agent HMAC keys (`agent-key
  issue|rotate|revoke`), and a signed, append-only event stream under
  `wiki/_state/events` that agents read per-agent cursors over
  (`events emit|since|verify`). The auth boundary does both halves —
  `event_append` rejects a forged or unsigned append at write time, and
  reads drop any tampered or revoked-agent line. On the hosted tier a
  `/api/act` write is a signed event authored by the authenticated
  agent, and `GET /api/events?since=<seq>` is the authenticated read.
  Local-first is byte-for-byte unchanged: no keyring, no stream, no
  daemon, posts stay machine-authored. Secrets + the stream are
  git-ignored runtime state; the audit trail stays the inbox +
  `log/log.md`. Only the owner-subscription wake (epic child 2) remains
  before the loop closes end to end.

- **The graph and connector reflect as page-level trust signals
  (0.26.0, 2026-07-14).** The edge-provenance graph and the structure
  connector were agent/maintainer plumbing with no user-facing payoff —
  a `/graph/` page and MCP tags, nothing on the pages people read. Now
  every page carries the signal where it's read: a "N pages rely on
  this" chip (authored-inbound centrality, linking to `/graph/`) and,
  on a page flagged AMBIGUOUS (low-confidence yet load-bearing), an
  "⚑ Uncertain but load-bearing — verify before building on this"
  banner (suppressed on superseded/archived trail). A repo shelf page
  surfaces structure-connector **drift** inline once a repo is
  configured — dormant on this instance (no active sibling repos), but
  wired. Third and last of the three review improvements.

- **Topics lead with an executive brief, not a wall of text (0.25.0,
  2026-07-14).** A human arriving to weigh in on a topic used to face
  the full discussion before reaching the compose box. A topic page now
  opens with its summary (the TL;DR), a "what's being decided" callout
  (the Question), and the Respond control right there — the full
  discussion collapses behind one "Read the full discussion" toggle. A
  companion fix: the compose form is properly hidden until you open it
  (a CSS rule had been overriding the hidden state, so every collab
  control rendered its box open). Second of the three review
  improvements.

- **Collaboration is one control everywhere (0.24.0, 2026-07-14).**
  The operator's ways of contributing — comment, queue, post to a
  thread — were split across cards, pages, and channels, and none of
  them could be undone or edited. They are now a single `Collaborate`
  control used on every card, page, and topic thread, backed only by
  the inbox, with full CRUD: comment / queue / post **plus edit and
  unqueue (remove)** of your own pending items, while they are still
  pending (a tend session clearing them is what makes them final).
  `/api/act` gained `edit` and `remove` actions (ui-action items only,
  guarded) and a `/api/pending` read lists your contributions for a
  page or thread. The old split `Actions` component and the bespoke
  thread compose box are gone.

- **An async conversation surface ships over the inbox (0.23.0,
  2026-07-14).** Channels ARE topics: a `/channels/` surface lists
  every topic as a channel, and each topic page grows a Thread panel
  with a compose box. A post is an **inbox write** — never a direct
  topic write, so the inbox-only-write invariant holds — and the agent
  replies *in the thread* on the next tend (a dated topic entry), then
  the item clears. It is async by construction: no live chat, no
  scheduled LLM. The RFC's craft objections are answered as code, not
  prose: attribution is **server-stamped** from a machine identity (a
  browser page cannot forge who posted), post text is **fenced as
  untrusted data** before it reaches the write-capable tending agent
  (with role-label injection lines flagged), the write endpoint never
  mounts in serving mode, and "unread since last visit" lives in the
  browser, not the git tree. Third of the three ingest-driven builds —
  the surface the RFC had marked no-go, built to the standard the RFC
  set. Ships behind the local server (`brain serve`); the static/
  serving build shows channels read-only and withholds pending posts.

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
