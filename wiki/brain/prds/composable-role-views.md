---
title: "Composable role-fit views — SQL view specs over a derived index, with observability connectors"
kind: initiative
status: living
updated: 2026-07-10
confidence: medium
supersedes: brain/pitches/composable-role-views.md
sources:
  - ../pitches/composable-role-views.md
  - ../../../sources/conversations/2026-07-10--composable-views-idea.md
  - ../../../sources/research/2026-07-10--composable-views-prior-art.md
  - ../../../sources/research/2026-07-10--sqlite-index-prototype.md
---

# Composable role-fit views

Graduated from the [pitch](../pitches/composable-role-views.md) on
the operator's 2026-07-10 bet, after a five-note deepdive (see the
pitch's Deepdive findings).

## What

A view layer anyone can compose: small spec files in a `views/`
folder define named views assembled from blocks — saved SQL queries
and simple declarative shorthands — over a derived, disposable
SQLite index of the brain's three data planes (wiki pages with
computed edges, connector snapshots, state extracts, plus the link
graph and the tend inbox). Each spec renders to a generated page
under the views output folder, readable in the UI, on the ops
dashboard, and by agents as session priming. Two new observability
connectors (Datadog monitor/SLO state, Langfuse prompt inventory)
extend the existing snapshot contract so production state and
prompt state become queryable planes. Example specs for three roles
(engineer, pm, operator) ship as editable starting points.

## How

At the fat-marker level (the ADR names the bet; the build owns the
details): a deterministic indexer rides the existing views pipeline
and rebuilds the index from files on every regeneration — files
stay the only source of truth, the index is gitignored and
delete-safe. View specs follow the layering prior art validated
(shared context, multiple named blocks with local parameters); raw
SQL is the full tier and a small set of shorthands compiles to SQL
rather than bypassing it. Full-text search uses the index's FTS
tables. The connectors follow the 0.3 contract verbatim, adding
the optional state-extract clause the pitch proposed.

## Why

Role fit is the gap between what the brain holds and what a person
(or agent session) actually needs in front of them. The three data
planes exist; only fixed-axis views compose them. Making the view
layer user-composable turns the brain from "a wiki with feeds" into
per-role working context — decisions, implementation deltas,
production state, prompt state — assembled the way each role needs,
as portable git-versioned files. Prior art validates every element;
the prototype proved the cost is trivial.

## Now

Shipped 2026-07-10, same day as the bet. The indexer, the read-only
query command, the view-spec renderer with three example specs, and
both connectors are live; the daily views-regen operation now
refreshes the index and re-renders custom views. Datadog and
Langfuse connectors no-op until an operator configures watch
targets and credentials.

## Perceived

Freshly built — no divergence recorded yet. The risk to watch: view
specs are only as good as the schema documentation; if the schema
drifts without the docs, spec authors (human or agent) write
queries against a phantom.

## Target

Operator adoption: configure the first real project, let the
example specs prove or disprove their block choices, and iterate
specs in place. The serving slice (next roadmap step) picks up the
Datasette pilot over this same index. A synthesised digest block
(LLM-written, via the tend loop) remains a future pitch, per the
pitch's fenced rabbit holes.
