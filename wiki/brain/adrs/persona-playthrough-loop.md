---
title: "Playthroughs are executed skills with immutable transcripts; synthetic findings are confidence-capped insights"
kind: decision
status: accepted
updated: 2026-07-12
confidence: medium
sources:
  - ../prds/persona-playthrough-loop.md
  - ../../../sources/conversations/2026-07-12--persona-playthrough-loop.md
---

# Playthroughs are executed skills with immutable transcripts; synthetic findings are confidence-capped insights

**Decision.** The playthrough loop lands as methodology, not
mechanism-code: a `playthrough` skill (protocol) plus four authored
persona files, riding surfaces the kernel already ships. A
playthrough is a real execution — the agent runs the product's
actual commands and fetches its actual pages while narrating as one
persona from `.claude/personas/users/`; a transcript with no real
output is invalid by protocol. Transcripts snapshot to
`sources/playthroughs/` (immutable, additive-only like every
source). Findings worth a human decision become `kind: insight`
pages on the insights shelf with the persona in
`affected_personas`; smaller frictions stay in the transcript. Two
structural rules distinguish synthetic from human signal: insight
pages born from playthroughs cite `sources/playthroughs/` (the
provenance is the marker), and they are capped at
`confidence: low` until a human — cold-start tester, operator, or a
real user report through `/feedback` — confirms the pattern. The
release prompt is deterministic: the existing inbox-refresh op
gains a version cursor (`wiki/_state/playthrough-cursor.json`) and
queues one `playthrough-<version>` inbox item when `VERSION`
advances past it; `/tend` digests the item by running the sweep
in-session. No LLM runs on any schedule, unchanged.

## Context

Three ad-hoc persona walks caught real defects in one week
(composer autofocus, markdown rendering, the stale-rebuild
regression), and each time the protocol, provenance, and routing
were improvised. The kernel already ships the insights shelf, the
personas convention, the inbox, and `/promote`; the missing piece
is the loop through them and a guard against the two failure modes
of synthetic testing — simulation theater (imagined output) and
self-confirmation (the product's author role-playing its user too
generously). The 1.0 gate's cold-start human test needs a scenario
script regardless; the cold-start persona's playthrough scenario is
that script.

## Alternatives

- **Skill + personas + version-cursor producer, confidence-capped
  insights** *(chosen)* — pure methodology; every moving part is an
  existing surface; the honesty rule is structural (path +
  confidence), not behavioural.
- **A `brain.py playthrough` subcommand orchestrating the run** —
  mechanism-code for what is inherently agent judgement (walking a
  product as a character); would need an LLM in the loop to be
  useful, which the queue-and-tend decision forbids on schedules
  and makes redundant in sessions. Rejected.
- **A dedicated `wiki/playthroughs/` shelf** — separates findings
  from the insights machinery (`/promote`, affected-personas
  views) that already does the graduation work; a second
  feedback-shaped shelf invites drift. Rejected — the transcript
  is the playthrough artefact, the insight is the finding.
- **Do nothing (keep playthroughs ad hoc)** — three catches in a
  week argue the practice earns structure; ad hoc means no
  provenance and no release prompt, so the practice decays when
  attention moves. Rejected.

## Consequences

- **Opens** a repeatable pre-human QA pass: every version bump
  queues a sweep; releases get walked before strangers arrive.
- **Opens** the 1.0 cold-start test's script: the cold-start
  adopter scenario is authored once and reused by the human run.
- **Costs** discipline around the confidence cap — downstream
  consumers must keep treating playthrough-born insights as
  hypotheses; the cap is enforced by convention and validated by
  provenance citation, not by a hard gate in the validator (a
  future gate is cheap to add if drift appears).
- **Retains** queue-and-tend intact: the producer only queues; the
  sweep runs in whatever interactive session tends it.
