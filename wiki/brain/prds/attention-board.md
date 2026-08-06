---
title: An attention board — what deserves the operator's day, not what is left to do
kind: initiative
status: living
updated: 2026-08-04
team: brain
division: "(inferred)"
repos:
  - brain
appetite: medium
confidence: medium
summary: >-
  The kernel collects and queues but has never triaged. A daily
  /attention pass produces a capped, ranked board of what deserves the
  operator's day, stored beside the inbox rather than inside it — cards
  are dismissed, queue items are done. Channels and categories come from
  brain.config.yml so a fresh shell gets an honest board that fills in
  as connectors are configured.
affects:
  - brain
depends_on:
  - brain/adrs/queue-and-tend-inbox.md
sources:
  - ~/projects/brain/brain.config.yml
  - ~/projects/brain/brain-schedule.yml
  - ~/projects/brain/.claude/skills/tend/SKILL.md
  - ~/projects/brain/wiki/brain/adrs/queue-and-tend-inbox.md
  - ~/projects/brain/.claude/skills/attention/SKILL.md
  - ~/projects/brain/wiki/brain/adrs/attention-board.md
  - ~/projects/brain/wiki/brain/attention-relevance-model.md
enola_intent:
  page:
    type: initiative
    status: living
    scope:
    - brain
    affects:
    - brain
    origin:
    - repo
    relations:
    - rel: depends-on
      to: wiki/brain/adrs/queue-and-tend-inbox.md
    anchors:
    - repo: brain
      path: .claude/skills/attention/SKILL.md
    - repo: brain
      path: .claude/skills/tend/SKILL.md
    - repo: brain
      path: brain-schedule.yml
    - repo: brain
      path: brain.config.yml
    - repo: brain
      path: wiki/brain/adrs/attention-board.md
    - repo: brain
      path: wiki/brain/adrs/queue-and-tend-inbox.md
    - repo: brain
      path: wiki/brain/attention-relevance-model.md
---
# An attention board — what deserves the operator's day, not what is left to do

Product Requirements Document for `wiki/brain/prds/attention-board.md`.

## Objective

Give a brain operator a daily board of the few things most worth
doing next, ranked from signal the brain already collects, so that
opening the brain answers *"what should I work on today?"* instead
of *"what is still in the queue?"*.

## Background

The kernel already collects and already queues. Six scheduled
connectors pull from GitHub, Notion, Slack, Datadog, Langfuse and
the code-shape substrate into immutable snapshots under
`sources/<connector>/`; deterministic producers accumulate pending
synthesis work into `wiki/_state/inbox/`, and `/tend` digests that
queue inside a supervised session. Both halves work.

Neither answers the operator's actual first question of the day.
The inbox is a queue by construction — items are digested and
cleared, and its honest end state is empty. That makes it a good
record of *what is outstanding* and a poor answer to *what matters
most right now*, because a queue cannot tell the operator that one
of forty items is worth displacing today's plan for. `/tend`'s own
budget grammar (`/tend 3`, `/tend 15m`) is the tell: the operator is
already asking for a subset, and the tool can only offer them the
first N in priority order.

Meanwhile a sibling brain has run a board of this shape daily for
long enough to learn what breaks. The lessons that transfer are
mostly negative ones — a board that accepts everything becomes a
second backlog, an unexplained ranking is an untrustworthy ranking,
and a channel that fails silently makes the board lie by omission
rather than by error. Those lessons are about the *mechanism* and
carry to any brain. What does not carry is that brain's channel
list, its four categories, and its scoring weights, all of which
encode one team's remit at one company.

The kernel is org-agnostic by contract — `brain.config.yml` exists
precisely so the code stays content-agnostic, and the connector
registry there is already the declarative channel abstraction this
work needs. The gap is not collection. It is **triage**.

## Affected personas

- [`viktor-daily-operator`](../../../.claude/personas/users/viktor-daily-operator.md)
  — the primary owner. Viktor opens the brain at the start of the
  day and currently has to reconstruct priority himself: read the
  inbox, remember which connector snapshots moved, and hold the
  cross-channel joins in his head. He experiences this work as a
  short briefing he can act on immediately, where each line says
  what changed and what to run, and where the absence of a line is
  itself trustworthy. The value is that the first ten minutes of
  his day stop being triage.
- [`noor-cold-start-adopter`](../../../.claude/personas/users/noor-cold-start-adopter.md)
  — secondary. Noor adopts the shell for an organisation the kernel
  has never heard of. She must get a board that is *empty and
  honest* on day one rather than one pre-populated with another
  company's categories, and it must fill in as she configures
  connectors, without her editing a skill file.

## Now / Perceived / Target

- **Now.** Connectors pull into `sources/<connector>/` on a
  schedule (`brain-schedule.yml`); producers queue synthesis work
  into `wiki/_state/inbox/`; `/tend` drains it. There is no ranking
  surface, no notion of a card that can be dismissed without being
  done, and no place where cross-channel signal is joined into one
  addressable item. `brain.py` has no `attention` subcommand — the
  three `"attention"` strings in it belong to an unrelated
  verdict-grading field.
- **Perceived.** The presence of `wiki/brain/prds/attention-calibration-operator-surface.md`
  makes it look as though the kernel has an attention surface. It
  does not: that PRD is superseded and concerns the judge/grade
  calibration loop — the same word for a different thing. Anyone
  reading the shelf for prior art will find a false positive.
- **Target.** A daily `/attention` pass produces a capped, ranked
  board stored at `wiki/_state/attention/` and rendered for humans
  and agents. Channels and categories come from
  `brain.config.yml`, so a fresh shell yields an honest empty board
  and a configured one yields a briefing. Every card names a
  repository and a change, carries the components of its score, and
  can leave the board by being dismissed rather than only by being
  done.

## Scope

A `/attention` skill that grooms a card store the operator owns,
plus the mechanical half that refreshes it from what the brain has
already collected. Channels are whatever the operator has
configured as connectors — the board reads their snapshots and
never re-implements their fetching. Categories and their weights
are operator-declared, with one built-in escape category for
signal outside the brain's remit. Each card carries a tier, a
one-sentence reason naming what changed, a runnable command, and
the scoring components behind its rank. The board is capped, and
items that cannot become work leave it. A rendered view makes the
board readable by agents and by humans, and the whole thing
degrades to a named skip — never a silent one — for every channel
that is absent, unconfigured or unreachable.

## No-gos

- **Not a second inbox.** The board never becomes the place
  outstanding work accumulates; `/tend` keeps that job. If an item
  belongs in a queue it goes to the queue.
- **No new fetching.** The board reads connector snapshots. It does
  not add API clients, credentials, or pull logic — a channel the
  kernel cannot already pull is out of scope until a connector for
  it exists.
- **No borrowed-organisation content.** Nothing from the reference
  implementation's own domain travels into kernel files — no named
  companies, teams, products, channels or categories. The shipped
  default category set must make sense to an organisation the
  kernel has never seen.
- **No execution.** The board proposes; it never runs a card's
  command itself.
- **No mutation of other people's work.** Reading a colleague's PR
  or message informs a card's reason; it is never a card's action.
- **No UI work** in this cut, and no write-back mirror to any
  external system.

## Rabbit holes

- **Building a scoring engine.** The ranking is a small weighted
  judgement recorded on the card, not a framework. If it starts
  growing a rules DSL, stop and re-pitch.
- **Unifying inbox and board storage.** They were deliberately kept
  separate. Attempting to merge the two stores mid-build means the
  no-backlog invariant is being traded away without a decision.
- **A connector-per-channel expansion.** Discovering that a useful
  channel has no connector is a *finding*, not licence to write one
  inside this work.
- **Perfecting the weights.** Shipping a calibration loop that
  learns weights from overrides is explicitly the "big" appetite
  this PRD did not take.

## Appetite

Medium. The mechanism is understood and has a working reference
implementation to learn from, so the cost is not discovery — it is
the careful separation of mechanism from configuration, which
touches a config schema, a small command surface, the state and
view scaffolding, and a skill of real length. Small would force
hardcoded categories and no config schema, which reproduces exactly
the coupling this work exists to remove. Big would add a UI and a
weight-learning loop before anyone has run the board for a week,
which is the wrong order.

## Success metrics

- A fresh `brain.py init` shell yields an empty, honest board with
  no organisation-specific content — verifiable by a test.
- On a configured brain, a groom produces a briefing where every
  card names a repository and a change, and every command runs
  without editing.
- Every channel that did not answer is named as skipped in the
  briefing; no groom ever silently shrinks the board.
- The board stays capped over repeated grooms rather than growing —
  the failure mode being measured is "this became a backlog".

## Dependencies

- [`queue-and-tend-inbox`](../adrs/queue-and-tend-inbox.md) — the
  board sits beside this, reads from it, and must not absorb it.
- The connector registry in `brain.config.yml` and the `*-pull`
  operations in `brain-schedule.yml` are the board's inputs.
- No sibling-repo dependencies; this is brain-scope work.

## Open questions

- Whether inbox items should appear as cards at all, or only
  influence the reason on a card sourced elsewhere. Treating the
  queue as one input among several is assumed here, but the
  duplication risk is real.
- Whether the relevance model ships as a page the operator edits or
  as config, given that its revisions are prose and its weights are
  data.
- What the built-in default categories should be such that they
  are meaningful to an unknown organisation without being so
  generic they stop discriminating.
- Whether a skipped channel should ever suppress a card that
  depends on it, or only annotate it.

## Decision needed

Given a separate card store fed from existing connector snapshots,
**how should channels, categories and weights be declared so the
kernel carries the mechanism and the operator carries the
content** — and what is the minimum a brand-new shell must have
configured before `/attention` produces something worth reading
rather than an empty page?

The corresponding ADR lands on the brain-scope `adrs/` shelf under
this PRD's own slug, once Phase 1 is approved.
