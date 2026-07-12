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
- [Human-legible presentation layer](adrs/human-legible-presentation-layer.md) — the briefing is a build-time derivation; summaries live in frontmatter; attention verdicts live on inbox items.
- [Persona playthrough loop](adrs/persona-playthrough-loop.md) — playthroughs are executed skills with immutable transcripts; synthetic findings are confidence-capped insights.
- [MCP + CLI surface](adrs/mcp-cli-surface.md) — the embedded terminal retires with the chat pane; the app page is the rendered knowledge under the ambient strip; billing guard degrades to a doctor warning.
- [Workbench PTY bridge](adrs/workbench-pty-bridge.md) — **superseded** 2026-07-12 by mcp-cli-surface: the PTY bridge is removed from the kernel.
- [Chat print-mode bridge](adrs/chat-print-mode-bridge.md) — chat as a per-harness print-mode registry; terminal demoted to a toggle; bare `brain` opens the app.
- [Kernel-manifest instancing](adrs/kernel-manifest-instancing.md) — instances born by explicit manifest: mechanism + kernel trail cross, dogfood never does.
- [Single-image serving profile](adrs/single-image-serving-profile.md) — one infra-agnostic image, env-selected surface; instance isolation via env ports + hashed timer units; Railway as reference, not dependency.

## Pitches (pre-bet) — awaiting a bet

- [Chat-first app](pitches/chat-first-app.md) — **superseded**
  2026-07-10: graduated on the operator's picks (registry / toggle /
  full collapse).

## Topics (discussions in flight)

- [Chat-surface necessity](topics/chat-surface-necessity.md) —
  **settled twice** 2026-07-12: chat pane removed, then the embedded
  terminal; surfaces settle at MCP + CLI.

- [Phoenix-Architecture adoption depth](topics/regenerative-schema-extensions.md)
  — which further Fowler concepts earn schema weight. Open.
- [1.0 criteria](topics/one-point-oh-criteria.md) — the five-point
  gate for instancing elsewhere. **Settled 2026-07-10.**
- [Market-readiness gaps](topics/market-readiness-gaps.md) — what
  stands between this repo and a credible market entrant: license,
  name, releases, public docs, packaging, community files. Open.

## Pitches (pre-bet)

- [Human-legible presentation layer](pitches/human-legible-presentation-layer.md)
  — **superseded** 2026-07-12: bet placed same day; graduated into
  the PRD below.

- [Persona playthrough loop](pitches/persona-playthrough-loop.md) —
  **superseded** 2026-07-12: graduated same-day on the operator's
  bet ("shape it and then build it").

- [Instance birth](pitches/instance-birth.md) — **superseded**
  2026-07-10: graduated in the same directive.

- [Harness workbench](pitches/harness-workbench.md) — **superseded**
  2026-07-10: graduated on the operator's bet.

- [Composable role-fit views](pitches/composable-role-views.md) —
  **superseded** 2026-07-10: graduated on the operator's bet into
  the PRD below.

## PRDs

- [Human-legible presentation layer](prds/human-legible-presentation-layer.md)
  — the UI becomes the partner's briefing: opinionated, Shape
  Up-native, attention-first. Bet 2026-07-12.
- [Persona playthrough loop](prds/persona-playthrough-loop.md) —
  synthetic users walk every release; findings become insights,
  capped below the human-confirmation line. Bet 2026-07-12.
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

Landed 2026-07-12 by a three-persona playthrough sweep (six agent
runs). Each is `ai_suggestion: true`, `confidence: low` — proposals
to review and graduate or discard, **not** decisions. See the
[aggregate view](../_views/ai-suggestions.md).

**Operator surface (Viktor — daily operator):**
- [Acknowledge recurring tend items](ai-suggestions/adrs/acknowledge-recurring-tend-items.md)
  — a re-verified signal producers respect, so operator judgement
  leaves a trace the machine remembers.
- [Producer death as first-class health](ai-suggestions/prds/producer-death-first-class-health.md)
  — distinguish "queue clear because tended" from "clear because the
  producer is dead".
- [Attention-calibration operator surface](ai-suggestions/prds/attention-calibration-operator-surface.md)
  — a pending-grades list + sample-size on the calibration stat.

**Reader surface (Priya — non-terminal PM):**
- [Status-honest generated reading lists](ai-suggestions/prds/status-honest-generated-reading-lists.md)
  — mark the current record when overviews list superseded ADRs;
  resolve raw slugs in trail links.
- [The PM view should read like a brief](ai-suggestions/prds/pm-view-reads-like-a-brief.md)
  — the surface named for the PM opens with maintainer text and raw
  paths.
- [Render-prove the AI-draft trust chrome](ai-suggestions/prds/priya-trust-banner-render-proof.md)
  — fail the UI build when the ai-suggestion banner path goes
  unexercised.

**Security surface (Sam — security reviewer):**
- [Uniform loopback Host-header guard](ai-suggestions/adrs/sam-uniform-loopback-host-guard.md)
  — converge both HTTP surfaces on one anti-rebinding check.

Related insight (Sam):
[ai-suggestions exclusion is MCP-only](../insights/ai-suggestions-exclusion-mcp-only.md)
— the serving-mode draft exclusion is enforced on the MCP surface
but not on `brain.py serve` `/pages/` or the static UI build.
