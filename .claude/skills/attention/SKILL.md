---
name: attention
description: Groom the attention board — the daily ranked shortlist of what deserves the operator's day, built from connector snapshots and the inbox. Load when the user says "attention", "the board", "what should I work on", "morning briefing", "groom the board", or invokes /attention. The judgement half of the collect-and-groom loop per wiki/brain/adrs/attention-board.md.
---

# attention — groom the board

The mechanical half (`brain.py attention refresh`) owns existence and
plumbing: which candidates exist, where their evidence lives, what is
new and what has gone. **This skill owns the judgement** — tier,
category, why, command, the score and the components behind it — and
the prune.

Never hand-edit the fields the collector writes; it will overwrite
them on the next refresh.

## What the board is, and is not

The board answers *what deserves today*. The inbox answers *what is
outstanding*. They are different questions with different exits:

- **A card leaves the board by being dismissed.** It stops mattering,
  and saying so is a decision the collector then respects forever.
- **A queue item leaves the inbox by being done.** `/tend` owns that.

So the board is **not a backlog**. Its output is a handful of things
worth displacing today's plan for — not everything that could be done.
A growing board is a failing board. If an item has no plausible next
action it is knowledge, not attention: route it to a wiki edit or the
inbox and drop it.

## Protocol

### 1. Refresh mechanically first

```bash
python3 tools/brain.py attention refresh
```

Read the resulting store. The line it prints — *"N of M connectors
answered"* — is load-bearing: a thin board on a brain with no
connectors configured means *not yet configured*, while a thin board
with all connectors answering means *a calm day*. Never let those two
read alike, in the board or in your briefing.

### 2. Group candidates into addressable items

Raw candidates are not cards. Collapse every mention of one
addressable thing into a single card: an error spike, the thread
discussing it, the failing build and the change that fixes it are
**one** item, not four. Grouping is also where corroboration is
counted — something seen independently through two channels carries
higher confidence than a passing mention in one.

Write each card as something that could be *done* ("decide whether to
adopt X"), never as a topic ("X").

### 3. Apply the two tests

Every surviving card must pass both:

- **The repo test.** Can you name the repository and roughly what
  changes there? The channels are evidence; the repo change is the
  card. Signal that cannot become a change in a repository is not a
  card.
- **The substitution test.** Would a different operator of this brain
  still care tomorrow? If the only reason is "you left this
  half-finished", it is not attention.

Discard anything that fails either. Tool and channel maintenance, and
the brain's own housekeeping, are the cheapest signal to collect and
will otherwise fill a board that looks busy while proposing no work.

### 4. Categorise and score

Assign exactly one **category** from `brain.config.yml`. An item
spanning categories takes the highest-weighted one it touches, never a
blend. Anything outside this brain's remit takes `off-surface` — kept
visible, because a board full of off-surface cards tells the operator
their real work is not reaching the channels, which is itself worth
knowing.

Score from the components the relevance model defines, multiply by the
category weight, and **store the components alongside the score**:

```bash
python3 tools/brain.py attention set <id> \
  --tier now --category <category> \
  --why "<one line naming what changed — a date, a number, a deadline>" \
  --command "</runnable command with no placeholders>" \
  --score <n> --components '{"impact":…,"urgency":…,"value":…,"confidence":…}'
```

A rank nobody can explain is a rank nobody will trust. *"Why is this
fourth?"* must always be answerable from the card.

### 5. Rank, cap, and justify every override

Sort by score. The top band becomes `now` — capped at
`now_tier_size`; the next band `next`; the rest `watch`. You may move
a card off its computed position, but then `--override-reason` is
required. Silent overrides make the whole ranking untrustworthy.

If a sixth card genuinely belongs in `now`, demote one and say so.
Never widen the tier.

### 6. Feed overrides back into the model

One override is noise. Two in the same direction in the same category
is a weight that no longer matches the evidence — revise
`wiki/brain/attention-relevance-model.md`, cite what moved it, and add
a dated line under its `## Revisions`. The metric is supposed to get
better as the brain ingests more, and it only does that if each groom
writes back what it learned.

### 7. Prune

```bash
python3 tools/brain.py attention prune
```

Drops done and gone cards past a week and tombstones past ninety days.
If the active count is over `max_active`, the board is hoarding —
demote or dismiss until it is honest again.

### 8. Render and surface

```bash
python3 tools/brain.py views
```

Then read `wiki/_views/attention.md` once as the operator would. Every
card must answer *why today?* and *what do I run?*.

**End with the `now` tier verbatim** — title, why, command per card.
The groom's output *is* the briefing. Never end with "board updated".
State which connectors answered and which did not, so the operator can
weigh the board's coverage; a briefing built on one of seven channels
is still useful, but only if it says so.

## Degradation

A channel that is unconfigured, unreachable or absent **never blocks
the groom**. Groom from what answered, and name what did not. Two hard
rules: never present stale data as current, and never let a missing
channel silently shrink the board — *"no cards from X"* and *"X was
unreachable"* mean opposite things.

## What this skill is NOT

- **Not `/tend`.** That drains the queue; this ranks what matters.
  This skill never marks inbox items done.
- **Not an executor.** It never runs a card's command. The operator
  picks a card deliberately.
- **Not a collector.** It adds no API clients and no credentials. If a
  useful channel has no connector, that is a finding to record, not a
  licence to write one here.
- **Not scheduled.** Like `/tend`, it runs inside a supervised
  session, so nothing decides what the operator sees first unattended.

## Done check

- [ ] Refresh ran before any judgement.
- [ ] Zero `untriaged` cards remain among active ones.
- [ ] Every card names a repository and a change; every card passes
      the substitution test.
- [ ] Every card carries a category, a score, and the components
      behind that score.
- [ ] `now` holds no more than `now_tier_size`; every override carries
      a reason.
- [ ] Overrides were weighed against the relevance model, and a
      revision was either made with a dated line or consciously
      declined.
- [ ] Every command runs without editing.
- [ ] Prune ran; the active count is within `max_active`.
- [ ] Views regenerated; the `now` tier was surfaced verbatim with the
      connector coverage stated.
