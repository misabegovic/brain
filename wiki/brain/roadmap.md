---
title: "Brain roadmap — 0.x arc toward a self-maintaining, servable brain"
kind: meta
status: living
updated: 2026-07-10
confidence: medium
sources:
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

## 0.2.0 — queue-and-tend (the self-maintenance loop)

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

## 0.3.0 — connectors as snapshot-writers (Slack, Notion, GitHub)

One connector contract: a connector is a pull-only, read-only-scoped
tool that writes **immutable, dedup-keyed snapshots** into
`sources/<connector>/` (idempotent re-sync via source-id addressing —
the existing `<slug>--<shortid>` shape) and never touches `wiki/`.
Slack export (selected channels since cursor), Notion walk upgraded
from staleness-flagging to fetch-changed-and-snapshot, GitHub beyond
issue counts (releases, discussions, PR narratives where useful). A
`*-walk` op flags new batches; the 0.2 ingest loop digests them
through the existing `/in` routing tables.

## 0.4.0 — pruning + deepening (knowledge GC and R&D)

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

## 0.5.0 — the serving plane (access for people outside the product)

**MCP-first.** The stdio MCP grows an HTTP transport behind SSO
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

## 0.6.0 — self-hosting hardening

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

## Standing ideas (unversioned)

From the open-knowledge study (see the captured source): page reads
that return graph context (backlinks, reverse edges, recent log
lines) so every read is a briefing; per-author attribution (operator
vs named agent) in the audit log; write-time broken-link warnings
surfaced to the writing agent, not just CI. Deliberately not adopted:
a vector store (the agentic retrieval loop over live files stays),
and a WYSIWYG editor (the UI is a reading surface; editors are
agents).
