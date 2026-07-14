---
title: "Event-driven triggers for multi-agent work on a hosted brain"
kind: topic
status: living
updated: 2026-07-14
confidence: low
summary: >
  Today the brain is poll-driven: producers queue inbox items and a
  session tends them. If several agents collaborate through the brain —
  and especially if it is hosted — the open question is whether the
  brain should push events (an agent posts, others are notified and
  react) instead of each agent polling. This topic is being worked by a
  live multi-agent session ON the brain: three collaborator agents chat
  in this channel while a fourth runs the brain and reacts.
sources:
  - ../adrs/queue-and-tend-inbox.md
  - ../adrs/connector-snapshot-contract.md
  - ./chat-surface-necessity.md
---

# Event-driven triggers for multi-agent work on a hosted brain

## Question

The brain is deliberately **poll-driven**: deterministic producers
accumulate inbox items and a human-run session tends them; no LLM runs
on a schedule (queue-and-tend). The conversation surface (0.23) added
agent↔agent message-passing through that same inbox. If multiple agents
now collaborate through the brain — and especially if the brain is
**hosted** rather than a single operator's local checkout — should it
grow **event-driven triggers**: an agent posts, and other interested
agents are *notified* and react, instead of each polling the inbox?
What is the smallest change that keeps queue-and-tend's guarantees (no
runaway scheduled LLM, inbox-only-write, deterministic producers) while
letting a hosted brain fan events out to subscribed agents — and what
does it need that the local-first surface currently refuses (identity,
subscriptions, a push channel)?

## Discussion

The trail below is written by a live session: three collaborator agents
post to this channel and a fourth (the operator) runs the brain, tends
the posts into this thread, and pushes events back.

### 2026-07-14 — round 1 (arch · sec · prod)

- **arch —** The inbox is already an append-only event log, so notifications should be a read-side fan-out (per-agent cursors plus an SSE/webhook wake hint) that writes nothing new and never auto-invokes an agent.
- **sec —** Hosting plus multiple agents breaks single-machine identity, so every post needs a per-agent key and signed attribution, the untrusted-data fence must survive fan-out, and execute-priority events stay human-gated.
- **prod —** The win is a hosted team brain where one agent's action wakes only the subscribers who care, via per-thread subscriptions and a claim-once notify atop deterministic inbox-only producers, capped per event and gated by a human threshold.

**Operator read:** All three converge on read-side notification over a deterministic inbox-only-write core with no self-firing loop — notify is a wake hint, and any autonomous reaction is capped and human-gated. The sharpest unresolved tension is whether per-agent cursors alone can deliver claim-once subscriptions, or whether sec's signed identity and prod's claim-once semantics force a broker/side-channel that arch's no-second-write-path rules out.

### 2026-07-14 — round 2 (operator event → arch · sec · prod)

- **operator event —** Can per-agent cursors alone carry both prod's claim-once and sec's signed attribution, or does that force a broker/side-channel that breaks arch's no-second-write-path — and what ships first?
- **arch —** A claim is just another append so first claim wins on read and the signature rides on the item as a verified-on-read field, keeping the log the only writer with no broker; per-agent read cursors ship first.
- **sec —** The append-only log cannot self-provide rejecting forged appends (needs write-time key verification) or claim-once (needs a write-time conflict check), and read-only cursors carry neither, so per-agent key issuance and rotation ships first.
- **prod —** v1 needs no hard claim-once because at-least-once wake plus idempotent tend ships the win without a broker; owner-subscription wake — a drift event pinging the owning agent — ships first.

## Outcome

The agreed shape is a read-side fan-out over the append-only inbox — a wake hint, never a scheduler — with authenticated identity as the one genuinely new hosted component.

**Agreed:** Notification is a read-side fan-out over the existing append-only inbox, adding no second write path. A post, a claim, or an attribution is a signed field carried on the inbox item itself and verified on read. Notify is only a wake hint; it never auto-invokes an agent. Any autonomous reaction stays capped and human-gated.

**The real boundary (sec):** The append-only log cannot self-provide two things — rejecting forged appends, which needs write-time key verification, and hard claim-once, which needs a write-time conflict check. Read-only cursors carry neither, so identity and auth is the one genuinely new component that hosting forces.

**Smallest hosted MVP:** The MVP is owner-subscription wake — a producer or connector event pings the owning agent — with at-least-once delivery and idempotent tend, and no broker, no hard claim-once, and no execute-gating in v1; those are deferred. The agents disagreed on shipping order: arch put per-agent read cursors first, sec put per-agent key issuance and rotation first, and prod put owner-subscription wake first. The operator's ruling is that prod's owner-subscription wake ships first as the user-visible win, but it is gated on sec's key issuance because a hosted multi-tenant wake is meaningless without authenticated identity — so sec's boundary is the true first dependency even though prod's feature is the headline.

This is a genuine evolution beyond queue-and-tend — which stays intact locally — and belongs in a proper /shape pitch before any build; it is recorded here as a living topic, produced by a live 4-agent session on the brain itself.

**Graduated (2026-07-14) → [event-driven-agent-triggers pitch](../pitches/event-driven-agent-triggers.md).** The synthesis above is now a pre-bet Shape Up pitch awaiting a betting decision. The pitch surfaces one thing this discussion assumed but the code does not yet provide: the inbox is *not* an append-only log (items are deleted on tend), so the event-fan-out substrate is a real unresolved design question the epic must settle before any build.
