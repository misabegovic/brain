---
title: "Brain roadmap — 0.x arc toward a self-maintaining, servable brain"
kind: meta
status: living
updated: 2026-07-10
confidence: high
sources:
  - ../../sources/research/2026-07-10--tend-sweep-2-verification.md
  - ../../sources/conversations/2026-07-10--self-hosting-roadmap-intent.md
  - ../../AGENTS.md
  - ../../brain-schedule.yml
---

# Brain roadmap — the 0.x arc

Operator intent (captured 2026-07-10): the brain self-maintains —
ingests diffs, pulls from Slack / Notion / GitHub, prunes and deepens
its own knowledge — and eventually offers safe, read-only chat access
to people outside the product, while staying local-first for the
operator's own work. Nothing urgent; this page holds the ordering.

Two load-bearing observations. First, **the governance rail is the
enterprise-safety substrate, and it already exists** — PR-required,
CI gates, the confidence floor, the `ai-suggestions/` separation, and
the `/shape` human gates were designed for unsupervised agent runs.
Second (operator constraint, 2026-07-10): **no scheduled LLM
invocation** — the operator works through interactive terminal
sessions only, and headless per-run billing is out. The consequence
is the *queue-and-tend* split: everything deterministic (observation,
collection, connector pulls, health scans) runs on a schedule for
free; everything that needs a model (synthesis, grooming judgement,
research) queues into a persistent inbox and is digested inside the
operator's normal sessions. Ordering: accumulation loop first (0.2),
more inputs once the loop digests them (0.3), garbage collection
before serving (0.4), then the serving plane (0.5) and the hosting
profile that carries it (0.6).

## 0.1.x — where we are

Kernel extracted, standalone, config-driven (`brain.config.yml`).
Deterministic schedule ops run daily via CI and degrade cleanly on an
empty shell; they *observe and flag* but do not synthesise. Ingestion
(`/in`), grooming (`/groom`), shaping (`/shape`), and research
(deepdive) are agent-operated but operator-triggered. Serving is
local-only: stdio MCP (read-only tools) + static Astro UI.
Sibling-diff ingestion is already incremental via `sync-cursor diff`.

## 0.2.0 — queue-and-tend (the self-maintenance loop) — **shipped 2026-07-10**

Decision recorded at [adrs/queue-and-tend-inbox.md](adrs/queue-and-tend-inbox.md);
built the same day (`brain.py inbox`, the `inbox-refresh` op, the
`/tend` skill, session-start surfacing, `tools/install-timer.sh`, a
producer template). Remaining operator step: run
`python3 tools/brain.py setup` once (it installs the timer among
everything else). The hands-off surface shipped the same day:
`setup` / `doctor` / the `/dash` ops page / `brain tend`.

No scheduled LLM runs. A **local timer** (cron / systemd — local
because the sibling repos only exist on the operator's machine) runs
the deterministic ops and accumulates pending synthesis work into a
persistent inbox: per-repo cursor-diff summaries, new connector
batches, half-life crossings, link-health findings, coverage gaps.
**The inbox is an open contract, not a closed pipeline**: one JSON
file per item at `wiki/_state/inbox/<id>.json` (merge-safe per the
efforts-registry precedent; committed, so arrival and clearing are
git-audited), written via `brain.py inbox add` with a
producer-chosen dedup id so re-runs are idempotent. Operator-defined
producers are first-class — any script that calls `inbox add`,
registered as one more `brain-schedule.yml` entry (the `handler:`
field is already arbitrary shell). A session-start hook surfaces one
line (`brain inbox: N pending`); a **`/tend` skill** digests the queue
inside the operator's normal interactive session — priority-ordered,
budget-bounded, landing `LOCAL_FIRST` commits and clearing items.
Latency is "next time the operator sits down", which matches the
nothing-urgent posture, and every synthesis run is implicitly
supervised because it happens in a visible session. The PR rail
remains the mode for multi-agent deployments; tend-mode and PR-mode
are the same skills under different governance toggles.

## 0.3.0 — connectors as snapshot-writers (Slack, Notion, GitHub) — **shipped 2026-07-10**

Decision recorded at
[adrs/connector-snapshot-contract.md](adrs/connector-snapshot-contract.md);
three built-ins ship in the kernel and no-op until configured
(`connectors:` in `brain.config.yml` + read-only tokens in `.env`).
Verified end-to-end against a public GitHub repository. Remaining
operator steps: add watch-lists and tokens when a project wants them.

One connector contract: a connector is a pull-only, read-only-scoped
tool that writes **immutable, dedup-keyed snapshots** into
`sources/<connector>/` (idempotent re-sync via source-id addressing —
the existing `<slug>--<shortid>` shape) and never touches `wiki/`.
Slack export (selected channels since cursor), Notion walk upgraded
from staleness-flagging to fetch-changed-and-snapshot, GitHub beyond
issue counts (releases, discussions, PR narratives where useful). A
`*-walk` op flags new batches; the 0.2 ingest loop digests them
through the existing `/in` routing tables.

## 0.4.0 — pruning + deepening (knowledge GC and R&D) — **shipped 2026-07-10**

Shipped as producers + a health view: `brain.py links` (orphans /
hubs / dead-ends / suggested links) and four new `inbox-refresh`
producers — per-kind half-life crossings (the groom table encoded),
an orphans item, the research picker (low confidence × ≥2 inbound
links, top 3), and per-repo coverage gaps. The picker queued its
first three real items the moment it ran.

Grooming gets teeth: the half-life table becomes a deterministic
scan emitting inbox items; `/tend` executes demotions / supersedes /
archives when the operator digests. Link-graph health joins the
detectors (dead ends / orphans / hubs / suggested links) as a pruning
input. Deepening: a deterministic picker queues the pages where
**low confidence crosses high centrality** (hub pages per reverse
edges) or coverage gaps as research items; the research itself runs
in-session via `/tend` (deep research over sibling code + web),
snapshots findings into `sources/research/`, and lands the commit
that earns the confidence bump with citations. The brain studies its
weakest load-bearing knowledge first.

## 0.5.0 — composable role-fit views — **shipped 2026-07-10**

Bet, shaped, and built the same day: pitch → deepdive (five research
notes) → [PRD](prds/composable-role-views.md) →
[ADR](adrs/sql-views-over-derived-index.md) → build. A disposable
SQLite index rides every views regeneration; view specs in `views/`
are SQL (plus shorthands that compile to SQL) rendering to
`wiki/_views/custom/`; `brain.py query` gives read-only ad-hoc SQL;
Datadog (monitors + SLOs) and Langfuse (prompt inventory) joined the
connector fleet with state extracts for view tiles. Example specs:
engineer / pm / operator. The serving and hosting slices below shift
to 0.6 / 0.7.

## 0.6.0 — the serving plane — **software shipped 2026-07-10; deployment pending**

The software half landed: the MCP server's streamable-HTTP
transport (localhost-bound, origin-checked), serving mode
(`BRAIN_SERVING=1`: ai-suggestions excluded from the corpus, every
tool call appended to the query audit log), and the Datasette pilot
(`tools/serve-datasette.sh`, immutable mode, canned queries) over
the derived index. What remains is deployment — where it runs and
which identity-aware proxy fronts it — which is operator
infrastructure, chosen per adoption.

### Original slice definition

**MCP-first**, now plus the Datasette pilot over the derived index
(researched: immutable mode behind an IAP is its canonical
deployment; stable 0.65.x). The stdio MCP grows an HTTP transport behind SSO
(identity-aware proxy); people outside the product connect *their
own* MCP-aware client (Claude, Cursor, ChatGPT connectors) to the
brain's read-only tools — the operator pays hosting, consumers pay
their own inference. Enterprise posture by construction: no write
path exists in the serving process, it runs against a read-only
checkout, an append-only query audit log records access,
`confidence:` and `updated:` ride along in tool results so trust is
calibrated, and `ai-suggestions/` is excluded from the serving
corpus. A minimal grounded chat app (answers must cite brain pages —
the zoom-out grounding rule, reused) is optional sugar for consumers
with no agent of their own, added only if demand shows up, with
per-query cost capped by construction. Local-first is unchanged —
serving is an optional deployment profile, not the default mode.

## 0.6.x — harness workbench — **shipped 2026-07-10**

Bet, shaped, and built the same day (pitch →
[PRD](prds/harness-workbench.md) →
[ADR](adrs/workbench-pty-bridge.md) → build): `brain workbench`
serves an embedded terminal (own login shell, xterm.js over a
loopback stdlib PTY bridge, token + Host check) beside the rendered
brain with change-driven reload; one-click harness launches
(claude / codex / cursor-agent / opencode) from a data registry;
`install-agent` wires each harness's MCP config from a fan-out
table — the agent-independence adapters delivered. Structurally
excluded from serving deployments.

## 0.7.0 — self-hosting hardening — **shipped 2026-07-10**

Decision at
[adrs/single-image-serving-profile.md](adrs/single-image-serving-profile.md):
one infra-agnostic image (two-stage build; UI + MCP-serving +
Datasette; `BRAIN_SURFACE` picks which binds the platform's `$PORT`),
Railway as the reference target via root `railway.toml` — but the
entrypoint runs unchanged on any host. Instance isolation shipped
with it: `BRAIN_PORT`/`BRAIN_MCP_PORT` envs and per-path-hashed
timer unit names, so multiple brains coexist on one machine.
Verified by local emulation: all three container surfaces up on
non-default ports while the client brain's server ran on its
default port simultaneously, working tree untouched.

### Original slice definition

One compose profile: static UI and MCP-HTTP against the git remote
as the single source of truth (backups are git); the deterministic
accumulation loop stays on the operator's machine where the sibling
repos live. Health is `brain.py status` exposed. Tenancy stays
isolation-shaped: one brain, one deployment, per organisation — no
cross-brain sharing.

## Cross-cutting — agent-independence

The brain's agent contract is deliberately harness-neutral: *read
`AGENTS.md`, follow the skill protocols, call `brain.py`, edit
files* — anything that can do that is a valid agent, and with no
agent at all the brain degrades to a validated markdown wiki.
Already independent: the validator/CLI, CI gates, the pre-commit
hook, the UI, the MCP server (an open standard — any MCP-aware
client queries the brain today), and the corpus itself (plain
markdown + git, directly compatible with open-knowledge-style
editors). The three genuinely Claude-Code-specific pieces and their
neutral counterparts: harness hooks are ergonomics only (the
load-bearing gates stay in pre-commit + CI, never only in a
harness); permission deny-lists are backstopped by **credential
scoping** (connectors carry read-only tokens, so no harness can
write regardless of its permission model); and the `.claude/`
layout gets thin generated adapters per harness via a future
`brain.py install-agent <harness>` (mirroring `install-sibling`),
pointing at canonical protocol files rather than maintaining copies
that drift.

## 0.8.0 — work happens inside the brain — **shipped 2026-07-10**

Operator directive: the brain is a standalone project and its own
daily surface. The local server now serves the **rendered wiki** at
`/ui` (from the ui-build hook's sandbox, so it is the freshest
build), the workbench's left pane navigates dashboard ↔ wiki ↔
custom views, and the change signal kicks a single-flight UI rebuild
whenever the rendered site is staler than the corpus — edits from
any editor appear rendered within one poll cycle plus a build. The
Starlight sidebar reflects the brain's real shelves (custom views,
brain state/roadmap/ADRs/PRDs/pitches, org). Project hygiene:
`VERSION` (bumped per shipped slice) + `brain.py --version`; the
operating principle is recorded as the first operator lesson
(develop-the-brain-inside-the-brain).

## 0.9.0 — every read is a briefing — **shipped 2026-07-10**

The open-knowledge study's standing ideas, implemented, plus the
stress-test findings from working the brain through its own UI.
`brain.py page <path>` (and the MCP get_page tool) return the page
*with* its graph context — backlinks, outbound links, computed
reverse edges, recent audit-log activity. `brain.py lint-page` gives
write-time feedback: a PostToolUse hook prints frontmatter and
broken-link warnings into the writing agent's transcript the moment
a wiki page is saved (CI stays the gate). The audit log gains
per-author attribution (`by:` line — operator vs named agent). And
the stress test's structural fix: the rendered wiki serves at the
local server's **root** (the Astro build links absolutely; a prefix
mount broke styling and navigation), with `/api` hosting the old
endpoint listing and `/ui` redirecting. Verified end-to-end in a
real browser: styled wiki beside a live terminal, in-iframe
navigation, commands executed in the workbench terminal.

## 0.10.0 — topics + the regenerative schema — **shipped 2026-07-10**

Two operator-directed evolutions. **Topics** (`kind: topic`,
`wiki/<scope>/topics/`): a running discussion thread on one question
— dated, attributed entries; an Outcome that either records a small
resolution or links the ADR/PRD it graduates into. The lightweight
decision-and-discussion tracker below the ADR ceremony threshold,
and the brain's provenance log in Fowler's sense (the rationale is
the unit of change). **The regenerative schema**: Chad Fowler's
Phoenix Architecture ingested (snapshot + synthesis at
`org/methodology/regenerative-software.md`) and folded into the
permanent layer — `constraints.md` (the architectural-primitives
registry: what cannot be deleted or violated) and
`implementation-memory.md` (the runtime's undocumented lessons,
catalogued with causes) join the structure-emergent set, with
routing rows in `/in` and `/capture`. First topic opened on adoption
depth for the remaining Fowler concepts.

## 0.11.0 — instance birth — **shipped 2026-07-10**

The delivery mechanism for the operator's standing constraint (this
repo is the tool's own project; adoption = separate instances).
`init --full` births a working instance from an explicit kernel
manifest ([ADR](adrs/kernel-manifest-instancing.md)): mechanism and
the kernel's documentation trail cross; dogfood never does;
citations that stayed behind are filtered with a schema fallback;
the born instance passes its own gates before the command returns.
Executable as a suite test — which is 1.0 criterion #1.

## The 1.0 gate

Settled at [topics/one-point-oh-criteria.md](topics/one-point-oh-criteria.md):
(1) birth works — in the suite; (2) seven unattended timer days;
(3) one full connector→tend loop on real data in an instance;
(4) cold-start onboarding by a non-operator; (5) all-green at tag
time. Criteria 2–4 need calendar time and a real adoption.

## 0.12.0 — chat-first app — **shipped 2026-07-10**

The operator's simplification bet, delivered on their three picks
([ADR](adrs/chat-print-mode-bridge.md)): the conversation is the
interface (per-harness print-mode chat rows beside the launch
registry — subscription-billed, project-config-honouring; verified
live with a real turn answering from `brain.py stats`), the
terminal demoted to an advanced toggle (PTY connects lazily), an
ambient attention strip replacing tables (health + queue + reload
signal in one poll), and the surface collapsed: bare `brain` opens
the app; the README leads with the conversation. Named follow-ups:
streaming replies, transcript capture. **0.12.1** (same day): persona
playthroughs through the real UI — a newcomer, an operator, a PM —
drove three upgrades: composer autofocus (the first playthrough lost
its first message to a focus miss), markdown-lite rendering in agent
bubbles (escape-then-markup), and one-click suggestion chips (the
chat-led onboarding follow-up, delivered early). The playthrough's
best moment: the chat's own agent flagged the uncommitted upgrade
diff in its "what changed?" answer — the mechanism reviewing its
author in real time.

## 0.13.0 — the chat builds — **shipped 2026-07-10**

The chat interface graduated from answering to authoring: the claude
chat row gained edit permission (acceptEdits — operator-initiated
turns in the operator's own repo; bash stays allowlist-gated), and
the first two product artifacts were built *through the chat* by the
brain's own nested agent: the competitive-positioning page
(category, positioning table vs open-knowledge / Codeplain / plain
wikis, defensible differentiators) and the market-readiness-gaps
topic — six gaps verified against the repo (license, name,
releases, packaging, public docs, community files), each queued as
an inbox item. The license and name are operator decisions,
deliberately left open on the topic.

## 0.14.0 — surfaces simplified: MCP + CLI + terminal — **shipped 2026-07-12**

The operator's reconsideration, two days of evidence, and the
deletion test agreed: the first-party chat pane duplicated richer
existing surfaces (an interactive harness in the terminal, MCP-aware
chat clients via `install-agent`, the CLI) at higher per-turn cost.
Removed via a superseding ADR
([mcp-cli-terminal-surface](adrs/mcp-cli-terminal-surface.md));
kept: the knowledge-first layout, the ambient strip, bare-`brain`
entry, `install-agent`, and the billing guard (now governing every
harness subprocess). A recorded reversal within days is the
mechanism working — cheap corrections are what the trail is for.

## 0.15.0 — surfaces settle at MCP + CLI — **shipped 2026-07-12**

The same deletion test, one step further, on the operator's
question: the embedded terminal was an arrangement of windows, not
a capability — the operator's own terminal beside a browser tab
reproduces it, and the PTY-over-websocket bridge was the kernel's
largest security/maintenance surface relative to value. Removed via
a superseding ADR ([mcp-cli-surface](adrs/mcp-cli-surface.md)); the
app page becomes the rendered knowledge under the ambient strip
(auto-reload kept), and the billing guard degrades honestly to a
`doctor` warning. Every remaining first-party surface now survives
the deletion test.

## 0.16.0 — persona playthrough loop — **shipped 2026-07-12**

Shaped and built on the operator's same-day bet
([pitch](pitches/persona-playthrough-loop.md) →
[PRD](prds/persona-playthrough-loop.md) →
[ADR](adrs/persona-playthrough-loop.md)): four user personas for
the brain-as-product, the `/playthrough` skill (real execution,
immutable transcripts, insights capped at `confidence: low` until
a human confirms), and a version-cursor producer queueing one
sweep per shipped release. The first dogfood walk paid for the
mechanism immediately — two cold-start defects fixed in-session,
one hypothesis routed to the insights shelf.

## Standing ideas (unversioned)

Deliberately not adopted from the open-knowledge direction: a vector
store (the agentic retrieval loop over live files stays), and a
WYSIWYG editor (the UI is a reading surface; editors are agents).
