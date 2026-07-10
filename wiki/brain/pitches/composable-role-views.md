---
title: "Composable role-fit views — declarative assemblies over wiki synthesis, connector state, and observability data"
kind: pitch
status: superseded
superseded_by: brain/prds/composable-role-views.md
updated: 2026-07-10
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-10--composable-views-idea.md
  - ../../../sources/conversations/2026-07-10--sqlite-substrate-musing.md
  - ../../../sources/research/2026-07-10--sqlite-fts5-derived-index.md
  - ../../../sources/research/2026-07-10--composable-views-prior-art.md
  - ../../../sources/research/2026-07-10--datasette-serving-surface.md
  - ../../../sources/research/2026-07-10--datadog-langfuse-apis.md
  - ../../../sources/research/2026-07-10--sqlite-index-prototype.md
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

## Deepdive findings (2026-07-10)

The load-bearing points were researched before any bet (five
research notes under `sources/research/`, cited above):

- **Feasibility is proven, not presumed.** A prototype index over
  the live corpus built in 19 ms (304 KB); a 50k-row benchmark on
  this machine rebuilt full FTS5 in ~1.5 s. System Python ships
  SQLite 3.45.1 with FTS5 and JSON core. The 0.4 research picker
  reproduced as five lines of SQL returning the same rows the
  Python producer queues.
- **The design shape is validated twice by prior art.** Obsidian's
  official Bases format is a YAML view spec (shared filters +
  multiple named views with local overrides — the anatomy to copy);
  Datasette's canned queries are SQL-in-YAML rendered as pages and
  APIs. Steampipe validates schema-per-connector tables
  (`github.*`, `datadog.*`) with cross-connector joins as the
  payoff. Logseq's Datalog is the cautionary tale — familiarity
  beats power; ship two tiers (simple filter shorthand + full SQL),
  never three.
- **Index mechanics are settled**: external-content FTS5 rebuilt in
  one statement, `unicode61 tokenchars '-_'` so code identifiers
  survive, build-to-temp + atomic `os.replace()`, readers open
  read-only URIs, user search tokens quoted against MATCH-syntax
  injection, links table indexed on both endpoints.
- **Datasette is the near-free serving tier**: immutable mode over
  the same index behind an identity-aware proxy is its canonical
  deployment; pilot on stable 0.65.x; it is the power-user/API
  surface, not a branded product UI.
- **Connector specifics**: Datadog — monitor state (not logs) is
  the daily production-state primitive (logs quota ~300 req/hr;
  opt-in only); scoped app keys (`monitors_read`, `slos_read`) +
  required `DD_SITE`. Langfuse — **no read-only key type exists**;
  keys are project-scoped and write-capable, so the credential
  guidance is dedicated-project keys or self-host. Durable cursors
  are last-run timestamps (server cursors expire across runs);
  overlap windows ~5 min and dedupe by id.

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
- **A derived SQLite index is the query substrate** (operator
  direction 2026-07-10). A `brain.py index` step, riding the views
  pipeline, deterministically rebuilds a **gitignored, disposable**
  database from the three data planes: `pages` (frontmatter +
  computed edges), `links`, `state` (flattened extracts),
  `snapshots` (connector files parsed to rows where tabular),
  `inbox`. Single writer (the indexer), read-only consumers, FTS5
  over page and snapshot text. Files remain the only source of
  truth — the db can be deleted and regenerated at any time.
- **Blocks are named SQL queries** over that documented schema —
  no invented filter language. Shipped example specs carry
  readable starter queries; a spec author edits SQL, the one
  language every operator and agent already knows. Convenience
  shorthands (a `pages:` filter block) can compile to SQL, not
  bypass it.
- **Rendering rides the existing views pipeline**: `brain.py views`
  additionally emits `wiki/_views/custom/<name>.md` per spec, with
  the standard auto-generated banner. The Astro UI renders them
  like any other view; `/dash` links them; agents read them as
  priming context; the home dashboard stays the one canonical
  primer.
- **Two new connectors under the existing snapshot contract**:
  `datadog-pull` (daily monitor states + SLOs + incremental events;
  logs search opt-in only — quota-scarce) and `langfuse-pull`
  (prompt inventory + production-labeled versions, incremental
  traces/scores). Both no-op until configured; plain REST, no
  vendor SDKs; scoped credentials in `.env` (Datadog app keys
  scoped to `monitors_read`/`slos_read` + `DD_SITE`; Langfuse has
  no read-only keys — document dedicated-project keys or
  self-host). The connector contract gains one optional clause: a
  connector MAY maintain a compact state extract for view tiles.
- **Role fit is convention, not accounts**: a view is a file; a
  persona field on the spec documents who it serves; individuals
  pin or copy the specs that fit their work. Example specs ship in
  the shell (`engineer`, `pm`, `operator`) as editable starting
  points.

## Rabbit holes

- **Inventing a query language.** Resolved by the SQLite direction
  — blocks are SQL over the derived index. The remaining hole to
  avoid: query builders / DSLs *on top of* SQL.
- **The db becoming load-bearing.** It is an index, never a store:
  no writes from anything but the indexer, no data that exists
  only in the db, delete-and-rebuild always safe.
- **Live dashboards.** Views are regenerated markdown on the
  existing cadence (timer + on-demand), not a websocket product.
- **LLM-composed blocks.** v1 is fully deterministic; a synthesised
  "digest" block is a `/tend` product for a later pitch.
- **Per-user state.** No accounts, no server-side preferences — the
  file is the preference.

Datasette over the same index is a candidate read-only browse/API
surface for the serving slice — noted for that pitch, not bet on
here.

## No-gos

- Views never write anything — read-only renderers over the three
  data planes.
- Views never bypass the layering: `snapshots` blocks render
  observations with source paths; synthesis stays in wiki pages.
- No vendor SDK dependencies in connectors; plain HTTPS pulls with
  read-only-scoped credentials, per the connector contract.
