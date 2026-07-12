---
title: Producer death as first-class health, not a notice
kind: initiative
status: superseded
superseded_by: brain/state.md
updated: 2026-07-12
team: brain
division: "(inferred)"
repos:
  - brain
appetite: small
confidence: medium
summary: >-
  The Viktor playthrough found a dead accumulation timer renders "queue
  clear" identically to a tended-clean queue, and the timer warning is
  flattened in with "UI deps missing" — clear-because-tended and
  clear-because-the-producer-is-dead are indistinguishable. Suggestion:
  treat producer/timer death as a first-class health state that
  qualifies the queue-empty claim.
sources:
  - sources/playthroughs/2026-07-12--viktor-daily-operator--daily-loop.md
  - tools/brain.py
---

# Producer death as first-class health, not a notice

**Graduated + delivered 2026-07-12** — this began as an agent-authored suggestion from a persona playthrough and was reviewed, approved, and shipped in PR #9. The synthesis below (originally written in inference mode) is retained as the record of the finding; the fix is live on `main`.

## Why the agent suggests this

The Viktor daily-operator playthrough (transcript above, 0.19.3)
observed that a dead accumulation timer is reported by doctor as a
warning on the same tier as missing UI dependencies, and that the
workbench strip flattens all warnings into an undifferentiated
notice count while simultaneously rendering "queue clear". The
observed strip output with a dead timer was "− 4 notice · queue
clear". The playthrough suggests this combination reads as calm
precisely when the queue-and-tend loop has stopped accumulating —
clear-because-tended and clear-because-the-producer-is-dead render
identically. Viktor's persona file names exactly this as a give-up
point: a health surface that stays reassuring while the timer has
been dead for days.

This is inference from one synthetic walk; no human operator has
reported being misled by the strip.

## Inferred objective

If the health surfaces treated producer/timer death as a
first-class state — distinct from generic warnings, and qualifying
the queue-emptiness claim — the daily operator's glance would stay
trustworthy through the exact failure mode that silently defeats
the queue-and-tend loop.

## Affected personas (agent-inferred)

- [Viktor — daily operator](../../../../.claude/personas/users/viktor-daily-operator.md) —
  the morning glance is his primary interface; his stated
  frustration is "drift — timers silently dead" and a strip that
  stays calm through it. The human reviewer should validate that
  real operators glance rather than run doctor daily.

## Now / Perceived / Target (agent's read)

- **Now** — doctor reports the missing timer as one of several
  same-tier warnings; the strip renders "− N notice · queue clear"
  and the briefing carries no producer-liveness signal at all
  (observed in the playthrough, 2026-07-12).
- **Perceived** — the queue-and-tend ADR records "the timer
  accumulates, sessions digest" as the operating rhythm; the
  brain's pages are consistent with a belief that doctor warnings
  are sufficient visibility. Whether the org believes the strip is
  honest about timer death is unknown without human input.
- **Target (hypothesis)** — a strip and doctor that distinguish
  "the accumulation machinery is alive" from all other health, and
  that qualify queue-emptiness when the producer cannot have run
  recently (for example, "queue clear — but nothing has accumulated
  since <date>").

## Scope (suggested)

- Doctor tiering: a dead/never-installed timer on a configured,
  in-use brain escalates beyond the generic warn tier, or gains a
  distinct visual class.
- Strip semantics: the queue-emptiness phrase is qualified by
  producer liveness (last successful producer run timestamp is
  already derivable from state files).
- Briefing orientation: optionally surface last-accumulation time.

## No-gos (suggested)

- No new daemons or monitoring infrastructure — liveness is derived
  from existing state-file timestamps.
- No change to the queue-and-tend division of labour (no LLM on the
  schedule).
- No notification/alerting channel — this is about the honesty of
  the surfaces the operator already reads.

## Rabbit holes (suggested)

- Defining "dead" for operators who legitimately run producers by
  hand (no timer installed by choice); a fresh-shell instance should
  not nag. The unconfigured-shell case observed in the playthrough
  is arguably correct to keep at warn tier.
- Deciding liveness from mtimes across worktrees and clones could
  produce false alarms — the deciding signal needs care.

## Appetite (estimated)

Small — the signals exist (doctor checks, state-file mtimes, the
strip's status endpoint); the work is tiering and phrasing, plus
tests. Estimate is technical-complexity only.

## Suggested success metrics

- A brain with a dead timer and an empty queue never renders an
  unqualified "queue clear".
- Timer death is distinguishable from other warnings at a glance on
  both doctor output and the strip.
- No new nagging on unconfigured shells or hand-run setups.

## Open questions for the human reviewer

- Is the affected persona real and the framing accurate — do
  operators glance at the strip rather than run doctor?
- Should timer death be a doctor *fail* (exit 1) on a configured
  brain, or a distinguished warn?
- Does this overlap with in-flight health/strip work the agent
  doesn't know about?
- Is "last accumulation time" the right qualifier, or is a simple
  liveness badge enough?

## Suggested next step

**Iterate or graduate.** If the framing holds, graduate with the
tiering decision made; if operators in practice run doctor daily,
reject with a note on the transcript's finding.

## Sources

- sources/playthroughs/2026-07-12--viktor-daily-operator--daily-loop.md
  (observed doctor output, strip rendering logic, status endpoint payload)
- tools/brain.py (doctor checks, inbox-refresh producer, and the
  workbench strip rendering served from the same file; read 2026-07-12)
- .claude/personas/users/viktor-daily-operator.md (frustrations list)
