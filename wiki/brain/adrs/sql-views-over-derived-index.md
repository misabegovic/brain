---
title: "View specs are SQL over a derived, disposable SQLite index; shorthands compile to SQL; the index rides the views pipeline"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../prds/composable-role-views.md
  - ../../../sources/research/2026-07-10--sqlite-fts5-derived-index.md
  - ../../../sources/research/2026-07-10--composable-views-prior-art.md
  - ../../../sources/research/2026-07-10--sqlite-index-prototype.md
---

# View specs are SQL over a derived, disposable SQLite index; shorthands compile to SQL; the index rides the views pipeline

**Decision.** The composable-views PRD is delivered on three commitments.
First, a **derived SQLite index** is the one query substrate: rebuilt
deterministically from the files on every views regeneration, gitignored,
single-writer (the indexer), read-only for every consumer, and always safe
to delete — files remain the only source of truth. It carries the wiki
pages with their frontmatter and computed edges, the link graph, the tend
inbox, flattened state extracts, connector-snapshot rows, and
full-text-search tables over page and snapshot text. Second, **view blocks
are SQL** over that documented schema; a deliberately small set of
declarative shorthands (page filters, state tiles, inbox slices)
*compiles to* SQL rather than bypassing it, giving the two-tier surface —
simple filters for most needs, full SQL as the escape hatch. Third,
**rendering rides the existing views pipeline**: specs live as
operator-editable files in a top-level views folder, and regeneration
emits one generated page per spec into the views output shelf, where the
UI, the ops dashboard, and agent sessions consume them like any other
generated view.

## Context

The PRD's deepdive (five research notes under the research sources shelf)
resolved every load-bearing unknown before this bet. Feasibility was
proven locally: the prototype indexed the live corpus in nineteen
milliseconds into a three-hundred-kilobyte file, a fifty-thousand-row
benchmark rebuilt full-text indexes in under two seconds on the
operator's machine, and the existing deepening picker reproduced as five
lines of SQL returning the same rows its Python implementation queues.
Prior art validated the exact shape twice — Obsidian's Bases format
(YAML view specs: shared filters plus multiple named views with local
overrides, frontmatter-properties only) and Datasette's canned queries
(SQL plus parameters in metadata, rendered as pages and APIs) — while
Steampipe validated schema-per-connector tables with cross-connector
joins, and Logseq's Datalog documented the failure mode of an unfamiliar
query language. The index mechanics were settled by the research:
external-content full-text tables rebuilt in one statement, a tokenizer
that keeps hyphenated and underscored identifiers whole, build-to-temp
with an atomic rename so readers are never disturbed, read-only
connections for consumers, and whitespace-token quoting to neutralise
match-syntax injection on user queries.

The governing constraints carried over unchanged from prior decisions:
the queue-and-tend ADR fixes that no model runs on a schedule, so the
index build and view rendering are fully deterministic; the connector
snapshot contract fixes that external data enters only as immutable
snapshots; and the brain's substrate thesis fixes that nothing
load-bearing may live only in a binary artefact.

## Alternatives

- **SQL over a derived index, shorthands compiling to SQL** *(chosen)* —
  the only option validated by two independent successful prior arts,
  fluent for agents (who author specs for non-technical users), and
  zero-dependency (the SQLite module ships in the standard library).
- **A bespoke declarative filter language** (the pitch's original
  sketch) — rejected: it caps composability at whatever filters the
  kernel hardcodes, and Logseq's experience shows unfamiliar query
  surfaces exclude exactly the users this feature serves. Kept only as
  the thin shorthand tier that compiles to SQL.
- **Query the files directly at render time** (no index) — rejected:
  every view render re-parses the corpus, cross-plane joins become
  hand-written Python, and the Dataview precedent shows a slow query
  surface kills adoption. The index is cheap enough to rebuild that
  freshness is a non-issue.
- **A persistent, incrementally-updated database as the store** —
  rejected outright: a binary source of truth breaks diffs, merges,
  agent ergonomics, and the audit trail; this was the explicit boundary
  the operator's SQLite direction drew.
- **Embedding-based retrieval as the query substrate** — rejected for
  this decision: deterministic SQL covers the composable-views need;
  semantic search remains a separate optional concern (and the external
  memory layer already handles verbatim recall).
- **Do nothing** — the three data planes stay queryable only by hand;
  the role-fit gap the PRD names persists. Rejected by the bet.

## Consequences

- **Closes** the query-language question permanently: SQL is the
  contract; any future convenience layer must compile to it. The schema
  becomes documentation-critical — it ships as part of the index
  command's help and the views documentation, and schema changes are
  additive-preferred.
- **Closes** the index's status: never committed, never load-bearing,
  never written by anything but the indexer. A corrupted or stale index
  is repaired by deletion.
- **Opens** every existing deterministic producer to future
  simplification as saved queries; opens the Datasette pilot for the
  serving slice over the same artefact; opens cross-plane joins
  (synthesis × production state × prompt state) as a one-line-of-SQL
  capability.
- **Opens** full-text search over the corpus and snapshots through the
  index's ranked match tables, replacing hand-rolled keyword scoring
  where the index is present.
- **Costs** a schema-documentation duty and one more generated artefact
  per view spec in the views shelf; both bounded and reviewable.
- **Costs** SQL exposure in spec files — mitigated by read-only
  connections, row limits at render time, and the injection-quoting
  rule on any user-supplied search input.

## Build notes

Shipped 2026-07-10 with the PRD. Refinements the build chose within this
decision's frame: the two observability connectors landed with
deliberately narrow daily defaults per the API research — Datadog pulls
monitor states and SLO inventory (events and logs deferred; logs are
quota-scarce and stay opt-in), Langfuse pulls the prompt inventory with
production-labelled versions (trace/score increments deferred) — each
writing both immutable snapshots and a compact state extract for view
tiles. The render layer emits tables for multi-column results and lists
for single-column ones, with a per-block row cap. Example specs shipped
for three roles (engineer, pm, operator) as editable starting points,
exercising both tiers: shorthands for the common blocks, raw SQL for the
cross-plane joins.
