---
title: Give recurring tend-queue items an operator acknowledgement path
kind: decision
status: suggested
ai_suggestion: true
updated: 2026-07-12
repos:
  - brain
confidence: low
summary: The viktor-daily-operator playthrough demonstrated that a half-life tend item cleared with inbox done is re-added on the next producer run, and the only ways to silence it falsify page metadata. This suggests the queue needs an acknowledgement that sticks — a re-verified signal the producers respect — before the daily timer turns the inbox into a cries-wolf machine.
sources:
  - sources/playthroughs/2026-07-12--viktor-daily-operator--agent-sweep.md
---

# Give recurring tend-queue items an operator acknowledgement path

> **AI-suggested ADR.** Does **not** reflect a human-approved
> decision and does **not** record current product state or
> upcoming product changes. This page is **agent-authored
> synthesis** of observed patterns from a persona playthrough — a
> *suggestion* for a human to review, iterate on, and either
> graduate (drop the `ai_suggestion: true` flag, change status to
> `accepted`, move the file from `wiki/brain/ai-suggestions/adrs/`
> to `wiki/brain/adrs/`) or supersede with a different framing.
>
> All content below is **inference from observed behaviour, not
> testimony from the deciders**. Treat anything that reads as a
> declarative claim about *why* something was built as hypothesis,
> not fact.

## Context

The queue-and-tend loop's contract (per the queue-and-tend ADR) is
that deterministic producers accumulate the inbox and sessions
digest it. The `inbox-refresh` reconciler upserts machine-produced
items while their trigger holds and removes them once it clears —
by design, so the queue never shows stale machine work.

The viktor-daily-operator playthrough of 2026-07-12 (cited above)
demonstrated the flip side empirically: a half-life item for a
high-confidence page past the 30-day refresh rule was cleared with
the inbox done command and re-added on the very next producer run,
because the trigger — the page's age — still held. The clearing
operator's judgement left no trace the producer respects.

The trap appears structural rather than incidental. The two ways
to make the half-life trigger clear are bumping the page's updated
date — which the schema forbids unless content actually changed —
or demoting its confidence — which is wrong when the page is still
accurate. An operator who re-verifies a page and finds it correct
has no policy-correct way to record that verdict. Every
high-confidence page that ages past 30 days without needing a
content change therefore becomes a daily, unsilenceable flag on
the timer. The daily-operator persona's stated abandonment
threshold is three false positives in a week; with today's seven
high-confidence pages the corpus is on course to cross that
threshold within weeks, deterministically.

Two observations suggest the team is already aware of the failure
mode in adjacent producers: the deepening picker carries explicit
damping (kind exclusions and a seven-day grace period, noted in
source as the "first dogfooding amendment, 2026-07-10"), and the
inbox grade command records useful-versus-noise calibration into
the attention-grades state file. But the reconciler never reads
those grades, and the half-life producer received no damping — the
calibration signal is collected and then ignored by the very loop
it exists to calibrate.

## Inferred decision

No decision exists yet; this suggestion proposes one. The brain
appears to need a first-class "operator acknowledged — trigger
satisfied by human judgement" state that recurring producers
respect, so that clearing a machine-produced item is an act the
machine remembers. The narrowest framing consistent with the
existing design: a re-verified signal on the page (or on the item)
that resets the half-life clock without falsifying the updated
date or the confidence tier.

## Considered options (agent surfacing)

- **A verified-date field on the page** — a frontmatter field
  recording when a human last re-confirmed the page's accuracy,
  distinct from the updated date. The half-life producer measures
  staleness from whichever is later. This keeps the stale-date
  rule intact (updated still means content changed), makes
  re-verification auditable in the page's own history, and gives
  /groom a richer signal. Cost: one more frontmatter field, and
  the validator plus views need to learn it.
- **Grade-aware suppression in the reconciler** *(closest to
  existing machinery)* — the reconciler already has the
  attention-grades file; an item graded noise (or judged routine)
  could be suppressed from re-add for that trigger until the
  trigger's underlying value changes again. No schema change, but
  the suppression lives in tooling state rather than on the page,
  is invisible to the corpus, and conflates "this item was noise"
  with "this page is verified accurate".
- **Snooze on done** — clearing a machine item records a
  suppress-until date; the producer skips re-adding until then.
  Simplest to build, but it defers the nag rather than resolving
  it, and a snoozed lie (a page that really is stale) stays
  invisible for the snooze window.
- **Do nothing** — the implicit baseline. The queue stays honest
  to its triggers but dishonest to operator judgement; the
  observed persona outcome is that the operator stops reading the
  inbox, which defeats the entire accumulation loop.

## Inferred consequences

- **Closes:** the cries-wolf path by which a policy-correct page
  generates a daily unsilenceable flag; the incentive to game the
  updated date (metadata falsification as the only escape hatch).
- **Opens:** an honest re-verification economy — /groom and the
  briefing can distinguish "aged and unexamined" from "aged and
  re-confirmed", which is a better staleness signal than age
  alone; the collected attention grades gain a consumer.
- **Costs:** whichever mechanism is chosen adds one more state the
  producers must reconcile, and a re-verification that is itself
  stale (a page confirmed months ago, wrong today) must eventually
  re-trigger — the half-life applies to the acknowledgement too.

## Open questions for the human reviewer

- Is the stale-date rule ("updated only when content changed")
  intended to be absolute, or was re-verification always meant to
  count as an update? If the latter, option A collapses into
  documentation rather than schema change.
- The grades file is written by inbox grade but read by nothing
  observed in the reconciler — is a consumer already planned, and
  should this decision fold into that work?
- Should the acknowledgement live per-page (verified date) or
  per-item (suppression)? The playthrough suggests per-page,
  since the item is derived and the page is the durable object.
- What is the half-life of an acknowledgement itself — does a
  re-verified high-confidence page re-flag after another 30 days,
  or a longer window?
- The same walk surfaced doctor's operating-mode check matching a
  commented-out boilerplate line and misreporting governance mode
  (transcript step 2) — a one-line fix, but it shares a root
  pattern with this ADR: operator-facing signals diverging from
  the contract's own predicates. Should the graduation of this
  suggestion also mandate that health checks reuse the contract's
  canonical predicates rather than re-implementing them?

## Suggested next step

Iterate, then graduate if the framing holds. The choice among the
three mechanisms is a genuine product decision (schema field vs.
tooling state vs. snooze) that deserves the operator's pick; the
playthrough evidence only establishes that "do nothing" fails the
daily-operator persona on its stated abandonment trigger.

## Sources

- sources/playthroughs/2026-07-12--viktor-daily-operator--agent-sweep.md
  — the persona walk: the empirical done-then-re-added
  demonstration (step 7), the abandonment-threshold arithmetic,
  and the observed damping precedent in the deepening picker.
