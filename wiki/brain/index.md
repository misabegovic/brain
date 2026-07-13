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
- [Acknowledge recurring tend items](adrs/acknowledge-recurring-tend-items.md) — an operator ack the producers respect; suppress until the page changes, no metadata falsified. Delivered 2026-07-12.
- [Uniform loopback Host-header guard](adrs/sam-uniform-loopback-host-guard.md) — one anti-DNS-rebinding Host check across both HTTP surfaces. Delivered 2026-07-12.
- [No personal data in public artifacts](adrs/no-personal-data-in-public-artifacts.md) — a commit-msg hook + /pr check strip session URLs regardless of harness behaviour. 2026-07-12.
- [Multi-PRD epic shape](adrs/multi-prd-epic-shape.md) — umbrella epics over multi-PRD work.
- [Shape deepdive pre-flight](adrs/shape-deepdive-pre-flight.md) — fetch real context before drafting a PRD.
- [Parallel execution agent teams](adrs/parallel-execution-agent-teams.md) — parent / owner / helper fan-out levels.
- [Parallel efforts on request](adrs/parallel-efforts-on-request.md) — `/spawn` worktree-based parallel efforts.
- [Zoom-out on current work](adrs/zoom-out-on-current-work.md) — per-work-item big-picture briefs.
- [Home content shape](adrs/home-content-shape.md) — the home dashboard's contract sections.
- [Successor SSG for UI](adrs/successor-ssg-for-ui.md) — Astro + Starlight + Pagefind substrate.
- [UI auto-refresh hook](adrs/ui-auto-refresh-hook.md) — smoke-build the UI on wiki edits.
- [Operator lesson pattern](adrs/operator-lesson-pattern.md) — durable operator lessons shelf.
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
- [Status-honest generated reading lists](prds/status-honest-generated-reading-lists.md) — generated lists mark status; cross-refs render titles. Delivered 2026-07-12.
- [Role views read like briefs](prds/pm-view-reads-like-a-brief.md) — purpose-first, title links, human empty states. Delivered 2026-07-12.
- [Render-prove the AI-draft trust banner](prds/priya-trust-banner-render-proof.md) — the build fails if a draft page loses its banner. Delivered 2026-07-12.
- [Producer death as first-class health](prds/producer-death-first-class-health.md) — a heartbeat distinguishes a dead loop from a tended-clean queue. Delivered 2026-07-12.
- [Attention-calibration operator surface](prds/attention-calibration-operator-surface.md) — pending-grades list + sample-sized stat. Delivered 2026-07-12.
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

- [A conversation surface over the inbox](ai-suggestions/prds/conversation-surface-over-inbox.md)
  — Slack-shaped async channels (topics as channels, inbox as
  messages, replies during tend); explicitly *not* the removed chat
  pane. Operator-requested 2026-07-13, awaiting review.

*(the 2026-07-12 playthrough sweep's eight suggestions
were all reviewed, delivered, and graduated to the ADR/PRD shelves
below; see the trail.)*

- [ai-suggestions exclusion was MCP-only](../insights/ai-suggestions-exclusion-mcp-only.md)
  — Sam's serving-mode insight, **acted on** 2026-07-12 (superseded by
  the uniform-host-guard ADR + the exclusion fix in PR #8).
