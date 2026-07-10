---
title: "Operator lessons live as Lessons subsections on conventions pages plus one cross-cutting org page"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
  - .claude/skills/capture/SKILL.md
---

# Operator lessons live as `## Lessons` subsections on conventions pages plus one cross-cutting org page

**Decision.** Repo-bound operator lessons live as a `## Lessons` subsection
convention on the target repo's existing `wiki/<repo>/permanent/conventions.md`
page; cross-cutting lessons that span repos or sit at brain-meta level live as
subsections on a single page at
[`wiki/org/operator-lessons.md`](../../org/operator-lessons.md)
(`kind: reference`). No new `kind:` is added to the validator, no required-sections
entry, no reverse-edge machinery, and no auto-creation of missing conventions
pages. Each lesson follows the same sub-shape: a `### <slug>` heading
(kebab-case, ≤ 6 words), a short prose *Why* paragraph naming the incident or
constraint that motivated the rule, a short prose *How to apply* paragraph
naming when and where the rule kicks in, and an inline *Graduated from*
citation pointing at the memory entry or prep source it came from. Lessons are
subsections, not pages — no frontmatter of their own; provenance lives inline.

## Context

Operator lessons are two-line *Why + How to apply* rules captured in the
operator's private agent-memory store on their own machine. A meaningful share
of them are team-applicable, but the store is invisible to a different operator
on a different machine and to a fresh agent on a CI runner — both re-derive the
same patterns from primary sources, imperfectly. The brain needed a resident
shelf for the team-applicable subset.

Several findings shaped the answer. First, graduation already happens
organically for repo-specific procedural rules where a conventions page exists:
one sibling repo's conventions page had absorbed several such rules, and the
originating memory entries cite that page as their canonical home. The question
was whether to formalise the pattern that already operates or replace it with a
different shape.

Second, not every active repo has a `permanent/conventions.md` page, and the
brain's own scope has no `permanent/` folder at all. The schema's
structure-emergence rule says that is by design — pages earn their place when
content earns it — so any convention leaning on conventions pages as the
universal home must handle their absence explicitly rather than silently
assume them into existence.

Third, several team-applicable lessons are not repo-bound at all: force-push
verification discipline applies across every repo with branch protection;
skills-over-memory governance applies to any repo with a skills folder;
PR-description shape cuts across every PR an agent opens. A purely per-repo
shape leaves this cross-cutting slice unhomed.

Fourth, the brain recently paid full schema cost for epics (see
[`multi-prd-epic-shape.md`](multi-prd-epic-shape.md)) — a new kind, validator
entries, a template, a reverse edge. That weight was right for epics, which
track multi-PRD initiatives with their own lifecycle. Lessons do not warrant
it: each is a short prose block that fits comfortably as a subsection on an
existing `kind: reference` page. What was missing is the *convention*, not a
new schema.

Fifth, the `/capture` routing table treated all captured content as
*observation* (state updates, permanent-page edits). Lessons are
*prescription* — postmortem-shaped rules about how to act — and the table had
no row for rule-shaped captures. The decision adds one row directing
rule-shaped content to the two shelves above; direct hand-editing of the
shelves remains valid. The graduation hop from operator memory to brain stays
documented but not gated, and once the convention exists, net-new
team-applicable lessons are authored brain-first, with the private memory
entry (if any) reduced to a pointer.

For repos whose conventions page does not yet exist, a repo-specific lesson
lands on the org page with a *Scope:* note naming the repo, and migrates when
the conventions page earns its place organically.

## Alternatives

- **A new `kind: lesson`, one lesson per page** *(rejected)*. Lessons would
  live at `wiki/<scope>/lessons/<slug>.md` with validator support enforcing
  the Why / How-to-apply sections. Rejected because a lesson is 4–8 lines of
  prose; one-page-per-lesson fragments a growing corpus when the natural
  shape is a subsection list, and the validator weight pays for structure the
  content does not need.
- **Conventions-page-only, with auto-creation for missing scopes**
  *(rejected)*. Auto-creating conventions pages inverts the
  structure-emergence rule: content earns the page, not the convention. The
  hybrid keeps the rule intact — cross-cutting and orphaned lessons land on
  the org page until a per-repo conventions page earns its place.
- **Single org page only, all lessons there** *(rejected)*. Easiest to walk
  end-to-end, but it loses the per-repo affinity the organic graduation
  precedent already exhibits — a repo-specific rule belongs next to the
  conventions section it complements, not floating on a cross-cutting list.
- **Do nothing — leave lessons in operator memory** *(rejected)*. The status
  quo produces an asymmetric corpus: a couple of lessons graduate organically,
  the rest stay operator-private and invisible to fresh agents and new
  teammates. The point of the decision is to close that asymmetry
  deliberately.

## Consequences

- **Closes** the open question of where lessons go. Future team-applicable
  entries have a known hop with known target paths, and there is no
  `kind: lesson` to add later without a fresh ADR superseding this one.
- **Closes** the auto-create-conventions-page path; the structure-emergence
  rule wins.
- **Opens** an audit pass over the existing memory corpus: triage each entry
  as team-applicable or operator-scoped, route the team-applicable subset to
  the appropriate shelf, seed worked examples, and add the `/capture`
  routing-table row.
- **Opens** brain-first authoring for net-new team-applicable lessons; the
  graduation pattern inverts, with operator memory reserved for genuinely
  operator-scoped rules.
- **Costs** — conventions pages and the org page grow over time. The
  page-size discipline (~500 lines) is the soft cap; crossing it triggers the
  standard promotion of a page into a folder with sub-pages, deferred to
  whoever crosses the threshold.
- **Costs** — provenance is in-prose, not in-frontmatter, so corpus-wide
  queries over lessons require a text search rather than a frontmatter walk.
  Acceptable while the corpus is small and read by humans and agents rather
  than tooling; the per-page alternative remains available via a future ADR.
- **Costs** — lessons cannot participate in the brain's frontmatter
  reverse-edge mechanism, because they are subsections rather than pages.
  Cross-references are inline links only.
