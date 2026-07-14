---
title: "Event-driven triggers for multi-agent work"
kind: epic
status: living
updated: 2026-07-14
team: brain kernel
division: "(brain)"
repos:
  - brain
confidence: low
summary: >
  Bet-on umbrella (2026-07-14) for an event-driven backbone: an agent's
  action wakes the agents who care via a read-side fan-out over the
  brain's existing records — a wake hint, never a scheduler — so
  queue-and-tend holds. Children in dependency order: per-agent identity
  first (the one new component hosting forces, also resolves the
  event-fan-out substrate since the inbox is not append-only), then
  owner-subscription wake with at-least-once delivery + idempotent tend.
sources:
  - ../pitches/event-driven-agent-triggers.md
  - ../topics/event-driven-multi-agent.md
  - ../adrs/queue-and-tend-inbox.md
  - ../adrs/connector-snapshot-contract.md
---

# Event-driven triggers for multi-agent work

Umbrella for the bet placed 2026-07-14 on the
[event-driven-agent-triggers pitch](../pitches/event-driven-agent-triggers.md)
(now superseded by this epic). The pitch graduated from a topic a live
four-agent session produced on the brain itself. Epics carry no
umbrella ADR pair — the decisions live in the children.

## Objective

Give the brain an **event-driven backbone for multi-agent work**: an
agent's action wakes the agents who care, instead of every agent
polling the inbox — without re-introducing the scheduled autonomous
loops the brain deliberately deleted. Delivered in dependency order:
authenticated per-agent identity first, then owner-subscription wake.
The success shape is a hosted team brain where a connector's drift
event pings the owning agent, that agent tends it on its own next
turn, and queue-and-tend's guarantees (no scheduled LLM,
inbox-only-write, deterministic producers) still hold.

## Background

The brain is poll-driven by design and correct for one operator at a
local checkout. Two gaps break it for multiple hosted agents, both
confirmed against the code during the pitch's deepdive:

- **No per-agent identity.** The conversation surface stamps a single
  machine identity on every post. Hosted and multi-agent, posts are
  unattributable and there is no boundary that could reject a forged
  event. This is the true first dependency — a multi-tenant wake is a
  spoofing surface without it.
- **The inbox is not an append-only log.** The topic assumed it was;
  in fact inbox items are deleted on tend. So the event-fan-out
  substrate — what agents subscribe to and read cursors over — is a
  genuine unresolved design question, not a free reuse. It is resolved
  inside child 1 (or a short spike) before child 2 builds on it.

The agreed architecture from the topic: notification is a **read-side
fan-out** over records the brain already writes; a wake is a hint that
never auto-invokes an agent; identity and claims ride on the event
item, verified on read. That keeps queue-and-tend intact.

## Affected personas

- [Viktor — daily operator](../../../.claude/personas/users/viktor-daily-operator.md)
  owns both the win (a hosted team brain that pings the owning agent on
  drift) and the risk (a chatty event bus burning tokens with no human
  in the loop — the thing he would turn off).
- The **autonomous agents** are the second audience: they authenticate,
  subscribe, are woken, and react on their own next tend.

## Scope

In the umbrella:

- A minimal **per-agent identity** layer: issue and rotate per-agent
  keys, sign events, reject forged appends. Enough to authenticate and
  attribute — no more.
- The **event-fan-out substrate** decision (retained event stream vs
  fan-out over the audit log vs tombstoned inbox items) and per-agent
  read cursors over it.
- **Owner-subscription wake**: subscribe to a thread, repo, or
  producer; a matching event wakes the subscriber over a dumb push
  channel that carries a wake, not a payload. At-least-once delivery;
  correctness from idempotent tend.
- A **hosted, authenticated, writable tier** distinct from today's
  read-only serving mode.

## No-gos

- **No scheduled LLM.** The wake is a hint; it never auto-invokes an
  agent. Autonomous reactions stay capped per event and human-gated for
  anything execute-priority. Queue-and-tend's core line does not move.
- **No second write path.** Fan-out is read-side over records the brain
  already writes; identity and claims ride on the event item.
- **No unauthenticated multi-tenant.** Owner-subscription wake does not
  ship before per-agent identity.
- **No claim-once broker, no full IAM, no execute-auto in v1.** These
  are deliberately deferred; at-least-once + idempotent tend is the
  cheaper answer, minimal keys are the identity answer.
- **Local-first stays unchanged.** Additive and opt-in for the hosted
  deployment; a single operator's loop gains no new moving parts and no
  daemon.

## Children

- [Per-agent identity for a hosted brain](../prds/per-agent-identity.md)
  — *draft* (the first dependency; also resolves the event-fan-out
  substrate).
- **Owner-subscription wake** — *not yet spawned* (built on identity;
  the headline win).

Children spawn via forward `/shape` with `parent_epic:
event-driven-agent-triggers`; this list gains a link and a status as
each PRD lands.

## Success metrics

- A connector's drift event reaches the owning agent **without that
  agent polling** — the poll-to-push win, observed end to end.
- A forged or unsigned event is **rejected** at the auth boundary.
- **No scheduled LLM** is added; the local-first loop is byte-for-byte
  unchanged when the hosted tier is off.
- Reaction cost is **bounded per event** — no runaway token spend, no
  standing autonomous loop (Viktor's abandon-trigger stays untripped).
