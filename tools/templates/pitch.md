---
title: <one-line pitch name — the shaped proposal, e.g. "Trigger system → composable workflow engine">
kind: pitch
status: draft                       # draft | living | superseded | archived
updated: YYYY-MM-DD
team: <owning / proposing team or focus team>
division: <division>
appetite: <small | medium | big>    # how much time the team would spend IF they bet on it
repos:
  - <scope repo>
confidence: low                     # pitches are pre-bet; start low
sources:
  - <pitch source — Notion URL snapshot, conversation, customer feedback, prior art>
# superseded_by:                    # filled in on a bet → the epic/PRD this pitch became
---

# <one-line pitch name>

Shape Up **pitch** for `wiki/<scope>/pitches/<slug>.md` — a
**pre-bet** shaped proposal. A pitch frames a problem, sets an
appetite, and sketches a solution at *fat-marker* fidelity so a
betting table can weigh it. It is the **one artifact kind allowed
to show the solution — including engineering/architecture shape —
at deliberately rough fidelity** (epics forbid engineering bets;
PRDs avoid dictating *how*). See
[`wiki/brain/adrs/shape-up-pitches.md`](../../brain/adrs/shape-up-pitches.md).

> **Author guidance — fat-marker, not blueprint.**
>
> - **Sketch, don't specify.** Show enough shape to bet on; leave
>   the details a future ADR will commit deliberately open. Name
>   models, flows, and components in prose; breadboard the moving
>   parts — but don't paste schemas, code, or final interface
>   definitions. (Architecture *shape* is welcome; frozen
>   architecture is an ADR's job, post-bet.)
> - **Honest about unknowns.** A pitch that hides risk doesn't help
>   the betting table. Rabbit holes and no-gos are first-class.
> - **Pre-bet.** A pitch proposes; it does not commit the team.
>   On a bet it graduates → an **epic + children** (umbrella) or a
>   **PRD + ADR(s)** (single); mark this pitch `superseded` with
>   `superseded_by:` pointing at what it became.

## Problem

The concrete problem, grounded in a real situation — not an
abstract desire. What's broken or missing today, for whom, and
what does it cost them? Cite the sources (code, incidents,
feedback, prior art) the same way a PRD would. The reader should
feel the problem before seeing any solution.

## Appetite

How much is this worth — the time budget the team *would* spend if
it bet on this (`small` / `medium` / `big`, with the rough
calendar sense). The appetite constrains the solution: it's a
spending limit, not an estimate. A big-appetite *exploration* is a
legitimate appetite (survey the space) — say so.

## Solution

The shaped solution at **fat-marker fidelity**. This is the
pitch's heart and its privilege: sketch the approach, the key
elements, and how they fit — breadboards (places + affordances +
connections) and rough sketches in prose. For technical pitches,
this is where the architecture shape lives (the models, the
flow, the building blocks) — rough enough to leave room, concrete
enough to bet on. Make the shape legible; resist freezing details.

## Rabbit holes

The places this could go wrong or balloon — technical unknowns,
tricky cases, tempting-but-out-of-scope detours. Naming them is
how the pitch declares them handled-or-avoided, so they don't
sink the work after a bet.

## No-gos

Explicit boundaries: what this pitch is *not* doing, and what a
bet on it must not break. Anything deliberately excluded to keep
the appetite honest.
