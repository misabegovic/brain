---
title: Operator-side surface for attention calibration
kind: initiative
status: superseded
superseded_by: brain/state.md
updated: 2026-07-12
team: brain
division: "(inferred)"
repos:
  - brain
appetite: small
confidence: medium
summary: >-
  The Viktor playthrough found the judge/grade calibration loop works
  end-to-end but is hard to operate: grading requires knowing the item
  id (no pending-grades list), and a single grade renders as "100%
  verdicts graded useful" with no sample size. Suggestion: a
  pending-grades surface and a sample-size-aware calibration stat so
  the loop is legible enough to actually use.
sources:
  - sources/playthroughs/2026-07-12--viktor-daily-operator--daily-loop.md
  - ~/projects/brain/ui/src/pages/dashboard.astro
  - .claude/skills/tend/SKILL.md
---

# Operator-side surface for attention calibration

**Graduated + delivered 2026-07-12** — this began as an agent-authored suggestion from a persona playthrough and was reviewed, approved, and shipped in PR #9. The synthesis below (originally written in inference mode) is retained as the record of the finding; the fix is live on `main`.

## Why the agent suggests this

The Viktor daily-operator playthrough (transcript above, 0.19.3)
exercised the attention loop end-to-end — add, judge, grade,
calibration file. The agent-side half is well built: verdicts are
durable on the item JSON, grades land in the attention-grades state
file, and the tend rules require reading calibration before
judging. The operator-side half is thin, on two observed points.
First, grading requires knowing the item id — no command or surface
lists verdicts awaiting a grade, so once an item is cleared, an
ungraded verdict disappears from every list the operator reads and
the calibration loop starves silently. Second, the dashboard
renders the grade ratio as a bare percentage with no sample size:
the playthrough's single test grade rendered as "100% verdicts
graded useful". A five-grade history showing 80 percent wears the
same confident face as a five-hundred-grade history.

This is inference from one synthetic walk; no human operator has
reported the grading loop starving.

## Inferred objective

If the calibration loop had an operator-side surface — a
pending-grades view and sample-size-honest stats — the
useful/noise feedback that the attention system depends on would
keep flowing, and degradation of verdict quality would become
visible before it erodes trust (the persona's stated kill
condition is roughly three wrong verdicts).

## Affected personas (agent-inferred)

- [Viktor — daily operator](../../../../.claude/personas/users/viktor-daily-operator.md) —
  the grader; his calibration keeps the Needs-you band honest. The
  human reviewer should validate whether operators grade in the
  moment (making a pending list unnecessary) or after the fact.

## Now / Perceived / Target (agent's read)

- **Now** — grading works only by id; nothing enumerates ungraded
  verdicts; the dashboard stat is a bare percentage computed from
  however many grades exist (observed at n=1 in the playthrough,
  2026-07-12).
- **Perceived** — the presentation-layer ADR and the tend skill
  describe the grade loop as the operator's calibration channel;
  the pages are consistent with a belief that mentioning the grade
  command when surfacing a needs-operator item is enough to sustain
  it. Whether that holds in practice is unknown without human
  input.
- **Target (hypothesis)** — ungraded verdicts are enumerable and
  visible where the operator already looks; grade statistics carry
  their sample size; a degrading verdict trend is noticeable within
  a few grades.

## Scope (suggested)

- A way to list verdicts awaiting a grade (CLI first; optionally a
  small briefing/dashboard affordance), including verdicts on items
  already cleared.
- Sample-size-honest stat rendering (counts alongside or instead of
  a bare percentage at low n).
- Keep grades append-only in the existing state file.

## No-gos (suggested)

- No gamification, streaks, or grade nagging — a single quiet list,
  not a demand.
- No change to the judge-side rules or verdict taxonomy.
- No automatic demotion mechanics driven by grades in this
  initiative — calibration input stays advisory to the tending
  agent.

## Rabbit holes (suggested)

- Retention: how long a cleared item's verdict stays gradeable
  before it ages out of the pending list.
- Where the pending-grades affordance lives in the UI without
  adding a fourth briefing band.

## Appetite (estimated)

Small — the data already exists in item JSONs and the grades file;
the work is enumeration, one CLI subcommand shape, and stat
rendering. Estimate is technical-complexity only.

## Suggested success metrics

- An operator can find every ungraded verdict without knowing any
  item id.
- No grade statistic renders without its sample size.
- Calibration file keeps accumulating grades after items clear
  (the loop does not starve when grading is deferred).

## Open questions for the human reviewer

- Do operators actually defer grading, or is grade-in-the-moment
  (as the tend skill nudges) sufficient in practice?
- Is the dashboard the right home for the calibration stat at all,
  or should it live only where verdicts are shown?
- Does this overlap with in-flight briefing/UI work the agent
  doesn't know about?
- Is appetite plausible given current capacity?

## Suggested next step

**Iterate.** The pending-grades enumeration feels load-bearing; the
stat rendering is a smaller companion fix. A human should confirm
the deferred-grading premise before graduating.

## Sources

- sources/playthroughs/2026-07-12--viktor-daily-operator--daily-loop.md
  (observed grade flow, attention-grades.json content, dashboard stat at n=1)
- ui/src/pages/dashboard.astro (percentage computation, read 2026-07-12)
- .claude/skills/tend/SKILL.md § Attention judgement (read 2026-07-12)
- .claude/personas/users/viktor-daily-operator.md (three-wrong-verdicts kill condition)
