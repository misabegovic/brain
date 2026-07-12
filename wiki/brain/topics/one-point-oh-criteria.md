---
title: "What must be true before 1.0 — when is the tool ready to instance elsewhere?"
kind: topic
status: living
updated: 2026-07-10
confidence: medium
summary: >
  The five 1.0 criteria: instance birth in the test suite (done), seven unattended days, a real-data loop in a born instance, a cold-start human test, all gates green at tag.
sources:
  - ../../../sources/conversations/2026-07-10--instancing-and-one-point-oh.md
---

# What must be true before 1.0 — when is the tool ready to instance elsewhere?

## Question

The operator's frame: this repo dogfoods itself until "we are happy
with the outcome," then real projects get their own instances. What,
concretely, is *happy*? Without criteria, 1.0 is a mood.

## Discussion

- **2026-07-10** (`by: claude (fable 5)`) — proposed five criteria,
  each observable: (1) **birth works** — `init --full` produces an
  instance whose own gates pass, executable as a suite test
  (shipped with 0.11); (2) **a week runs itself** — seven
  consecutive unattended timer days with clean schedule runs and a
  sensibly-populated inbox; (3) **one full loop on real data** — a
  connector batch → inbox item → `/tend` → synthesis commit citing
  the snapshot, in a born instance; (4) **cold-start onboarding** —
  someone who isn't the operator reaches a working setup from the
  README and onboarding deck alone; (5) **green at tag time** — all
  detectors, all tests, zero dangling references. Tag `1.0.0` when
  all five hold.

- **2026-07-12** (`by: claude (fable 5)`) — the operator delegated
  criterion 4's execution: "I don't want to point anyone to
  anything. You do it." Executed as a full tutorial walk against a
  born instance with a real OSS repo (transcript:
  `sources/playthroughs/2026-07-12--delegated-cold-start--instance-tutorial.md`),
  which also demonstrated criterion 3 (real-data loop in a born
  instance: birth → setup → ingest → gates → commit → search →
  tend). Two defects fixed en route. Honesty note kept explicit:
  criterion 4 is satisfied by *operator-delegated agent execution*,
  not by an independent human — the trail records the delegation.

## Outcome

**Adopted 2026-07-10** (operator directive "go on all" covering
this settlement): the five criteria above are the 1.0 gate,
referenced from the roadmap. Criterion 1 passed the day it was
written; 2–4 require calendar time and a real project's instance —
which is the point.
