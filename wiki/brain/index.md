---
title: "Brain (meta level)"
kind: meta
status: living
updated: 2026-07-10
confidence: high
sources:
  - ../../AGENTS.md
---

# Brain — meta level

This shelf tracks how the brain itself operates: schema, conventions,
tooling, governance.

- [State](state.md) — past / now / perceived / target for the brain itself.
- [Roadmap](roadmap.md) — the 0.x arc toward a self-maintaining, servable brain.
- [Authoring ADRs and PRDs](authoring-adrs-and-prds.md) — the writing
  discipline behind `/shape` artefacts.

## ADRs

Kernel decisions ported from the origin deployment on 2026-07-10,
sanitized to organisation-agnostic form:

- [Shape Up pitches](adrs/shape-up-pitches.md) — pre-bet pitch pages as a first-class kind.
- [Multi-PRD epic shape](adrs/multi-prd-epic-shape.md) — umbrella epics over multi-PRD work.
- [Shape deepdive pre-flight](adrs/shape-deepdive-pre-flight.md) — fetch real context before drafting a PRD.
- [Parallel execution agent teams](adrs/parallel-execution-agent-teams.md) — parent / owner / helper fan-out levels.
- [Parallel efforts on request](adrs/parallel-efforts-on-request.md) — `/spawn` worktree-based parallel efforts.
- [Zoom-out on current work](adrs/zoom-out-on-current-work.md) — per-work-item big-picture briefs.
- [Home content shape](adrs/home-content-shape.md) — the home dashboard's contract sections.
- [Successor SSG for UI](adrs/successor-ssg-for-ui.md) — Astro + Starlight + Pagefind substrate.
- [UI auto-refresh hook](adrs/ui-auto-refresh-hook.md) — smoke-build the UI on wiki edits.
- [Operator lesson pattern](adrs/operator-lesson-pattern.md) — durable operator lessons shelf.
- [Competitor intel ingestion](adrs/competitor-intel-ingestion.md) — public competitor info routing.
- [Queue-and-tend inbox](adrs/queue-and-tend-inbox.md) — deterministic producers accumulate; `/tend` digests in-session; no scheduled LLM runs.
- [Connector snapshot contract](adrs/connector-snapshot-contract.md) — connectors are pull-only snapshot-writers: immutable dedup files, cursors, inbox items out, never a wiki write.
- [SQL views over a derived index](adrs/sql-views-over-derived-index.md) — view specs are SQL over a disposable SQLite index; shorthands compile to SQL; the index rides the views pipeline.
- [Workbench PTY bridge](adrs/workbench-pty-bridge.md) — loopback browser page over a stdlib PTY bridge; harness launches + config adapters as data tables; never in serving mode.
- [Chat print-mode bridge](adrs/chat-print-mode-bridge.md) — chat as a per-harness print-mode registry; terminal demoted to a toggle; bare `brain` opens the app.
- [Kernel-manifest instancing](adrs/kernel-manifest-instancing.md) — instances born by explicit manifest: mechanism + kernel trail cross, dogfood never does.
- [Single-image serving profile](adrs/single-image-serving-profile.md) — one infra-agnostic image, env-selected surface; instance isolation via env ports + hashed timer units; Railway as reference, not dependency.

## Pitches (pre-bet) — awaiting a bet

- [Chat-first app](pitches/chat-first-app.md) — **superseded**
  2026-07-10: graduated on the operator's picks (registry / toggle /
  full collapse).

## Topics (discussions in flight)

- [Chat-surface necessity](topics/chat-surface-necessity.md) — drop
  the chat pane for MCP + CLI + terminal? Open, operator's call.

- [Phoenix-Architecture adoption depth](topics/regenerative-schema-extensions.md)
  — which further Fowler concepts earn schema weight. Open.
- [1.0 criteria](topics/one-point-oh-criteria.md) — the five-point
  gate for instancing elsewhere. **Settled 2026-07-10.**
- [Market-readiness gaps](topics/market-readiness-gaps.md) — what
  stands between this repo and a credible market entrant: license,
  name, releases, public docs, packaging, community files. Open.

## Pitches (pre-bet)

- [Instance birth](pitches/instance-birth.md) — **superseded**
  2026-07-10: graduated in the same directive.

- [Harness workbench](pitches/harness-workbench.md) — **superseded**
  2026-07-10: graduated on the operator's bet.

- [Composable role-fit views](pitches/composable-role-views.md) —
  **superseded** 2026-07-10: graduated on the operator's bet into
  the PRD below.

## PRDs

- [Chat-first app](prds/chat-first-app.md) — conversation as the
  interface; ambient status; bare `brain` opens the app. Bet
  2026-07-10.
- [Instance birth](prds/instance-birth.md) — `init --full` births a
  working instance from the kernel manifest. Bet 2026-07-10.
- [Composable role-fit views](prds/composable-role-views.md) — SQL
  view specs over a derived index, with Datadog / Langfuse
  connectors. Bet 2026-07-10.
- [Harness workbench](prds/harness-workbench.md) — the local surface
  runs your harness terminal beside the rendered results. Bet
  2026-07-10.

## AI suggestions (drafts for human review)

*(none yet)*
