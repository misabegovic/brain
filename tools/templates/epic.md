---
title: <one-line umbrella initiative name, e.g. "Migrate Ember to React" or "Adopt OAuth2 across all services">
kind: epic
status: draft                       # draft | living | superseded | archived
updated: YYYY-MM-DD
team: <owning team or focus team>
division: <umbrella division>
repos:
  - <scope repo>
confidence: low                     # PM-authored: starts low, raised as the umbrella is reviewed
sources:
  - <pitch source — Notion URL, strategic want, customer-feedback synthesis, etc.>
---

# <one-line umbrella initiative name>

Epic page for `wiki/<scope>/epics/<slug>.md`. Records the
**umbrella narrative** for an initiative too large to fit in a
single PRD/ADR pair — multiple PRDs and multiple ADRs spawn
as children under this umbrella, each shipping independently
while connected back here via `parent_epic: <slug>`
frontmatter.

**Epics have no umbrella ADR pair** (per
[`wiki/brain/adrs/multi-prd-epic-shape.md`](../../brain/adrs/multi-prd-epic-shape.md)
§ Decision). The umbrella has no single bet to make; decisions
live in the children.

> **Author guidance — what does NOT belong in this epic.**
>
> - **No engineering bets / architectural decisions.** Each
>   child PRD/ADR makes its own bets. The umbrella records
>   *what* coordinates the children and *why*; the *how* is
>   per-child.
> - **No detailed work-decomposition.** The `## Children`
>   section accumulates as real children spawn via regular
>   `/shape` invocations with `parent_epic: <slug>`. The
>   epic's Phase 1 may name *anticipated* children but
>   shouldn't prescribe them — children may evolve as the
>   umbrella unfolds.
> - **No code samples / interface definitions / vendor
>   commitments.** Per the PRD template's same guidance.

## Objective

The umbrella's load-bearing user-outcome. Why does this
*umbrella-scale* work exist? What user need does the whole
initiative serve, beyond what any single child PRD could
serve alone? One sentence that fits on the back of a napkin
+ one paragraph of unpacking.

## Background

What's the current state? What's the gap that triggers the
umbrella? Why now? What incidents / strategic wants /
customer-feedback patterns inform the framing? Cite the
sources that ground the narrative — same grounding rule as
PRDs.

If the umbrella decomposes a known existing surface (a
codebase area, a feature family, an org pattern), describe
the surface in enough detail that the reader can place each
anticipated child within it.

## Affected personas

The personas the umbrella serves — typically broader than
any single child's persona set. List 2-5 named personas
with the user need each one carries in the umbrella's
context.

For each persona: *Now* (what they experience without the
umbrella), *Target* (what changes when the umbrella's
children all ship). Each persona's path through the
umbrella may touch different children; that's expected.

## Scope

What's *in* the umbrella's coordination — the cohesive set
of children the umbrella exists to coordinate. What's *out*
— work that's adjacent but doesn't belong under this
umbrella (named explicitly to prevent scope-creep).

The umbrella's scope is the *coordination scope*, not a
sum of child scopes. Each child has its own scope statement;
the umbrella scopes the *narrative*.

## No-gos

Hard boundaries the umbrella commits to. Different from a
PRD's no-gos in that they apply *across all children*: e.g.
*"no breaking the existing public API surface during the
migration"* might be an umbrella-level no-go that every
child inherits.

## Children

The umbrella's child list — populated as children spawn
via regular `/shape <scope> <child-pitch>` invocations
with `parent_epic: <slug>`. The agent maintains this
section automatically:

- One line per child slug, formatted as
  `- [<title>](../prds/<slug>.md) — *<status>*`
- `<status>` reflects the child's lifecycle (draft / living
  / superseded / archived per the brain's general status
  vocabulary), surfaced via the status-mapping in
  `.claude/skills/zoom-out/SKILL.md`'s status table.
- New children are appended as they spawn. Existing entries
  update on phase advances (`/continue` maintains them).

At Phase 1 of the epic, this section is empty — *no
children yet*. Don't pre-populate; children appear as
real spawn events fire.

## Success metrics

What signals the umbrella is *working*? Typically broader
than per-child metrics:

- A user-visible outcome that materialises only when
  multiple children have shipped together.
- A coherence signal — does the umbrella narrative still
  read as one coherent story as more children land, or
  has it fragmented? Anecdotal review at major
  child-shipping milestones.
- A throughput signal — children shipping at a healthy
  cadence (no months-long gaps suggesting the umbrella
  is stalled).

Re-pitch signal at the umbrella level: if the umbrella's
children stop shipping for >1 cycle, or if a child
materially contradicts the umbrella's framing, pause and
re-shape.

## Open questions

Track umbrella-level open questions here. Per-child open
questions stay on the children's pages.

## Sources

Cite the sources that grounded the umbrella narrative.
Same rule as PRDs: every load-bearing claim cites a
source the reader can verify.
