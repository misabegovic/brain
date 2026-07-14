---
title: "Event-driven triggers for multi-agent work — an agentic future for a hosted brain"
kind: pitch
status: draft
updated: 2026-07-14
team: brain kernel
division: "(brain)"
appetite: big
repos:
  - brain
confidence: low
sources:
  - ../topics/event-driven-multi-agent.md
  - ../adrs/queue-and-tend-inbox.md
  - ../adrs/connector-snapshot-contract.md
  - ../adrs/mcp-cli-surface.md
---

# Event-driven triggers for multi-agent work — an agentic future for a hosted brain

Shape Up **pitch** — pre-bet, fat-marker fidelity. It graduates from
the [event-driven-multi-agent topic](../topics/event-driven-multi-agent.md),
which a live four-agent session on the brain itself produced. On a bet
this most likely becomes an **epic + children** (identity first, then
owner-subscription wake), not a single PRD — see Appetite.

## Problem

The brain is deliberately poll-driven. Deterministic producers
accumulate inbox items; a human-run session tends them; no LLM ever
runs on a schedule (queue-and-tend). That is exactly right for one
operator at a local checkout. It breaks the moment several agents
collaborate through the brain — and it breaks hardest if the brain is
hosted for a team.

Two concrete gaps make this real, not hypothetical:

- **Nobody gets woken.** When a connector detects that a repo's
  architecture drifted, or one agent posts to a channel another agent
  owns, the only way the interested party finds out is to poll the
  inbox. On a local checkout the operator polls by tending. Across
  several hosted agents, "everyone polls everything" is either wasteful
  or slow, and the agent who should react has no idea it should.
- **Everyone is "operator."** The conversation surface stamps a single
  machine identity (`BRAIN_AUTHOR`, default `operator`) on every post.
  Locally that is honest. Hosted and multi-agent, it means posts are
  unattributable, subscriptions are unspoofable-from, and there is no
  boundary that could reject a forged event. The brain has **no
  per-agent identity today** at all.

The operator wants an agentic future: a brain that is shared
infrastructure, where an agent's action wakes the agents who care —
without re-introducing the always-on autonomous loops the brain
spent weeks deleting.

## Appetite

**Big** — but the bet's shape matters more than the size. This is not
one change; it is a hosting-posture shift, a genuinely new identity
component, an event-fan-out substrate, and a small tend-loop
extension. On a bet it should graduate to an **epic with two children
in dependency order**, not a monolithic PRD:

1. **Per-agent identity** — the true first dependency. A hosted
   multi-tenant wake is meaningless without authenticated,
   attributable agents.
2. **Owner-subscription wake** — the headline, user-visible win, built
   on top of identity.

The betting table should size the epic, not this pitch. The honest
minimum that delivers value is child 2 (owner-subscription wake), and
it cannot ship before child 1 (identity). Everything else named below
is explicitly deferred.

## Affected personas

- [Viktor — daily operator](../../../.claude/personas/users/viktor-daily-operator.md)
  owns the win: running a hosted team brain where a drift event pings
  the owning agent instead of Viktor re-discovering rot by hand. He
  also owns the risk — a chatty event bus that wakes agents to burn
  tokens with no human in the loop is the thing he would turn off.
- The **autonomous agents** are the consumers: they subscribe, get
  woken, and react on their own next tend. They are not a `users/`
  persona, but they are the second audience and the reason identity is
  load-bearing.

## Solution

The agreed shape from the topic, at fat-marker fidelity. Four moving
parts; the loop reuses the brain's existing bones.

**Notification is a read-side fan-out, never a scheduler.** An event is
not a new write path and not a timer. When a producer or an agent
appends something the brain already records (a connector batch, a
channel post, a drift item), interested agents are *told an item
exists*. They still pull and tend on their own initiative. The wake is
a hint, never an auto-invocation — this is the line that keeps
queue-and-tend intact and keeps a self-firing agent loop from emerging.

**Identity rides on the item.** A post, a claim, or an attribution is a
signed field carried on the event itself and verified on read — no
second write path, no side channel. What the append-only record cannot
self-provide is the boundary that *rejects a forged append* and issues
and rotates per-agent keys. That boundary — a minimal per-agent auth
layer — is the one genuinely new component, and it is child 1.

**Owner-subscription is the MVP.** An agent (or the operator on its
behalf) subscribes to a thread, a repo, or a producer. When a matching
event lands, the subscriber is woken. Delivery is **at-least-once**;
correctness comes from **idempotent tend**, not from a broker
guaranteeing exactly-once. That choice deletes the hardest piece
(a claim-once broker) from v1 while still shipping the win: a drift
event pings its owning agent, a channel post pings the thread's
subscribers.

**The push channel is deliberately dumb.** A subscriber connects and
hears "a new item exists for you" — nothing more. Whether that is
server-sent events, a webhook, or a long-poll is an ADR-level detail;
the pitch's bet is only that it carries a wake, not a payload, so it
can never leak content or become an instruction stream.

Breadboarded end to end: *producer appends event → auth boundary
verifies the signer → fan-out marks the event against each subscriber's
cursor → subscribers hear "you have something" → each pulls, tends, and
reacts on its own, capped per event and human-gated for anything
execute-priority.* Queue-and-tend still governs the reaction; the only
new thing is that the wake is pushed instead of polled.

## Rabbit holes

- **The "append-only inbox" does not exist yet.** The topic assumed the
  inbox is an append-only event log. It is not — inbox items are
  *deleted* on tend (`inbox done` unlinks the file). The append-only
  record the brain actually has is the audit log (`log/log.md`). So the
  fan-out substrate is a real, unresolved design question: retain a
  parallel append-only event stream, or fan out over the audit log, or
  keep tended items as tombstones. Do not assume it is free. This is
  the single biggest thing the epic must resolve before building
  child 2.
- **Identity scope creep.** "Per-agent auth" can balloon into a full
  IAM. The bet is the minimum: issue and rotate per-agent keys, sign
  events, reject forged appends. OAuth, roles, and org hierarchies are
  out of the appetite.
- **Claim-once is a siren.** Exactly-once delivery and claim-once
  subscriptions are tempting and hard (they need a write-time conflict
  check a read cursor cannot provide). At-least-once + idempotent tend
  is the deliberate cheaper answer for v1; resist rebuilding a broker.
- **Hosting collides with serving mode.** Serving mode today is
  read-only, unauthenticated, behind a proxy. An event-driven
  multi-agent brain needs a *writable, authenticated, multi-tenant*
  tier — a different deployment posture. That tier's shape is a real
  cost, not a footnote.

## No-gos

- **No scheduled LLM.** The wake is a hint; it never auto-invokes an
  agent. Any autonomous reaction stays capped per event and, for
  execute-priority, human-gated. This is the queue-and-tend line and it
  does not move.
- **No second write path.** Fan-out is read-side over records the brain
  already writes. Identity and claims ride on the event item, verified
  on read. Nothing here adds a parallel writer to the wiki or the
  inbox.
- **No unauthenticated multi-tenant.** Owner-subscription wake does not
  ship before per-agent identity. A hosted wake without authenticated
  senders is a spoofing surface, not a feature.
- **Local-first stays unchanged.** This is additive and opt-in for the
  hosted deployment. A single operator at a local checkout keeps the
  exact queue-and-tend loop they have now, with no new moving parts and
  no daemon.
- **Push carries a wake, not a payload.** The channel says "you have
  something," never the content — so it can neither leak private data
  nor become an agent-to-agent instruction stream.
