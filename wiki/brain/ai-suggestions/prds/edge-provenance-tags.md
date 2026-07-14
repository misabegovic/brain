---
title: "Give the brain's link graph per-edge provenance tags — push uncertainty from the page down to the relationship"
kind: initiative
status: suggested
ai_suggestion: true
updated: 2026-07-14
team: "(inferred)"
division: "(inferred)"
repos:
  - brain
appetite: small
confidence: low
summary: >
  The brain's confidence lives per page; its graph edges (depends_on,
  affects, authored links, suggested links) carry none. Borrow
  Graphify's EXTRACTED / INFERRED / AMBIGUOUS edge-provenance tags —
  deterministically, no LLM — and render them on the existing
  build-time /graph/ SVG. A small bundled second item: emit the page
  graph as GraphML/Cypher for external analysis.
sources:
  - ../../../../sources/research/2026-07-14--graphify-llm-knowledge-graph.md
  - ../../adrs/human-legible-presentation-layer.md
  - ../../adrs/sql-views-over-derived-index.md
  - ../../adrs/queue-and-tend-inbox.md
---

# Give the brain's link graph per-edge provenance tags — push uncertainty from the page down to the relationship

> **AI-suggested PRD.** Does **not** reflect a human-approved
> initiative and does **not** record committed work or upcoming
> product changes. Agent-authored synthesis from a directed research
> deepdive — a *suggestion* to review, iterate on, and either
> graduate or supersede. Treat the shape and metrics as the agent's
> hypothesis, not the team's commitment.

## Why the agent suggests this

The operator asked how the brain could benefit from Graphify
(`Graphify-Labs/graphify`), a code-graph tool with an optional LLM
semantic layer. Four research agents deepdived and validated it
against the brain's own ADRs (research note in `sources/`).

The honest conclusion: Graphify is a **near-peer**, and most of its
value the brain already has — the token-efficiency thesis, hubs
(= god nodes), the SHA-incremental cache (= sync-cursors), the
deterministic-triggers/deliberate-LLM split (= queue-and-tend). One
idea is genuinely new and does not conflict with anything: Graphify
tags every graph *edge* with how it was obtained — `EXTRACTED`
(explicit in source), `INFERRED` (a deduction), `AMBIGUOUS`
(uncertain, flagged for review) — and renders that confidence
visually.

The brain's uncertainty discipline (confidence tiers, "mark
uncertainty explicitly," `sources:` citations) is strong, but it
lives **per page**. The brain's *edges* — `depends_on`/`consumed_by`,
`affects`/`affected_by`, authored markdown links, and `brain.py
links` suggested links — carry no confidence at all. A reader (human
or agent) can't tell a hand-authored, load-bearing link from a
machine-suggested guess. Graphify shows the fix.

## Inferred objective

If every edge in the brain's link graph carried a provenance tag, an
agent reasoning over the graph — and a human reading `/graph/` —
could tell an authored relationship from a suggested or uncertain
one at a glance, extending the brain's page-level uncertainty
discipline to the relationship level where it currently has none.

## Affected personas (agent-inferred)

- [Priya — non-terminal PM](../../../../.claude/personas/users/priya-non-terminal-pm.md)
  — reads the graph to trace how decisions connect; a suggested link
  rendered identically to an authored one is the same
  draft-mistaken-for-fact trap the AI-draft banner already guards
  against. The reviewer should confirm the tag is legible, not noise.

## Now / Perceived / Target (agent's read)

- **Now** — `pages.json` computes edges (`depends_on`/`consumed_by`,
  `affects`/`affected_by`), `brain.py links` computes hubs, orphans,
  and *suggested* links, and `/graph/` renders them all as identical
  build-time SVG lines. Nothing marks which edges are authored vs
  inferred.
- **Perceived** — the brain records that its confidence discipline is
  strong; the gap is that it stops at the page boundary and never
  reaches the edges.
- **Target** *(hypothesis)* — every edge carries a deterministic
  provenance tag; `/graph/` renders it (solid vs dashed vs faint, the
  way Graphify does); MCP graph reads expose it so agents weight
  edges by trust.

## Scope (suggested)

- **A deterministic tag on every edge — no LLM.** Map the brain's
  existing edge sources to the three tiers:
  - `EXTRACTED` — hand-authored: frontmatter `depends_on`/`affects`
    and markdown links a human wrote.
  - `INFERRED` — machine-suggested: `brain.py links` suggested links
    (pages sharing `repos:`/`affects:`).
  - `AMBIGUOUS` — a low-confidence page sitting on a high-centrality
    edge (the existing "low confidence × high centrality"
    research-trigger already computes this signal).
  Computed in `brain.py links` / the views pipeline; it's a labelling
  convention over data the brain already derives.
- **Render it on the existing `/graph/` SVG.** Solid for EXTRACTED,
  dashed/faint for INFERRED, a distinct mark for AMBIGUOUS — the same
  edge-styling Graphify uses, but on the brain's build-time SVG, not
  a client-side library.
- **Expose it in MCP graph reads** so an agent can down-weight
  INFERRED/AMBIGUOUS edges when reasoning.
- **Bundled small item: GraphML / Neo4j-Cypher export.** Emit the
  page graph in a graph-interchange format (the brain exports JSON +
  SQLite today, no graph format). Deterministic; a sibling of the
  existing derived views. Low effort, niche-but-real interop value.

## No-gos (suggested)

- **No LLM in the tagging.** The tag is a deterministic mapping over
  existing edge sources; it stays a free producer (queue-and-tend).
- **No vis.js / client-side graph UI.** Render on the build-time SVG;
  the presentation-layer ADR forbids client-side graph/chart deps.
- **Don't overload the tags.** Graphify's own `INFERRED` conflates
  deterministic resolution and LLM guesses; the brain's mapping must
  keep each tier one clean meaning.
- **Don't generate wiki content from the graph.** The graph is a
  derived view of the wiki, never a source fed back in
  (closed-loop-poisoning rule).

## Rabbit holes (suggested)

- **Tag noise.** If most edges end up AMBIGUOUS the signal is
  useless; the thresholds need to keep AMBIGUOUS rare, matching the
  operator's damping preference on the research trigger.
- **Two-audience rendering.** The visual encoding must read on the
  SVG for humans *and* survive into the MCP/data layer for agents
  without a second source of truth.
- **Scope creep toward a graph database.** GraphML/Cypher export is a
  one-shot emitter, not a Neo4j dependency; keep it a derived file.

## Appetite (estimated)

Small — a labelling convention over data `pages.json` and `brain.py
links` already compute, plus edge-styling on the existing SVG and a
one-shot export emitter. The agent has no read on team capacity.

## Suggested success metrics

- A human reading `/graph/` can tell authored from suggested edges at
  a glance.
- An agent reading the graph over MCP can weight edges by provenance.
- AMBIGUOUS stays rare (low-noise), matching the research-trigger
  damping.
- No settled invariant regresses: no LLM in the producer, no
  client-side graph deps, the graph stays a derived view.

## Suggested next step

Small and cheap: add the three-tier tag to `brain.py links` output
and style the `/graph/` SVG edges by it — one deterministic pass over
existing data. If the tagged graph reads better (authored vs
suggested is obvious, AMBIGUOUS is rare and useful), `/shape` the MCP
exposure and the GraphML/Cypher export as follow-ons. If the tags add
noise, the convention is recorded and parked.

## Open questions for the human reviewer

- Is edge-level provenance worth the visual complexity on `/graph/`,
  or does page-level confidence already suffice?
- Are the three source→tier mappings right (authored=EXTRACTED,
  suggested=INFERRED, low-confidence-hub=AMBIGUOUS)?
- Is GraphML/Cypher export worth bundling, or a separate low-priority
  item?
- Does this overlap with in-flight work the agent can't see?
