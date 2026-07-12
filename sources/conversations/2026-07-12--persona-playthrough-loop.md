---
title: "Conversation capture: user-group testing through personas and playthroughs"
kind: source
captured: 2026-07-12
participants: operator (Muhamed), claude (fable 5)
context: >
  Immediately after the 0.15.0 terminal removal. The operator asked
  whether persona-driven playthrough testing should become a
  distinct, apparent part of the brain for collecting product
  feedback.
---

# Conversation capture — persona playthrough loop (2026-07-12)

**Operator:** "ok. what do you think about user group testing
through personas and playthroughs? should we make this a distinct
and apparent part of the brain? to collect feedback on the product"

**Agent position (summarised):** strong yes, with one honesty
caveat. Two different things must not be conflated: (1) *synthetic
playthroughs* — the agent plays a persona and actually executes a
scenario against the running product — are already proven in this
repo (the 0.12.1 persona sweeps caught the composer-autofocus and
markdown-rendering bugs; the 0.14.2 screenshot playthrough caught
the stale-rebuild regression). They find friction and defects
cheaply, but they produce *hypotheses*, not user feedback — an LLM
role-playing a user cannot generate evidence about what users feel.
(2) *Real user testing* — the 1.0 gate's cold-start criterion —
remains the only source of actual feedback; personas structure the
recruiting and the scenario scripts but never substitute.

Proposed mechanism (small — the brain already owns most pieces):
author the brain's own user personas (cold-start adopter, daily
operator, non-terminal PM, security reviewer); a `/playthrough
<persona> <scenario>` skill that executes the scenario for real,
snapshots the transcript to `sources/playthroughs/`, and routes
findings to `wiki/insights/` at `confidence: low` with affected
personas set; a producer hook queueing a playthrough sweep on each
version bump; and one honesty rule — synthetic insights can only
reach `confidence: medium+` when a human playthrough or real user
report confirms them. Survives the deletion test: methodology, not
surface.

**Operator:** "ok, shape it and then build it" — bet placed;
approval covers shaping (pitch → PRD → ADR) and the build.
