---
title: "Owner-subscription wake via signed subscribe events and guarded webhooks"
kind: decision
status: living
updated: 2026-07-14
team: brain kernel
division: "(brain)"
parent_epic: event-driven-agent-triggers
repos:
  - brain
confidence: medium
summary: >
  Subscriptions are signed subscribe events on the child-1 stream,
  carrying a glob match pattern and a wake URL. When a matching event
  lands, the hosted write path POSTs a signed hint (seq + ref, no
  payload) to each owner's URL, capped per event, through an SSRF guard
  (scheme allowlist, no loopback/private hosts, no redirects, short
  timeout). Delivery is at-least-once; the per-agent cursor is the
  durable backstop. Webhook was the operator's pick over SSE and
  long-poll on 2026-07-14.
sources:
  - ../prds/owner-subscription-wake.md
  - ../adrs/per-agent-identity.md
  - ../epics/event-driven-agent-triggers.md
---

# Owner-subscription wake via signed subscribe events and guarded webhooks

:::note[Part of Event-driven triggers for multi-agent work]
This decision implements [`owner-subscription-wake`](../prds/owner-subscription-wake.md),
the second child of [`event-driven-agent-triggers`](../epics/event-driven-agent-triggers.md),
on top of [`per-agent-identity`](../adrs/per-agent-identity.md).
:::

## What

An agent subscribes by emitting a signed `subscribe` event whose ref
encodes a glob match pattern and the agent's wake URL. The active
subscription set is the fold of those events (a later empty-URL
subscribe unsubscribes). When a non-subscribe event is appended on the
hosted tier, the brain matches it against the active subscriptions and,
for each match up to a per-event cap, POSTs a signed hint — the event's
seq and ref, nothing more — to the owner's URL through an SSRF guard.
Delivery is at-least-once and best-effort; correctness is the woken
agent reading `/api/events` from its cursor.

## Why

Child 1 built the stream but nothing reads it unprompted. The epic's
purpose is that an agent's action wakes the agents who care. Subscriptions
as signed events reuse everything child 1 shipped — attribution, the
append-only log, verification — so there is no new store and no broker.
The webhook was the operator's pick: it holds no connection on the brain
and suits long-lived agent services, at the cost of an outbound network
surface the brain must guard. The design keeps that cost bounded by
sending a hint, never a payload, and by leaning on the cursor as the
real delivery guarantee, so a failed or blocked webhook is harmless.

## How

A subscribe event's ref is a small JSON object naming the pattern and
the wake URL, signed like any event, so neither can be tampered. The
matcher globs the pattern against an incoming event's ref
(`channel:*`, `repo:brain`, `producer:structure`). The wake body is the
seq, the ref, and an HMAC the brain computes with the subscriber's own
key — which the brain holds — so the agent verifies the hint came from
the boundary without any new brain principal.

The SSRF guard rejects any wake URL whose scheme is not http/https or
whose host is a loopback, link-local, or private address; the POST
carries a short timeout and does not follow redirects. Fan-out is
capped per event, and a failed delivery is logged and dropped, never
queued — the subscriber's cursor catches it up on its next read. The
wake never invokes the agent; local-first has no subscriptions and
fires no wakes.

The confidence floor applies: this ADR stays `draft` until it ships,
then graduates to `living` with build notes.

## Alternatives

- **SSE stream** (a held authenticated GET) — real-time and needs no
  agent-side endpoint, but the brain holds a connection per subscriber.
  Not chosen: the operator preferred the webhook's connectionless model
  for long-lived agent services.
- **Long-poll** (`/api/wake?wait=N` blocks until a match) — simplest and
  robust, no held stream, but reconnect churn and up-to-N latency. Not
  chosen; same operator call.
- **A separate subscriptions store** instead of signed subscribe events —
  rejected: it would add a second store and lose the free attribution
  and tamper-resistance the signed stream already provides.
- **Exactly-once delivery / a retry queue** — rejected: the cursor is
  already an at-least-once guarantee, so a broker is cost without value;
  idempotent tend absorbs duplicates.
- **Do nothing** — the stream stays pull-only and the epic's win never
  lands. Rejected.

## Consequences

- **Closes** the event-driven loop end to end: a drift event pings the
  repo's owning agent, a channel post pings the thread's subscribers,
  without polling.
- **Opens** a new outbound-network surface on the hosted tier; the SSRF
  guard and the hint-not-payload rule are the controls, and the blast
  radius of a bypass is a leaked sequence number.
- **Holds** the invariants: no scheduled LLM (a wake is a hint), no
  second store (subscriptions are events), no exactly-once (the cursor
  is the guarantee), local-first untouched.
- **Leaves** richer matching (beyond globs) and delivery analytics as
  later concerns, out of this appetite.

## Build notes

Shipped 0.28.0 (2026-07-14) in `tools/brain.py`, closing the epic.

- **Subscriptions** are signed `subscribe` events whose ref is a small
  JSON object of the glob pattern and wake URL; `_active_subscriptions`
  folds them (latest per agent+pattern wins, empty URL removes). CLI:
  `subscribe --agent --pattern --wake-url` and `subscriptions`.
- **Matching** is `fnmatch` glob over the event ref.
- **Delivery** POSTs `{seq, ref, sig}` — a hint, no payload — where the
  sig is HMAC of `wake:<seq>:<ref>` with the subscriber's own key, so
  the agent verifies the wake came from the boundary. Fired from a
  daemon thread off the hosted `/api/act` write path (and from
  `events emit` under `BRAIN_HOSTED`), so a slow webhook never delays
  the response. Fan-out capped at 32/event; best-effort with no retry
  queue.
- **The SSRF guard** (`_wake_url_ok`) resolves the host and rejects any
  loopback / private / link-local / reserved / multicast address, and
  non-http(s) schemes. It refused the cloud-metadata endpoint
  (`169.254.169.254`) in tests. A `BRAIN_WAKE_ALLOW_LOOPBACK=1` opt-in
  relaxes **only** loopback for same-host dev — never link-local or
  private.
- **The cursor is the guarantee.** A refused or failed webhook is logged
  and dropped; the subscriber still sees the event on its next
  `/api/events` read. Local-first has no subscriptions and fires no
  wakes.

## Linked PRD

[`owner-subscription-wake`](../prds/owner-subscription-wake.md).
