---
title: "Per-agent identity on a signed, append-only event stream"
kind: decision
status: draft
updated: 2026-07-14
team: brain kernel
division: "(brain)"
parent_epic: event-driven-agent-triggers
repos:
  - brain
confidence: medium
summary: >
  The hosted brain authenticates and attributes agents with per-agent
  keys, and signed events live on a new append-only event stream under
  wiki/_state/events that agents read per-agent cursors over. The auth
  boundary both rejects forged appends at write time and verifies
  attribution on read. Local-first is untouched. Chosen over tombstoned
  inbox items and audit-log fan-out; the operator picked the event
  stream on 2026-07-14.
sources:
  - ../prds/per-agent-identity.md
  - ../epics/event-driven-agent-triggers.md
  - ../adrs/queue-and-tend-inbox.md
  - ../adrs/connector-snapshot-contract.md
  - ../adrs/mcp-cli-surface.md
---

# Per-agent identity on a signed, append-only event stream

:::note[Part of Event-driven triggers for multi-agent work]
This decision implements [`per-agent-identity`](../prds/per-agent-identity.md),
the first child of [`event-driven-agent-triggers`](../epics/event-driven-agent-triggers.md).
Umbrella objective: an agent's action wakes the agents who care,
without re-introducing scheduled autonomous loops.
:::

## What

The hosted brain gains a minimal per-agent identity layer and a durable
home for the events that identity signs.

Each agent is issued a key that the hosted tier can rotate. Every event
an agent creates carries a signed attribution. Those events live on a
**new append-only event stream** under `wiki/_state/events` — one
signed event per line, each naming its id, its author, its signature,
its kind, and a reference to the record it concerns. Agents read
**per-agent cursors** over that stream, reusing the connector-cursor
state pattern the brain already has.

The auth boundary provides two distinct guarantees, because the
append-only log can self-provide neither: it **rejects a forged or
unsigned append at write time**, and it **verifies attribution when an
event is read**. Write-time rejection stops a bad event from ever
landing; read-time verification lets any consumer trust who an event
came from.

Local-first is untouched. With the hosted tier off, no events are
written, no keys exist, and the single machine-stamped author stays the
default. Existing single-author posts are treated as a valid legacy
principal, not rejected.

This decision delivers the substrate, the identity, and the cursors.
The subscription-and-wake that reads those cursors is the second child
of the epic and is out of scope here.

## Why

The brain has no per-agent identity today; the conversation surface
stamps one machine identity on every post, and the local server's only
guards are a request header and a loopback host check. That is correct
for one operator and a spoofing surface for many hosted agents. Every
later piece of the epic needs a principal it can trust, so identity is
the epic's first dependency.

Signed events need somewhere durable to live, and the obvious reuse —
the inbox — does not qualify: inbox items are deleted on tend, so a
consumer cannot read a stable cursor over them. A purpose-built
append-only stream is the smallest durable, structured, signable home
that keeps the wiki written only by tend and does not overload the
inbox (a queue) or the audit log (human prose). Cursor stability is the
deciding property: a stream can be rolled by period without breaking a
monotonic cursor, whereas the audit log's rotation would.

## How

The stream is an append-only, line-oriented record under
`wiki/_state/events`, rolled by period so no single file grows without
bound. One signed event occupies one line; readers address it by
position, so a per-agent cursor is a single offset the brain persists
beside the existing connector cursors. Whether the durable engine
underneath is a committed file, a write-ahead log, or a hosted table is
a build-time choice bounded by three invariants: append-only, one
signed event per line, and cursor-addressable. High-volume hosted
events are not git-committed the way the inbox is; the audit trail
stays the inbox and `log/log.md`.

The auth boundary sits on the hosted writable tier — the one that
already differs from today's read-only serving mode. It issues and
rotates per-agent keys, checks a signature before an append lands, and
exposes verification to readers. It is deliberately not a full identity
system: no OAuth, no roles, no org hierarchy, no sessions.

The confidence floor applies: this ADR stays `draft` until the work
ships, then graduates to `living` with build notes.

## Alternatives

- **Tombstoned inbox items** — stop deleting inbox items on tend and
  keep them as tombstones for cursors to read. It reuses the existing
  store and keeps a single write path, but it makes the inbox do two
  jobs (a work queue and an event log), grows without bound, and needs
  a garbage-collection pass the queue never wanted. Rejected: the
  overload is a worse cost than one new purpose-built store.
- **Fan-out over the audit log (`log/log.md`)** — reuse the one
  append-only record the brain already keeps. Rejected: it is
  prose-shaped rather than structured or signable per line, it mixes
  human audit with machine events, and it is rotated at 2,000 lines,
  which breaks any stable read cursor.
- **Verify-on-read only, no write-time rejection** — cheaper, but it
  cannot stop a forged event from landing in the stream, so a consumer
  would have to filter forgeries on every read forever. Rejected: the
  boundary must reject at write time.
- **Write-time rejection only, no read-time verification** — stops
  forged writes, but downstream readers still need to trust
  attribution independently. Rejected: both guarantees are needed, for
  different reasons.
- **Do nothing (stay poll-only)** — the brain remains a single-operator
  local tool. Rejected by the bet on the epic; the operator wants a
  hosted, multi-agent, agentic future.

## Consequences

- **Opens** the epic's second child (owner-subscription wake) on a
  stable substrate: subscriptions bind to authenticated principals and
  read cursors over the event stream.
- **Costs** a new append-only store to operate on the hosted tier, key
  issuance and rotation, and a write-time auth gate distinct from
  today's header and host checks.
- **Holds** the invariants: no scheduled LLM, the wiki is still written
  only by tend, and there is no second *content* store — the event
  stream is append-only infrastructure, not wiki content.
- **Preserves** local-first exactly; a single operator gains no keys,
  no stream, and no daemon.
- **Leaves** the durable storage engine, the key format, and the wake
  channel itself as deliberately-open build- or child-level decisions,
  bounded by the invariants named above.

## Linked PRD

[`per-agent-identity`](../prds/per-agent-identity.md) — the initiative
this decision implements.
