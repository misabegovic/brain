---
title: "Composable role-fit views — declarative assemblies over wiki synthesis, connector state, and observability data"
kind: pitch
status: draft
updated: 2026-07-10
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-10--composable-views-idea.md
  - ../adrs/connector-snapshot-contract.md
  - ../../../brain-schedule.yml
---

# Composable role-fit views

Pre-bet pitch per the operator's 2026-07-10 direction: let anyone
assemble the brain's incoming data the way *their role* needs it —
out of the box, locally, as files.

## Problem

The brain now has three data planes — synthesised wiki pages,
connector snapshots under `sources/`, and compact state extracts
under `wiki/_state/` — but only fixed-axis generated views over the
first (`by-kind`, `by-repo`, `by-epic`). An engineer who wants
"recent decisions + implementation deltas + production error state"
and a PM who wants "open initiatives + insights + customer signal"
both assemble that context by hand, every session. Meanwhile whole
categories of role-critical context (observability state from
Datadog, prompt/eval state from Langfuse) have no connector at all.
The brain holds or could hold everything a role needs to prime a
session; nothing composes it per role.

## Appetite

Medium — one cycle. The renderer and two or three block types are
the core; each additional block type or connector is an increment,
not a prerequisite.

## Solution

Fat-marker sketch (details are the build's call):

- **View specs are YAML files** in a `views/` folder at the repo
  root — operator-editable, git-versioned, shareable. A spec names
  the view, an optional audience persona, and an ordered list of
  **blocks**.
- **Blocks are deterministic queries with fixed parameters**, one
  renderer each. The v1 set: `pages` (filter wiki pages by kind /
  repo / status / confidence, sort, limit), `state` (render one
  `wiki/_state/*.json` extract as a tile — deadlines, issues,
  security, connector states), `snapshots` (latest N files matching
  a `sources/<connector>/...` glob, with title + excerpt), `inbox`
  (pending tend items, filterable by kind), and `links` (a
  link-graph health slice).
- **Rendering rides the existing views pipeline**: `brain.py views`
  additionally emits `wiki/_views/custom/<name>.md` per spec, with
  the standard auto-generated banner. The Astro UI renders them
  like any other view; `/dash` links them; agents read them as
  priming context; the home dashboard stays the one canonical
  primer.
- **Two new connectors under the existing snapshot contract**:
  `datadog-pull` (monitor states, recent error patterns → snapshots
  + a `wiki/_state/datadog.json` extract) and `langfuse-pull`
  (prompt versions, eval summaries → snapshots + extract). Both
  no-op until configured; read-only tokens in `.env`; plain REST,
  no vendor SDKs. The connector contract gains one optional clause:
  a connector MAY maintain a compact state extract for view tiles.
- **Role fit is convention, not accounts**: a view is a file; a
  persona field on the spec documents who it serves; individuals
  pin or copy the specs that fit their work. Example specs ship in
  the shell (`engineer`, `pm`, `operator`) as editable starting
  points.

## Rabbit holes

- **A query language.** Block parameters stay a fixed enum of
  filters; the moment a spec wants expressions, stop and rethink.
- **Live dashboards.** Views are regenerated markdown on the
  existing cadence (timer + on-demand), not a websocket product.
- **LLM-composed blocks.** v1 is fully deterministic; a synthesised
  "digest" block is a `/tend` product for a later pitch.
- **Per-user state.** No accounts, no server-side preferences — the
  file is the preference.

## No-gos

- Views never write anything — read-only renderers over the three
  data planes.
- Views never bypass the layering: `snapshots` blocks render
  observations with source paths; synthesis stays in wiki pages.
- No vendor SDK dependencies in connectors; plain HTTPS pulls with
  read-only-scoped credentials, per the connector contract.
