---
title: "Competitor intel lives at wiki/org/competitors/<competitor>/index.md, ingested via the existing wiki-ingest classifier with an explicit hint override"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
summary: >
  Public competitor information routes to per-competitor org shelves with web snapshots under sources/; press-release claims stay marked as vendor claims, never facts.
sources:
  - ../../../AGENTS.md
  - .claude/skills/wiki-ingest/SKILL.md
  - ../../../tools/templates/competitor-index.md
---

# Competitor intel lives at `wiki/org/competitors/<competitor>/index.md`, ingested via the existing wiki-ingest classifier with an explicit hint override

**Decision.** Per-competitor synthesis lands at
`wiki/org/competitors/<competitor>/index.md` with `kind: reference`. The
page's frontmatter carries `affects:` for every sibling repo whose strategy
the competitor's product touches (so the auto-computed reverse edge propagates
back to repo state views), and `confidence:` starts low per the brain's
confidence-floor rule, earning medium as cited evidence accumulates.
Competitor content routes through the **existing `/in` ingest path** — the
[`intake`](../../../.claude/skills/intake/SKILL.md) classifier recognises
competitor-shaped sources, and
[`wiki-ingest`](../../../.claude/skills/wiki-ingest/SKILL.md) carries the
shelf routing and the snapshot-path branch — rather than a new dedicated
skill. When auto-classification is uncertain or wrong, the operator overrides
with an explicit leading-marker hint of the shape `/in <url> competitor:
<name>`, mirroring the intake skill's existing override surface. Source
snapshots land at `sources/web/competitors/<competitor>/<slug>--<shortid>.md`,
folder-per-competitor to mirror the wiki side. No new `kind:` is added.

## Context

The gap: competitor news (press releases, product pages, trade-press coverage)
had no committed home in the brain, and four coupled questions were open —
where per-competitor synthesis pages live, how competitor content is routed
in, where source snapshots land, and what `kind:` the synthesis page carries.

Three forces shaped the answer. The first is the brain's nested-emergent rule:
folders earn their place once content arrives; don't promote preemptively. A
new top-level `wiki/competitors/` namespace would create a peer to `wiki/org/`,
`wiki/brain/`, and the per-repo trees, which the brain's three-level model
(brain / org / repo) doesn't entertain — competitors are not a fourth level,
they are *content within the org level*: cross-org topics that don't belong to
any single sibling repo.

The second is the `kind:` enum cost. Every kind addition propagates through
the validator, the views generator, the templates, and the schema's page-kinds
table. A `kind: competitor` would buy no section-structure differentiation the
existing `kind: reference` doesn't already serve — competitor pages describe
*how a thing is*, which is the literal definition of reference.

The third is routing-skill blast radius. Extending the existing intake and
wiki-ingest skills with a competitor-content classifier costs one row in two
routing tables and one snapshot-path branch; a new dedicated ingest skill
costs a new skill file, new entries in the schema's operations and
intent-mapping tables, and a parallel-but-divergent code path that future
drift would eventually need to reconcile.

The classifier recognises competitor-shaped sources by three signals: a press
release naming a competitor company in its headline; a URL on a
known-competitor domain (the catalogue is seeded, not exhaustively enumerated
— agents extend it as content earns it); and trade-press follow-up coverage
that name-checks a competitor alongside the org's product category. The
convention was sized against a realistic first case — a single competitor
with one press release plus a handful of follow-up sources — without
prematurely committing to multi-competitor cross-cutting structures.

## Alternatives

- **Top-level `wiki/competitors/` namespace** *(rejected)* — treats
  competitors as a fourth level peer to brain / org / repo. Competitors are
  cross-org reference content, which is exactly what `wiki/org/` exists for;
  a fourth-level exception would invite others by analogy (partners,
  regulators, customers).
- **Per-repo `wiki/<repo>/competitors/`** *(rejected)* — forces a competitor
  whose product touches two sibling repos to land twice or arbitrarily under
  one. Competitors are inherently cross-repo at the org's product-strategy
  level.
- **A new dedicated ingest skill** *(rejected)* — the routing problem is
  small (classify three or four content shapes; choose one snapshot path) and
  does not warrant a separate skill with its own command surface and
  intent-mapping row. The existing auto-classification path picks the correct
  sub-skill, and a new competitor row in the routing table is the natural
  extension.
- **Flat snapshots with a frontmatter discriminator** *(rejected)* — a flat
  `sources/web/<slug>--<shortid>.md` shape works against the wiki side's
  folder-per-competitor structure and forces every consumer to parse
  frontmatter. One competitor accumulates roughly 5–20 sources over a year —
  bounded but non-trivial volume that earns the folder.
- **A new `kind: competitor`** *(rejected)* — buys no section-structure
  differentiation over `kind: reference`, and pays cost across the validator,
  views generator, templates, and schema.
- **Do nothing** *(rejected)* — the next competitor ingest improvises the
  path and the convention gets written by accident in whatever shape the
  first ad-hoc run picks. Convention before content is the right ordering.

## Consequences

- **Closes** the shelf question: a competitor-shaped source landing outside
  `wiki/org/competitors/<competitor>/` after this decision is a routing bug
  or a convention violation, not an open question.
- **Closes** `kind: competitor` and a dedicated ingest skill at this scale;
  either requires superseding this ADR with explicit alternatives rationale.
- **Opens** the classifier as a citable component of the intake skill, with
  wiki-ingest carrying the shelf-routing rule and the snapshot-path branch.
- **Opens** per-competitor sub-pages (a product page, an event page) via the
  nested-emergent rule when content is dense enough, and cross-competitor
  pages (comparison matrices, category overviews) at an index page under
  `wiki/org/competitors/` once two or three competitors exist. None
  are pre-created.
- **Opens** a deterministic competitive-landscape input for repo state pages
  and shaping runs via the `affects:` reverse-edge propagation.
- **Costs** — one routing-table row each in the intake and wiki-ingest
  skills, plus the explicit-hint override pattern and the snapshot-path
  branch, owned by the build phase rather than left as an open promise.
- **Costs** — an optional skeleton template at
  `tools/templates/competitor-index.md` for the first source of a new
  competitor; the generic reference template is the fallback.
- **Costs** — one row in the schema's content-routing table and a
  discoverability entry on the wiki home page's catalogue. Snapshot
  immutability holds: the additive-only rule for `sources/**` applies
  unchanged, and re-fetches overwrite rather than edit.
