---
title: "Per-agent identity for a hosted brain"
kind: initiative
status: living
updated: 2026-07-14
team: brain kernel
division: "(brain)"
appetite: medium
parent_epic: event-driven-agent-triggers
repos:
  - brain
confidence: medium
summary: >
  The first child of the event-driven epic and its true first
  dependency: a minimal per-agent identity layer so a hosted brain can
  authenticate and attribute agents — issue and rotate per-agent keys,
  sign events, verify on read, reject forged appends at the write
  boundary. Also settles the event-fan-out substrate (the inbox is not
  append-only), since signed events need somewhere durable to live.
  Not a full IAM; local-first stays unchanged.
sources:
  - ../epics/event-driven-agent-triggers.md
  - ../pitches/event-driven-agent-triggers.md
  - ../adrs/mcp-cli-surface.md
  - ../adrs/queue-and-tend-inbox.md
---

# Per-agent identity for a hosted brain

:::note[Part of Event-driven triggers for multi-agent work]
This work is a child of [`event-driven-agent-triggers`](../epics/event-driven-agent-triggers.md).
Umbrella objective: give the brain an event-driven backbone for
multi-agent work — an agent's action wakes the agents who care —
without re-introducing scheduled autonomous loops.
:::

## What

A minimal per-agent identity layer for the hosted brain: issue and
rotate a key per agent, carry a signed attribution on every event, and
reject forged or unsigned appends at the write boundary. Enough to
authenticate and attribute agents — not a full identity-and-access
system. This is the epic's first dependency: owner-subscription wake is
a spoofing surface without it.

## How

At PRD (fat-marker) fidelity, leaving the commitments to the ADR:

Every event an agent creates — a channel post today, a subscription or
a claim later — carries a **signed attribution field on the item
itself**, verified when it is read. No side channel and no second write
path: the signature rides the record the brain already writes. The
hosted, writable tier gains an **auth boundary** that verifies the
signer and **rejects a forged or unsigned append at write time** —
because verify-on-read alone cannot stop a bad write from landing, and
read-only cursors carry neither forgery-rejection nor conflict checks.
Keys are issued and rotated per agent by that boundary.

This child also settles the **event-fan-out substrate**, because signed
events need somewhere durable to live for cursors to read them — and
the inbox does not qualify (items are deleted on tend). The ADR
chooses among a retained append-only event stream, fan-out over the
existing append-only audit log, or tombstoned inbox items. That choice
is the load-bearing decision here.

Local-first is untouched: a single operator at a local checkout issues
no keys and signs nothing; the current machine-stamped author stays the
default when the hosted tier is off.

## Why

The brain has **no per-agent identity today**. The conversation surface
stamps a single machine identity (`BRAIN_AUTHOR`, default `operator`)
on every post; the local server's only guards are a custom request
header and a loopback Host check; serving mode is read-only and
unauthenticated behind a proxy. That is correct for one operator and
breaks the moment several agents collaborate on a hosted brain: posts
are unattributable, subscriptions have no principal to bind to, and
nothing can reject a forged event. Every later piece of the epic —
owner-subscription wake, capped reactions, execute-priority
human-gating — needs a principal it can trust.

## Now

Posts carry a server-stamped `author` from a single machine identity.
The write endpoint (`/api/act`) admits any loopback caller presenting
the `X-Brain-Act` header; there is no per-caller authentication. The
inbox is mutable — items are deleted on tend — so it is not a durable
event log. The only append-only, git-audited record the brain keeps is
`log/log.md`.

## Perceived

The brain records its attribution as "server-stamped, unforgeable by a
browser page." That is true locally, but it conflates *a browser cannot
forge the author* with *agents are authenticated* — which hosting
breaks. The gap between the two is this initiative.

## Target

Per-agent keys are issued and rotated by the hosted tier's auth
boundary. Every event carries a signed attribution verified on read.
A forged or unsigned append is rejected at write time. The event-fan-out
substrate is chosen and durable, with per-agent read cursors over it.
The local-first loop is byte-for-byte unchanged when the hosted tier is
off.

## Appetite

Medium — the larger of the epic's two children. Minimal key
issuance/rotation, signing, and a write-time reject boundary, plus the
substrate decision. It is deliberately not a full IAM; the appetite
holds only if OAuth, roles, and org hierarchy stay out.

## Affected personas

- [Viktor — daily operator](../../../.claude/personas/users/viktor-daily-operator.md)
  runs the hosted team brain and needs agents to be attributable and
  un-spoofable before he will trust a wake that pings one of them.
- The **autonomous agents** are the principals: each authenticates,
  signs its events, and is the subject of an owner-subscription later.

## No-gos

- **No full IAM.** No OAuth, roles, org hierarchy, or session
  management. Issue/rotate a per-agent key, sign, verify, reject
  forged. That is the whole appetite.
- **No second write path.** The signature is a field on the event item,
  not a parallel store.
- **No scheduled LLM, no autonomous reaction here.** This child is
  plumbing; it wakes nothing and runs no agent.
- **Local-first unchanged.** A single operator needs no keys; the
  machine-stamped author stays the default with the hosted tier off.

## Rabbit holes

- **The substrate decision balloons.** Choosing where signed events
  live could turn into building a message broker. Keep it to the
  smallest durable append-only record that cursors can read.
- **Key management scope creep.** Rotation and revocation are in;
  federation, hardware tokens, and per-scope grants are not.
- **Verify-on-read vs reject-at-write confusion.** Both are needed for
  different reasons (attribution vs forgery). The ADR must say which
  guarantee each provides so neither is mistaken for the other.
- **Backward compatibility.** Existing single-author posts predate
  signing; the design must treat them as a valid legacy principal, not
  reject the whole local history.

## Decision needed (for the Tech Lead / ADR)

Two bets the ADR must make: **which event-fan-out substrate** (retained
append-only event stream vs fan-out over the audit log vs tombstoned
inbox items), and **where the auth boundary lives and what each half
guarantees** (write-time rejection of forged appends, read-time
verification of attribution, or both — and why).

## Decision

Both bets are made in [`per-agent-identity`](../adrs/per-agent-identity.md)
(ADR, 2026-07-14). The operator picked a **new append-only event
stream** under `wiki/_state/events` (over tombstoned inbox items and
audit-log fan-out) for cursor stability, and the auth boundary does
**both** — rejects forged appends at write time and verifies
attribution on read.
