---
title: "Self-maintenance is queue-and-tend: deterministic producers accumulate a per-item inbox; synthesis digests in-session via /tend — never on a schedule"
kind: decision
status: accepted
updated: 2026-07-10
confidence: high
sources:
  - ../../../sources/research/2026-07-10--hub-adr-verification.md
  - ../../../sources/conversations/2026-07-10--self-hosting-roadmap-intent.md
  - .claude/skills/tend/SKILL.md
  - ../../../brain-schedule.yml
---

# Self-maintenance is queue-and-tend: deterministic producers accumulate a per-item inbox; synthesis digests in-session via `/tend` — never on a schedule

**Decision.** The brain's self-maintenance loop splits along the
deterministic/model line. Everything deterministic — sibling cursor-diff
detection, half-life crossings, link-graph health, connector batch arrival,
operator-defined observations — runs on a **local timer** for free and
accumulates pending work as one JSON item per file under
`wiki/_state/inbox/`. Everything that needs a model — synthesis, grooming
judgement, research — runs **inside the operator's normal interactive
session** via the `/tend` skill, surfaced by a one-line session-start
summary. No LLM is ever invoked on a schedule.

## Context

The operator's self-maintenance intent (captured 2026-07-10) collided with
a hard constraint raised in the same conversation: model access is
interactive terminal sessions only; scheduled headless runs bill per-run
and are out. The first roadmap sketch had assumed scheduled agent
invocation; the operator rejected that direction explicitly.

The reframe that resolved it: autonomy does not require scheduled
inference. The brain's operations already split cleanly into observation
(deterministic, already largely built as schedule ops and reflection
detectors) and synthesis (the model half). What was missing was a durable
seam between them — a queue that survives between sessions, that any
producer can write to and one skill drains. Three properties were
load-bearing. The queue must be **merge-safe** (two producers or two
checkouts must never conflict), which the per-effort-file registry
precedent already solved: one file per item. It must be **idempotent for
producers** (a cron job re-running hourly must not spam duplicates), which
a producer-chosen dedup id gives — re-adding an existing id is a no-op,
and the refresh op reconciles its own items so cleared triggers disappear.
And it must be **open**: an operator-defined producer is any script that
calls the inbox-add command, registered as one more schedule entry — the
schedule file's handler field is already arbitrary shell, so customisation
costs one YAML block and no kernel changes.

The runner is a local timer (systemd user timer, cron fallback) rather
than CI cron, because the sibling repos exist only on the operator's
machine — CI can neither compute cursor diffs nor pull from
locally-authenticated connectors. Latency of "next time the operator sits
down" matches the stated nothing-urgent posture, and digestion inside a
visible session makes every synthesis run implicitly supervised — the
governance rail's human gates are reached *earlier*, not bypassed.

## Alternatives

- **Queue-and-tend** *(chosen)* — deterministic accumulation on a free
  local timer; in-session digestion via one skill; per-item files;
  producer-chosen dedup ids; open producer contract.
- **Scheduled headless agent runs** — the original sketch: cron invokes
  the agent, work lands as PRs on the governance rail. Architecturally
  sound but rejected by the operator on cost: per-run billing for a
  personal harness inverts the economics, and the operator's model access
  is session-based.
- **Digest-at-session-start automatically** — same queue, but the agent
  drains it unprompted whenever a session opens. Rejected: it taxes every
  session's context and startup with work the operator may not want right
  then; a one-line summary plus an explicit `/tend` keeps the operator in
  charge of when the model half runs.
- **One shared inbox file** — matches the older single-file state shape
  but recreates the merge-conflict problem the efforts registry already
  solved with per-item files. Rejected.
- **Local small models for scheduled synthesis** — free inference via a
  local model on the timer. Rejected for the synthesis path (quality is
  the product; weak synthesis is the failure mode that defeats the brain);
  remains open as a future triage-only experiment (classification,
  batch summarisation) feeding better inbox items.
- **Do nothing** — self-maintenance stays fully manual; the operator
  re-derives "what needs attention" each session. Rejected: that
  re-derivation is exactly the deterministic work a timer does better.

## Consequences

- **Closes** the invocation question for 0.2: no scheduled LLM runs,
  ever; the timer is deterministic-only. A future deployment that wants
  true unattended synthesis opts into the PR rail explicitly — tend-mode
  and PR-mode are the same skills under different governance toggles.
- **Closes** the queue shape: per-item JSON files, committed (arrival and
  clearing are git-audited), dedup ids, refresh-op reconciliation for
  machine-produced items, operator items never touched by reconciliation.
- **Opens** the producer ecosystem: connectors (the 0.3 arc) and
  operator-defined observations join by writing items, with no kernel
  change. The inbox is the single seam every future input flows through.
- **Opens** budget-bounded digestion (`/tend 15m`, `/tend ingest`) as the
  operator's control over how much of a session the brain consumes.
- **Costs** freshness: knowledge lands when the operator next works, not
  when the trigger fired. Accepted — it matches the harness's posture and
  a personal brain's stakes.
- **Costs** one more state surface to keep honest; mitigated by the
  refresh op's reconciliation and by clearing items in the same commit as
  their synthesis, so a stale queue is visible in the diff.

## Build notes

Shipped as decided: `brain.py inbox add|list|summary|done` with slug-
validated dedup ids and upsert preserving arrival dates; the
`inbox-refresh` schedule op producing cursor-diff / half-life /
link-health items with full reconciliation of its own; a session-start
hook printing the summary line; `tools/install-timer.sh` (systemd user
timer at 06:15 with `Persistent=true` catch-up, crontab line printed as
fallback); a documented producer template at
`tools/producers/example-producer.sh` plus a disabled schedule entry to
copy. The one refinement over the sketch: refresh-owned items are
reconciled as a *set* (added, refreshed, and cleared each run) rather
than only appended, so machine items never go stale in the queue.
