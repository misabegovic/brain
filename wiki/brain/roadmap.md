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

The load-bearing observation: **the governance rail is the
enterprise-safety substrate, and it already exists.** PR-required,
CI gates, the confidence floor, the `ai-suggestions/` separation, and
the `/shape` human gates were designed for unsupervised agent runs.
What "self-maintaining" adds is the *invocation* — moving the agent
itself onto the schedule — not a new safety model. Ordering follows
from that: autonomy first (0.2), more inputs only once the loop can
digest them (0.3), garbage collection before serving (0.4), then the
chat plane (0.5) and the hosting profile that carries it (0.6).

## 0.1.x — where we are

Kernel extracted, standalone, config-driven (`brain.config.yml`).
Deterministic schedule ops run daily via CI and degrade cleanly on an
empty shell; they *observe and flag* but do not synthesise. Ingestion
(`/in`), grooming (`/groom`), shaping (`/shape`), and research
(deepdive) are agent-operated but operator-triggered. Serving is
local-only: stdio MCP (read-only tools) + static Astro UI.
Sibling-diff ingestion is already incremental via `sync-cursor diff`.

## 0.2.0 — scheduled autonomy (the self-maintenance loop)

A second class of schedule op whose handler is a **headless agent
run** rather than a deterministic script. Nightly: mechanical `/sync`,
then per-repo `sync-cursor diff` → `wiki-ingest` → PR. Weekly:
`/groom` in agent mode producing demotion / supersede / archive PRs.
Every run lands as a PR on the governance rail — self-merge on green
for routine synthesis, `ai-suggestions/` for anything
commitment-shaped, human gates untouched. The runner is CI cron or
local cron; `LOCAL_FIRST` stays an operator-session mode, never a
scheduled-run mode.

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
scan emitting a work-list; the weekly agent run executes it as PRs.
Link-graph health joins the detectors (dead ends / orphans / hubs /
suggested links) as a pruning input. Deepening: a research op picks
the pages where **low confidence crosses high centrality** (hub pages
per reverse edges) or coverage gaps, runs deep research (sibling code
+ web), snapshots findings into `sources/research/`, and lands an
ingest PR that earns the confidence bump with citations. The brain
studies its weakest load-bearing knowledge first.

## 0.5.0 — the serving plane (chat for people outside the product)

A grounded, **read-only chat surface** over the corpus. The stdio MCP
grows an HTTP transport; a minimal chat app holds *only* the read
tools, runs against a read-only checkout, and must cite brain pages
in every answer (the zoom-out grounding rule, reused). Enterprise
posture by construction: no write path in the serving process, SSO in
front (identity-aware proxy), an append-only query audit log,
`confidence:` and `updated:` surfaced inline so trust is calibrated,
and `ai-suggestions/` excluded from the serving corpus. Local-first
is unchanged — serving is an optional deployment profile, not the
default mode.

## 0.6.0 — self-hosting hardening

One compose profile: static UI, chat/MCP-HTTP, and a scheduler
container running the 0.2 agent ops, all against the git remote as
the single source of truth (backups are git). Health is
`brain.py status` exposed. Tenancy stays isolation-shaped: one brain,
one deployment, per organisation — no cross-brain sharing.

## Standing ideas (unversioned)

From the open-knowledge study (see the captured source): page reads
that return graph context (backlinks, reverse edges, recent log
lines) so every read is a briefing; per-author attribution (operator
vs named agent) in the audit log; write-time broken-link warnings
surfaced to the writing agent, not just CI. Deliberately not adopted:
a vector store (the agentic retrieval loop over live files stays),
and a WYSIWYG editor (the UI is a reading surface; editors are
agents).
