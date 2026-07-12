---
title: "Persona playthrough loop — synthetic users walk every release; findings become insights, never facts"
kind: pitch
status: superseded
superseded_by: brain/prds/persona-playthrough-loop.md
updated: 2026-07-12
appetite: small
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-12--persona-playthrough-loop.md
  - ../../org/operator-lessons.md
---

# Persona playthrough loop

Pre-bet pitch per the operator's 2026-07-12 question: should
user-group testing through personas and playthroughs become a
distinct, apparent part of the brain? Graduated same-day on the
operator's bet ("shape it and then build it").

## Problem

The brain has no repeatable way to see itself through a user's
eyes. Persona playthroughs have already earned their keep three
times — the 0.12.1 sweeps caught the composer-autofocus and
markdown-rendering bugs, and the 0.14.2 screenshot walk caught the
stale-rebuild regression — but each run was ad hoc: no protocol, no
provenance, no routing for what was found, and nothing that
prompts the next sweep when a release ships. Meanwhile the product
is approaching shareability (MIT license, cold-start README, 1.0
gate) and the cost of shipping friction a synthetic walk would
have caught in minutes keeps rising. The insights shelf and the
personas folder exist in the kernel but sit empty and unconnected
in this repo — the pieces of a feedback loop with no loop through
them.

## Appetite

Small — a skill, a template, four persona files, one deterministic
producer, and a schema note. The mechanism reuses the insights
shelf, the inbox, `/promote`, and the personas convention as they
stand. If it grows past that (dashboards, scoring, simulated
cohorts), it has left its appetite.

## Solution

Fat-marker shape, four pieces. **Personas:** the brain-as-product
gets its own `users/` set — the cold-start adopter, the daily
operator, the non-terminal PM, the security reviewer — each with
goals and frustrations concrete enough to walk a scenario from.
**The playthrough protocol:** a `/playthrough <persona>
[<scenario>]` skill that *executes* the scenario against the
running product (real commands, real pages — never imagined
output), narrating as the persona, then snapshots the transcript
to `sources/playthroughs/` and routes each finding to
`wiki/insights/` as `kind: insight`, `confidence: low`, affected
personas set. **The prompt:** a producer queues one
playthrough-sweep inbox item per shipped version bump, so every
release gets walked before a human ever trips on it. **The honesty
rule:** synthetic findings are hypotheses — an insight born from a
playthrough cannot rise above `confidence: low` until a real human
(cold-start tester, operator, or user report via `/feedback`)
confirms it; the graduation path to initiatives stays `/promote`.

## Rabbit holes

- **Simulation theater** — an agent *imagining* what a persona
  would see instead of running the product. The protocol must
  demand real execution and cite real output; a playthrough with no
  command output or screenshot in its transcript is invalid.
- **Self-confirmation** — the same model authoring the product and
  playing its user will be generous. The persona files need real
  frustrations and the skill needs an explicit "what would make
  this persona give up?" beat to counteract it.
- **Insight inflation** — dozens of low-confidence insights nobody
  reads. Findings below a friction threshold stay in the
  transcript; only patterns worth a human decision become insight
  pages.

## No-gos

- No synthetic finding ever presented as user feedback — the
  provenance (`sources/playthroughs/`) and the confidence floor
  make the distinction structural.
- No new serving surface, no schedule that runs an LLM — the
  producer queues; sessions play through.
- No replacement of the 1.0 cold-start human test — this loop
  *prepares* scenarios for it; it cannot satisfy it.
