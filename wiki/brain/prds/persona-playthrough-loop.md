---
title: "Persona playthrough loop — every release gets walked by synthetic users; findings route to insights below the human-confirmation line"
kind: initiative
status: living
updated: 2026-07-12
confidence: medium
supersedes: brain/pitches/persona-playthrough-loop.md
sources:
  - ../pitches/persona-playthrough-loop.md
  - ../../../sources/conversations/2026-07-12--persona-playthrough-loop.md
---

# Persona playthrough loop

Graduated from the [pitch](../pitches/persona-playthrough-loop.md)
on the operator's 2026-07-12 bet.

## What

A first-class product-testing loop inside the brain: authored user
personas for the brain-as-product, a `/playthrough` protocol that
executes a scenario against the running product as a chosen persona,
immutable transcripts under `sources/playthroughs/`, findings
routed to `wiki/insights/` as low-confidence insight pages, and a
deterministic producer that queues a playthrough sweep whenever a
version ships. One structural honesty rule binds it: synthetic
findings are hypotheses, distinguishable from real user feedback by
provenance and capped at `confidence: low` until a human confirms.

## How

Fat-marker (the ADR names the bet): four persona files in
`.claude/personas/users/` (cold-start adopter, daily operator,
non-terminal PM, security reviewer); a `playthrough` skill that
demands real execution — commands actually run, pages actually
fetched — narrates as the persona including the "when would I give
up?" beat, snapshots the transcript, and writes insight pages only
for findings worth a human decision; a version-cursor producer
inside the existing inbox-refresh op that queues one sweep item per
shipped `VERSION` bump; and a routing-table line in the schema so
ingest knows playthrough findings belong on the insights shelf.

## Why

Three ad-hoc playthroughs already paid for the mechanism (composer
autofocus, markdown rendering, the stale-rebuild regression) — the
loop makes that luck structural. The product is approaching
strangers (MIT, cold-start README, the 1.0 gate's human test);
synthetic walks catch the friction that would burn a real tester's
patience, and the persona scenarios double as the script the real
cold-start test will follow. The honesty rule keeps the insights
shelf trustworthy: the brain must never mistake its own role-play
for its users' voice.

## Now

Shipped 2026-07-12 with the bet: four personas authored, the
`playthrough` skill and command live, `sources/playthroughs/`
receiving transcripts, the version-cursor producer queueing sweeps,
and the schema routing line landed. First dogfood playthrough run
against 0.15.0/0.16.0 in the shipping session.

## Perceived

The risk the pitch names: playthrough findings could be read as
user feedback by a future consumer that ignores provenance. The
confidence cap and the `sources/playthroughs/` path are the
structural guards; the perception gap closes only if downstream
skills (`/promote`, views) keep respecting them.

## Target

Every version bump is followed by at least one tended playthrough
sweep before the next slice starts. When the 1.0 cold-start human
test runs, its script comes from the cold-start adopter's scenario,
and its findings land through the same insights shelf — human-
confirmed, so free to rise past `confidence: low`. Longer horizon:
adopting organisations author their own `users/` personas and the
loop tests *their* product the same way.
