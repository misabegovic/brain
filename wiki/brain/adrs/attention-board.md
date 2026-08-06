---
title: "The attention board is a ranked, capped store beside the inbox: per-connector readers behind one card shape, weights in config and rationale on a page"
kind: decision
status: accepted
updated: 2026-08-04
confidence: low
summary: >
  A daily attention board gets its own card store beside the inbox — cards are dismissed, queue items are done. The groom reads connector snapshots directly through a thin per-connector reader, each emitting one uniform candidate shape, with the inbox as the universal fallback so a connector without a reader is degraded rather than invisible. Category weights live in brain.config.yml; the reasoning and its dated revisions live on a wiki page. An unconfigured shell still produces a board from internal producers and names how many connectors answered.
depends_on:
  - brain/adrs/connector-snapshot-contract.md
  - brain/adrs/queue-and-tend-inbox.md
sources:
  - ../prds/attention-board.md
  - ../../../brain.config.yml
  - ../../../brain-schedule.yml
  - .claude/skills/tend/SKILL.md
enola_intent:
  page:
    type: decision
    status: accepted
    origin:
    - repo
    relations:
    - rel: depends-on
      to: wiki/brain/adrs/connector-snapshot-contract.md
    - rel: depends-on
      to: wiki/brain/adrs/queue-and-tend-inbox.md
---
# The attention board is a ranked, capped store beside the inbox: per-connector readers behind one card shape, weights in config and rationale on a page

Phase 2 ADR for the attention-board PRD, which carries the same slug
on the brain-scope `prds/` shelf.

## Context

The kernel collects and queues but has never triaged. Connectors are
pull-only snapshot-writers under one contract — immutable dedup-keyed
files into `sources/`, a cursor in state, an inbox item per new batch,
never a wiki write — and `/tend` digests the resulting queue in a
supervised session. The PRD establishes that a queue cannot answer
*what deserves today*, because its honest end state is empty and it
has no way to say which of forty items is worth displacing a plan for.

Three constraints shaped what follows, all discovered in pre-flight
rather than assumed.

**The inbox is already the connector-agnostic surface.** Because every
connector queues an inbox item per batch, the queue is a uniform
notification channel over heterogeneous systems. Anything that reads
only the inbox is automatically channel-agnostic — and automatically
limited to whatever the producer chose to summarise.

**No connector is configured on the reference machine.** `sources/`
holds conversations, playthroughs, research and web material; there is
no `github/`, `slack/`, `notion/`, `datadog/` or `langfuse/`
directory, and every connector entry in configuration is empty. The
design must therefore be judged against a shell where the board's only
live input is internal producers, because that is the only state it
can currently be observed in.

**The kernel is org-agnostic by contract.** Configuration exists
precisely so code stays content-agnostic, and the reference
implementation this work learns from encodes one team's channels,
categories and weights directly in its skill text. Porting the text
would port the coupling.

## Decision

**The board is a card store of its own, beside the inbox, and the two
never merge.** Cards leave the board by being dismissed; queue items
leave the inbox by being done. This is the invariant the whole design
protects: a board that can only be emptied by doing everything on it
is a second backlog, and the reference implementation's hardest-won
rule is that a growing board is a failing board.

**The groom reads connector snapshots directly, through a thin
per-connector reader.** Each reader observes exactly one connector's
snapshot format and emits one uniform candidate shape — a summary, the
repository and change it implies, the snapshot path as evidence, and
whatever timestamps allow recency to be judged. The board itself never
learns a connector's format; it consumes candidates. This is the
operator's chosen bet, taken over reading the inbox alone, because
joining across channels on underlying facts is the capability that
makes a board better than a queue, and joins on producer summaries are
joins on someone else's compression.

**The inbox is the universal fallback, not a competing input.** A
connector with no reader still reaches the board through the inbox
item it already queues. This is what keeps the coupling bounded:
adding a connector never makes it invisible, it only makes it shallow
until a reader exists. Absent that fallback, the reader set would
become a gate on visibility, and every new connector would be a
silent hole in the board.

**Category names and weights are configuration; the reasoning is a
page.** Weights are read from the brain's configuration file, so they
are diffable, testable and settable without editing prose, and a
malformed weight is a configuration error rather than a scoring bug.
The rationale — why a category is weighted as it is, and a dated trail
of revisions when overrides accumulate — lives on a relevance-model
page the operator edits. The kernel ships the mechanism and a
deliberately small default category set; it ships no organisation's
categories.

**Scoring components are stored on the card, never just the result.**
A rank that cannot be explained is a rank that will not be trusted,
so each card carries the components behind its score alongside the
score, and any judgement that moves a card off its computed position
carries a written reason. Silent overrides are forbidden.

**An unconfigured shell still produces a board.** Internal producers
queue inbox items with no connector configured, so a fresh adopter
gets something useful on day one, and the briefing states how many
connectors answered out of how many are configured. Every channel that
did not answer is named. *"Nothing was found"* and *"nothing was
asked"* must never render identically — the same rule the brain
already applies to its graph substrate and its skip lines.

**The board proposes and never executes.** Cards carry a runnable
command; running it is the operator's deliberate act.

## Alternatives

- **Rank the inbox in place, no second store.** One store, zero
  duplication, and the existing queue tooling reused wholesale.
  Rejected by the operator at Phase 1: the inbox is a queue by
  construction, and overlaying tiers on it conflates *must drain*
  with *worth doing today* until the no-backlog rule becomes
  unenforceable.
- **Read the inbox only, never the snapshots.** The simplest design
  and the most naturally channel-agnostic — the board would need no
  per-connector knowledge at all. Rejected by the operator: batch-level
  summaries cap the board's granularity, and the cross-channel joins
  that justify a board over a queue would be performed on summaries
  rather than facts. The cost accepted in exchange is the per-connector
  reader set, contained as described above.
- **Compute the board on demand and persist only dismissals.** Nothing
  can drift from its sources. Rejected at Phase 1: tier, reason and
  score continuity between days is what lets the board say *what is
  new*, and tombstones need a store regardless, so the saving is
  smaller than it appears.
- **Everything in configuration, including scoring rationale.** A
  single machine-readable source. Rejected: calibration reasoning would
  have nowhere durable to live, and *"why is this weighted as it is"*
  would be answerable only from commit history.
- **Everything on a wiki page, including weights.** Matches the
  reference implementation and makes calibration an ordinary wiki
  edit. Rejected: parsing weights out of prose is brittle, and an
  operator typo would become a silent scoring defect instead of a
  loud configuration error.
- **Do nothing.** The inbox and `/tend` already work, and operators
  can keep reconstructing priority themselves. Rejected because the
  reconstruction is exactly the daily cost the brain exists to remove,
  and `/tend`'s own budget grammar shows operators already asking for
  a subset the tool cannot rank.

## Consequences

- **The board carries per-connector knowledge, and that is a real
  cost knowingly accepted.** The reader set is the one place the
  kernel stops being channel-agnostic. It is contained by three
  properties: a reader is small and observes exactly one connector,
  every reader emits the same candidate shape, and a connector
  without a reader degrades to its inbox item rather than
  disappearing. If the reader set starts growing per-connector
  scoring, per-connector categories, or anything beyond
  normalisation, the containment has failed and the decision should
  be revisited rather than patched.
- **Two stores must stay conceptually distinct.** The temptation to
  merge them will recur, because they overlap in what they read. The
  PRD names merging mid-build as a rabbit hole; this ADR names the
  test — if a card can only leave the board by being done, the
  invariant has already been lost.
- **Weights and rationale live in two places and can drift.** The
  mitigation is that the page owns the reasoning and the
  configuration owns the numbers, so drift is visible as a page that
  explains a weight the configuration no longer carries. Making the
  page authoritative would trade this for brittleness.
- **The design is unproven against live connector data.** No
  connector is configured on the reference machine, so the reader
  interface will first be exercised against internal producers alone.
  The first configured connector is the real test of whether one
  candidate shape is sufficient, and it should be treated as such
  rather than as routine.
- **A fresh adopter gets a board built from housekeeping.** Ranking
  half-life crossings and link-health findings as though they were
  attention-worthy risks teaching a new operator to ignore the board.
  The named connector count is the counterweight: the briefing says
  what it is working from, so a thin board reads as *not yet
  configured* rather than as *nothing matters today*.
- **The board never becomes a schedule-driven surface.** It is
  groomed inside a supervised session like `/tend`, so nothing
  accumulates unattended and no unattended process decides what the
  operator sees first.

## Linked PRD

The Phase 1 PRD carries this ADR's slug on the brain-scope `prds/`
shelf and was approved 2026-08-04.

- ../prds/attention-board.md

## Build notes

- **Phase 2 authored 2026-08-04.** Three decisions were the
  operator's, taken at the Phase 2 gate: snapshots read directly
  rather than the inbox alone, weights in configuration with
  rationale on a page, and an unconfigured shell producing a board
  from internal signal rather than refusing. The snapshot-reading
  bet was taken against the option's own stated cost; the
  per-connector reader plus universal inbox fallback is this ADR's
  attempt to bound that cost rather than to argue with it.
