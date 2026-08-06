---
title: Attention relevance model — how the board decides what deserves a day
kind: reference
status: living
updated: 2026-08-04
confidence: low
summary: >-
  The metric the attention board ranks by: four components scored per card, multiplied by a category weight declared in brain.config.yml. This page owns the reasoning and its dated revisions; the numbers live in configuration so a bad weight is a config error rather than a silent scoring bug. The shipped weights are a starting position, not a finding.
sources:
  - ../../brain.config.yml
  - .claude/skills/attention/SKILL.md
enola_intent:
  page:
    type: reference
    status: living
    origin:
    - repo
---
# Attention relevance model — how the board decides what deserves a day

The board ranks cards so that two unlike things — a failing pipeline
and an unread piece of research — can be compared honestly. This page
is the metric. Read it before scoring; never score from memory, because
the whole point is that it is maintained.

**The split is deliberate.** The category names and their weights live
in `brain.config.yml`, where they are diffable, testable, and settable
without editing prose — and where a malformed weight is a loud
configuration error rather than a quiet scoring defect. The
*reasoning* lives here, along with a dated trail of what changed it.
A weight explained here that no longer exists in configuration is
drift, and that visibility is the point.

## The components

Each card is scored on four components, then multiplied by its
category weight.

- **Impact** (0–5) — how much changes if this is handled well, or
  goes unhandled. A production surface serving real traffic scores
  above an internal convenience.
- **Urgency** (0–5) — how much worse this gets by waiting. Something
  actively failing is urgent; something that will still be true next
  month is not, however important.
- **Value** (0–5) — what handling it is worth relative to the effort
  it takes. This is where a cheap fix to a moderate problem beats an
  expensive fix to a slightly larger one.
- **Confidence** (0.5–1.0) — how much the signal is to be trusted.
  Corroboration is the main lever: something observed independently
  through two channels scores higher than a single passing mention.
  A measured failure outranks a remark.

**Effort** is recorded as a band (small / medium / large) rather than
scored. It informs Value rather than competing with it, and recording
it separately keeps the board honest about what it is asking for.

## Why a category weight at all

Without weights, the board would rank a broken deploy and a stale wiki
page on the same scale and quietly favour whichever produced a louder
signal. The weight encodes *what this brain is for*, so the comparison
stays meaningful across kinds of work. Every card takes exactly one
category; an item spanning several takes the highest-weighted one it
touches, never a blend.

Watch the distribution as much as the individual scores. Several
`off-surface` items reaching the top tier does not mean the board is
wrong — it means the operator's real work is not reaching the
channels, and that observation is itself worth a card.

## The shipped defaults, and why they are provisional

The kernel ships five deliberately generic categories, chosen to
discriminate in *any* organisation rather than to describe one:
`breakage` above `commitment` above `signal` above `upkeep`, with
`off-surface` lowest.

The ordering encodes one claim: **a thing that is broken now outranks
a thing that was promised, which outranks a thing that is merely
newly known, which outranks the brain's own housekeeping.** That
ordering is defensible in the abstract and will be wrong for some
brains — a research-heavy brain may well want `signal` above
`commitment`. Replace them. Keep `off-surface` so that signal outside
the remit has somewhere honest to go instead of being dropped.

These weights have **not been calibrated against a real board**. No
connector is configured on the reference machine, so every number here
is a starting position argued from first principles rather than a
finding. Treat the first month of overrides as the real evidence.

## How this page changes

One override is noise. **Two overrides in the same direction in the
same category** mean the weight no longer matches the evidence: revise
the number in configuration, write the reason here, and add a dated
line below. That loop is the point — the metric is supposed to get
better at describing this organisation as the brain ingests more, and
it only does that if each groom writes back what it learned.

## Revisions

- **2026-08-04 — first cut.** Four components, five default
  categories, weights argued from first principles and uncalibrated.
  Ships with the board; expected to move once a real board has run for
  a week.
