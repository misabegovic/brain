---
title: Generated reading lists carry lifecycle status — titles and superseded markers, never bare slugs or undifferentiated rows
kind: initiative
status: superseded
superseded_by: brain/state.md
updated: 2026-07-12
team: "(inferred)"
division: "(inferred)"
repos:
  - brain
appetite: small
confidence: medium
summary: "The Priya playthrough suggests generated reading surfaces undercut the trust promise: the shelf-home Project overview lists superseded ADRs beside the current one with only date chips (two contradictory decision titles, nothing marking which is the record), and the trail's supersedes links render raw slugs as link text. Suggestion: every generated list row carries the page's status, and every cross-reference renders the target's human title."
sources:
  - sources/playthroughs/2026-07-12--priya-non-terminal-pm--reading-journeys.md
---

# Generated reading lists carry lifecycle status — titles and superseded markers, never bare slugs or undifferentiated rows

**Graduated + delivered 2026-07-12** — this began as an agent-authored suggestion from a persona playthrough and was reviewed, approved, and shipped in PR #7. The synthesis below (originally written in inference mode) is retained as the record of the finding; the fix is live on `main`.

## Why the agent suggests this

The Priya (non-terminal PM) playthrough of 2026-07-12 walked the
rendered site read-only and observed two related gaps on generated
reading surfaces. First, the shelf-home Project overview's "Recent
decisions" section rendered four ADRs with only date chips; two of
the four are superseded, and two titles directly contradict each
other ("surfaces are MCP, CLI, and the terminal" beside "surfaces
are MCP and the CLI — the embedded terminal retires") with nothing
on the row marking which is in force. Second, the trail's
supersedes cross-references render raw slugs as link text
("supersedes mcp-cli-terminal-surface", "superseded by state")
where every other surface gives human titles. The transcript
records both with fetched excerpts. This is inference from a
synthetic walk, not user testimony — no human reader has reported
being misled yet.

## Inferred objective

If every generated list row carried the target page's lifecycle
status and every generated cross-reference rendered its human
title, a reading-only user could trust any list on the site as
"current record unless marked otherwise" — the same promise the
trail page and the ai-suggestions banner already keep.

## Affected personas (agent-inferred)

- [Priya — non-terminal PM](../../../../.claude/personas/users/priya-non-terminal-pm.md) —
  her stated trust requirement is that what she reads is the
  approved record; the playthrough suggests the Project overview
  can hand her a superseded decision undistinguished from the
  current one. The human reviewer should validate this reading.

## Now / Perceived / Target (agent's read)

- **Now** — the trail page renders status chips and supersedes
  arrows correctly; the shelf-home Project overview's generated
  "Recent decisions" list renders date chips only, and trail
  supersedes anchors render slugs (observed in the playthrough
  transcript, 2026-07-12, against build 0.19.3).
- **Perceived** — the presentation-layer trail records that
  lifecycle chrome renders "on every card and page"; the brain's
  own onboarding deck tells readers to "trust the banner". The
  overview rows appear to sit outside that guarantee without any
  page recording the exception.
- **Target (hypothesis)** — generated lists and cross-references
  are status-honest and title-first everywhere a human reads.

## Scope (suggested)

The Project overview's generated sections (Recent decisions, Open
work) carry the same kind/status chips the trail rows already
carry; supersedes/superseded-by references on the trail (and any
other generated surface) render the target page's title, with the
slug at most as secondary detail. An audit pass over other
generated list surfaces (role views, home sections) for the same
two properties.

## No-gos (suggested)

No redesign of the trail or overview layout; no change to how
status is stored in frontmatter; no hand-authored content changes
— this is about what the generators render, not what pages say.

## Rabbit holes (suggested)

Deciding whether superseded rows should be hidden rather than
marked (the playthrough suggests marked-not-hidden — the trail's
visible supersede chains read as honesty, not clutter). Title
lookups for dangling supersedes targets could invite fallback
logic; a missing target rendering as a slug is an acceptable
degraded state.

## Appetite (estimated)

Small — the data (status, titles) already exists in the derived
page index; this is a rendering change in a handful of components.
Load-bearing only on the technical-complexity dimension.

## Suggested success metrics

A re-run of the Priya reading-journeys scenario finds no generated
row where a superseded page is indistinguishable from an accepted
one, and no generated cross-reference whose visible text is a slug.

## Open questions for the human reviewer

- Is the affected persona real and the framing accurate?
- Should superseded entries appear (marked) in the Project
  overview at all, or be filtered out?
- Does this overlap with in-flight presentation-layer follow-up
  work the agent doesn't know about?
- Is the appetite plausible given current team capacity?
- Is the suggestion landing in the right scope (brain-meta)?

## Suggested next step

- **Graduate** if the reviewer confirms the overview rows and
  slug anchors are defects against the presentation layer's own
  promise. (Drop `ai_suggestion: true`, status to `living`, move
  to `wiki/brain/prds/`, hand to Tech Lead.)
- **Iterate** if marked-vs-hidden or scope needs a different call.
- **Reject** if the overview is intentionally date-only and the
  distinction is judged adequately carried by the trail.

## Sources

- sources/playthroughs/2026-07-12--priya-non-terminal-pm--reading-journeys.md
  — the walk: fetched excerpts of `/brain/` (Project overview rows
  without status) and `/trail/` (slug anchor text).
- .claude/personas/users/priya-non-terminal-pm.md — the persona's
  trust goals and give-up points.
