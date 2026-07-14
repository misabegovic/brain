---
title: "Owner-subscription wake — the headline agentic win"
kind: initiative
status: superseded
superseded_by: brain/state.md
updated: 2026-07-14
team: brain kernel
division: "(brain)"
appetite: medium
parent_epic: event-driven-agent-triggers
repos:
  - brain
confidence: medium
summary: >
  The epic's second child and the win it was for: an agent subscribes to
  a thread, repo, or producer, and when a matching event lands the brain
  wakes it — so a connector's drift event pings the owning agent instead
  of every agent polling. Subscriptions are signed subscribe events on
  the child-1 stream; the wake is a webhook POST of a hint (seq + ref,
  never a payload); the per-agent cursor is the durable at-least-once
  backstop. Closes the event-driven loop end to end.
sources:
  - ../epics/event-driven-agent-triggers.md
  - ../adrs/per-agent-identity.md
  - ../topics/event-driven-multi-agent.md
---

# Owner-subscription wake — the headline agentic win

:::note[Part of Event-driven triggers for multi-agent work]
This work is the second child of [`event-driven-agent-triggers`](../epics/event-driven-agent-triggers.md),
built on [`per-agent-identity`](../adrs/per-agent-identity.md) (child 1).
Umbrella objective: an agent's action wakes the agents who care,
without re-introducing scheduled autonomous loops.
:::

## What

An agent subscribes to what it cares about — a channel thread, a repo,
or a producer — and when a matching event lands on the stream, the brain
**wakes** it. The wake is a hint, never an invocation: the woken agent
pulls the event and reacts on its own next tend. This is the win the
whole epic was for; it closes the loop.

## How

At PRD (fat-marker) fidelity:

A **subscription is a signed `subscribe` event** on the child-1 stream —
it carries a match pattern and the agent's wake URL, and it is signed
and attributable like every other event. Unsubscribing is a later
subscribe event with an empty URL. The active subscription set is the
fold of those events, so there is no new store.

When a non-subscribe event lands, the brain **matches** it against the
active subscriptions (a simple glob over the event's ref — `channel:*`,
`repo:brain`, `producer:structure`) and **wakes** each matching owner by
**POSTing a signed hint** (the event's seq and ref, nothing more) to the
agent's registered URL. The wake carries no payload, so even a
misdirected POST leaks only a sequence number.

Delivery is **at-least-once**, and correctness comes from **idempotent
tend**, not from the webhook: the woken agent reads `/api/events` from
its cursor, which already delivers every matching event exactly the way
child 1 built it. So the webhook is an *accelerator* — it wakes the
agent sooner — and the cursor is the durable backstop when a POST fails,
times out, or hits a dead URL. Fan-out is capped per event so one event
can never wake an unbounded fleet.

## Why

Child 1 built the identity and the stream but nothing reads them on its
own — an agent still has to poll `/api/events`. The whole point of the
epic is that an agent's action *wakes the agents who care*: a connector's
drift event should ping the repo's owning agent, a channel post should
ping the thread's subscribers, without everyone polling everything. That
is this child, and it is the reason child 1 was worth building.

## Now

Events land on the append-only stream and any authenticated agent can
read them from its cursor (`/api/events`), but only by pulling. There is
no subscription, no matching, and no wake — an agent learns of a
relevant event only when it next chooses to read.

## Perceived

The epic records owner-subscription wake as "the headline win, unblocked
by child 1." The gap is that "wake" still needs a delivery mechanism the
brain does not have: an outbound push to the owning agent, which is a
new network surface the brain has never had.

## Target

An agent subscribes with a pattern and a wake URL. A matching event
POSTs a signed hint to that URL within the same request that appended
the event. The agent verifies the hint, pulls from its cursor, and tends.
A failed webhook is logged and harmless — the cursor catches the agent
up regardless. Fan-out per event is bounded; the wake never invokes the
agent; local-first is untouched.

## Appetite

Medium. Subscriptions reuse the child-1 stream (near-free); the real
cost is the outbound webhook — an SSRF guard on agent-supplied URLs, a
short timeout, no redirects, best-effort retry, and a per-event fan-out
cap. Not a message broker, not exactly-once, not a retry queue.

## Affected personas

- [Viktor — daily operator](../../../.claude/personas/users/viktor-daily-operator.md)
  gets the win he'd fight for: drift on a repo he owns pings his agent
  instead of rotting `architecture.md` unseen — and the abandon-trigger
  he named (a chatty bus) is held off by the per-event cap and the
  hint-not-payload rule.

## No-gos

- **The wake never invokes.** It POSTs a hint; the agent decides to act
  on its own next tend. No scheduled LLM, no auto-reaction.
- **Hint, not payload.** The webhook body is the event's seq + ref only,
  signed — never the event content. The `/api/events` pull is the only
  way to read content, and it is authenticated.
- **No new store, no broker.** Subscriptions are signed events on the
  existing stream; the cursor is the at-least-once guarantee; there is
  no exactly-once and no retry queue.
- **Local-first unchanged.** Subscriptions and wakes exist only on the
  hosted tier; a single operator has none.

## Rabbit holes

- **SSRF via wake URLs.** The brain POSTing to agent-supplied URLs is a
  server-side request forgery surface. The guard (scheme allowlist,
  reject loopback/private hosts, no redirects, short timeout) is
  load-bearing and the hint-not-payload rule caps the blast radius.
- **Retry storms and dead URLs.** Best-effort with a tiny bounded retry;
  a dead URL is logged and dropped, never queued. The cursor backstop is
  why this is safe to keep dumb.
- **Fan-out storms.** A broadly-matching subscription (`*`) could wake a
  fleet on every event. Cap wakes per event and keep patterns specific.
- **Signing the wake.** The brain signs the hint with the subscriber's
  own key (which it holds), so the agent verifies it came from the
  boundary — no new brain principal needed.

## Decision needed (for the Tech Lead / ADR)

The wake channel is chosen (webhook, operator pick 2026-07-14). The ADR
commits: how subscriptions encode pattern + URL on a signed event, the
exact SSRF guard, the per-event fan-out cap and retry bound, and where
delivery fires (the hosted write path, after append).

## Decision

Made in [`owner-subscription-wake`](../adrs/owner-subscription-wake.md)
(ADR, 2026-07-14): signed subscribe events encode a glob pattern + wake
URL; a matching append POSTs a signed hint (seq + ref) through an SSRF
guard (scheme allowlist, no loopback/private hosts, no redirects, short
timeout), capped per event; the cursor is the at-least-once backstop.
