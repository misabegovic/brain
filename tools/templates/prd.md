---
title: <one-line user-facing title, e.g. "Bulk candidate-tagging from the inbox">
kind: initiative
status: draft                       # draft | living | superseded | archived
updated: YYYY-MM-DD
team: <owning team>
division: <umbrella division>
repos:
  - <target repo>
appetite: small | medium | big      # Shape Up: ≤2w / 2-4w / full 6w cycle
confidence: low                     # PM-authored: starts low, raised as the PRD is reviewed
sources:
  - <pitch source — Notion URL, feedback insight, customer-interview transcript, etc.>
---

# <one-line user-facing title>

Product Requirements Document for `wiki/<repo>/prds/<slug>.md`.
Records *what* a piece of work is and *why* it matters — **not**
*how* engineering will build it. The Tech Lead reviews this PRD
and produces the corresponding ADR(s) at
`wiki/<repo>/adrs/<slug>.md`.

This template is for **human-supervised** PRDs: a human reviews
the pitch, iterates with the agent or PM, approves the PRD
before the Tech Lead phase begins.

For **agent-authored** PRDs (no human review yet), use
`prd-ai-suggestion.md` and place the file under
`wiki/<repo>/ai-suggestions/prds/`.

> **Author guidance — what does NOT belong in this PRD.**
>
> - **No code samples.** PRDs hint at the user-facing shape, not
>   the implementation. Engineering writes the spec / ADR / code.
> - **No technical interface definitions.** No HTTP endpoints,
>   JSON schemas, function signatures, database tables. Those
>   are ADR + permanent/interfaces.md territory.
> - **No "how" detail beyond what's needed to test feasibility.**
>   The Tech Lead may push back on the appetite or scope — leave
>   them room.
> - **No commitments to specific libraries / frameworks /
>   vendors.** Per ProductPlan: a PRD "may hint at a potential
>   implementation to illustrate a use case but may not dictate
>   a specific implementation."

## Objective

The single sentence that says what would ship if this PRD
becomes work, and what user outcome that produces. If the
sentence isn't sharp, the PRD isn't ready.

## Background

Why this matters now. What changed in the world, the product,
or the customer base that makes this the right thing to ship in
this cycle rather than next quarter. Cite customer feedback,
insight pages, the `/feedback` trail, conversations with sales,
support tickets — whatever evidence is load-bearing.

## Affected personas

- `[<persona-name>](../../../.claude/personas/users/<slug>.md)` —
  one paragraph: their current frustration, the change they'd
  experience, the value to them. If a persona doesn't appear
  in `users/`, propose adding it before the PRD lands.
- (one entry per primary persona; secondary personas in a
  follow-up bullet list)

A PRD without at least one named persona is a feature spec, not
a PRD. The persona link is non-negotiable.

## Now / Perceived / Target

Per the brain's three-states convention:

- **Now** — what's true on the relevant surface today, with
  citations to sibling-repo source paths and brain reference
  pages.
- **Perceived** — what the org appears to *believe* about the
  surface today. Where Now diverges from Perceived, that's
  where the risk hides.
- **Target** — what's true if this PRD ships and the build is
  done. Distinct from Now in concrete, observable ways.

## Scope

What's **in** this release: the user-facing capability. Three to
seven sentences. Wireframe references go here if they exist.

## No-gos

What's explicitly out of scope. Adjacent capabilities that look
like extensions of this work but aren't part of it. The Tech
Lead and Developer agents will treat this list as a hard
boundary.

## Rabbit holes

Areas where engineering is expected to *stop digging* if they
hit them. *"If you find yourself rebuilding X, stop and
re-pitch."* Per Shape Up: rabbit holes are where appetites get
blown.

## Appetite

Small (≤ 2 weeks) | medium (2–4 weeks) | big (full 6-week
cycle). Justify in one paragraph.

The appetite is the *budget* — if the Tech Lead's ADR doesn't
fit it, the PRD goes back for re-shaping. Don't fudge the
appetite to make the work fit; the appetite is a deliberate
constraint.

## Success metrics

How the team will know this shipped well. Two to four metrics —
ideally a mix of leading (engagement, adoption) and lagging
(retention, revenue). Specific enough that "did this work?" is
answerable in 30-90 days post-ship.

## Dependencies

Other ADRs, other PRDs, other repos, other teams whose work this
depends on or affects. List them as `affects:` / `depends_on:`
front-matter entries; cross-link inline where context helps.

## Open questions

What the PRD authors couldn't resolve before publishing. The
Tech Lead phase often reduces this list; remaining items become
ADR `## Alternatives` candidates or follow-up RFCs.

## Decision needed

The single decision the Tech Lead is being asked to make.
*"Do we X or Y?"* Concrete enough that the resulting ADR's
`## Alternatives` is a meaningful comparison.

The corresponding ADR(s) will land at `wiki/<repo>/adrs/<slug>.md`.
