---
title: "The way we work — the Shape Up cadence"
kind: reference
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
---

# The way we work — the Shape Up cadence

The organisation runs on a Shape Up adaptation: six-week cycles
separated by **Innovation Week** and **Improvement Week**. There is
no centralized backlog — pitches live with their authors and surface
during cycle planning.

## Cycle rhythm

```
[ 6-week cycle ] → [ Innovation Week ] → [ Improvement Week ] → [ 6-week cycle ] → …
```

Cycles end with a **team retrospective**. Innovation Week ends with a
**demo session**. Improvement Week is bounded by a "bang-for-buck ×
time needed" heuristic — improvements typically take less than a day.

| Week type        | What happens                                                                 |
|------------------|-------------------------------------------------------------------------------|
| Cycle (6 weeks)  | Cycle team works on 1–3 projects with fixed scope. Ends ready-and-deployed.  |
| Innovation Week  | Open ideation; team votes on pitches; winners become work. Ends in a demo.   |
| Improvement Week | Smaller fixes / polish on existing features. Onboarding starts here.         |

The cycle's "definition of done" is the gate; everything must be
deployed within the cycle window.

## Project sizing (the appetite)

| Size            | Appetite                |
|-----------------|--------------------------|
| **Big / Large** | Full six weeks.         |
| **Medium**      | > 2 weeks, < 4 weeks.   |
| **Small**       | A day up to two weeks.  |

Sizing is "appetite" rather than estimate — the time you're willing
to spend, not how long the work will take.

## Backlog policy

**No centralized backlog.** Anyone can write a pitch; the author
keeps their pitch and adds it to the cycle board when the next cycle
opens up. This is by design: it pushes responsibility onto the
authoring team and keeps the brain trust distributed.

Implication for the brain: PRDs and pitches ingested via `/in
<source>` should mostly be tagged as `kind: initiative` (in flight)
or `kind: decision` (the cycle accepted/rejected the pitch). The
brain doesn't reproduce a centralized backlog — it surfaces what
*is* in flight.

## Support model

- **A rotating support team** owns incoming issues, rotating through
  team members each cycle.
- Teams whose support scope differs materially (e.g. an
  integrations-heavy team) run their own dedicated rotation.
- **A recurring tech forum**, open to all product people, handles
  cross-team technical topics.

## "Owning our work" rule

After releasing a project, the team that released it **owns it for
at least one cycle after**. Bugs and issues land back with that
team. The support rotation can assist but doesn't take ownership.

This is the canonical answer to "who gets paged when something
breaks?" — the most recent releasing team.

## Role perspectives

- **Junior engineer** — lands during Improvement Week for a reason:
  low stakes, team has bandwidth. The "bang for buck × time"
  heuristic is the right first lens for picking week-1 tasks.
- **Engineering manager** — this is the cadence to plan around. The
  fixed cycle window plus retro makes velocity measurable
  cycle-over-cycle; "owning our work for one cycle after" defines
  on-call boundaries.
- **Product manager** — pitches live with their authors, not in a
  ticketing backlog. Each cycle is a pitch selection moment; the
  "appetite" framing replaces estimates.
- **Engineering leadership** — the predictable cadence (cycle /
  innovation / improvement) makes capacity planning tractable, and
  "no centralized backlog" is a strong, defensible signal to the
  org.

## The 8-week shaping calendar

The cadence distinguishes **what cycle teams ship** from **what
shapers prepare for the next cycle**. The shaper's calendar runs in
parallel to the cycle, ramping toward the next betting table:

| Week | Shapers focus                                                                          |
|------|-----------------------------------------------------------------------------------------|
| 1    | **Handovers** — cycle start-up meeting; prepare presentation; set up shaping sessions.  |
| 2    | **Breathe and think** — scout pitches for the next cycle; rough outlines of the most important ones. Cycle post goes out. |
| 3    | **Decide on most important pitches** — early betting-table meeting; agree which pitches could form the basis of the upcoming cycle. |
| 4–6  | **Shaping in progress** — team sync about the next cycle near the end of the cycle.     |
| 7    | **Innovation week** — follow up on the previous cycle, reshape if needed; **betting table**. |
| 8    | **Improvement week** — pick up interesting things from innovation week; **final betting table** + set the teams. |

The pitch decision is not a single event at the end of a cycle —
shaping ramps from week 1 to week 8, starting roughly as soon as the
previous cycle started.

## Communication pulse

Beyond cycle retros and the betting-table calendar, the day-to-day
heartbeat that makes the cadence work:

- **Daily check-in** — team-flexible (team channel, video call, etc.).
- **Weekly demos** — once a week during a cycle, each team posts a
  demo update in a shared channel. Purpose is sharing progress for
  feedback, not status reporting.
- **Product weekly** — a fixed weekly slot with an open agenda;
  cancelled if nothing's queued.
- **Release communication** — heads-up to customer-facing teams, a
  user-facing changelog post, and a celebratory org-wide message.

## Pitch council

A small group of senior product people **evaluates pitches for
inclusion in the next cycle** and takes feedback from the rest of
the organisation to keep alignment with company vision and goals.
Betting-table outputs flow through this group.
