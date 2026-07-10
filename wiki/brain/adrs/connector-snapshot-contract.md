---
title: "Connectors are pull-only snapshot-writers: immutable dedup-keyed files under sources/, cursors in state, inbox items out — never a wiki write"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-10--self-hosting-roadmap-intent.md
  - ../../../brain-schedule.yml
  - .claude/skills/tend/SKILL.md
---

# Connectors are pull-only snapshot-writers: immutable dedup-keyed files under `sources/`, cursors in state, inbox items out — never a wiki write

**Decision.** External systems (GitHub, Notion, Slack, and whatever the
operator adds) enter the brain through one contract. A connector is a
scheduled, deterministic tool that *pulls* with **read-only-scoped
credentials**, writes **immutable snapshots** into `sources/<connector>/`
whose file paths double as dedup keys (an existing path is never
rewritten — the additive-only rule enforces idempotency), advances a
per-source **cursor** in the connector-cursors state file, and **queues an
inbox item** per new batch for `/tend` to digest. A connector never
touches `wiki/` — synthesis is the tend loop's job, in-session, under the
normal authoring rules. Unconfigured connectors are clean no-ops: the
watch-list lives in the repo config's `connectors:` section, credentials
live in the git-ignored `.env`, and an empty watch-list or missing token
exits zero with a one-line explanation. Three built-ins ship in the kernel
(GitHub releases + merged-PR batches with sibling-remote auto-discovery;
Notion watched-page re-snapshots gated on `last_edited`; Slack per-channel
daily transcripts); custom connectors are any script honouring the same
contract, registered as a schedule entry.

## Context

The 0.3 roadmap step needed the ingestion surface to grow beyond sibling
repos without breaking the three-layer model. The forces were already
settled by prior decisions: sources are immutable and additive-only; the
wiki is synthesised only by agents under the confidence floor; the
queue-and-tend split (see
[queue-and-tend-inbox](./queue-and-tend-inbox.md)) fixes *where* model
work happens, so connectors had to be pure observation. The snapshot-first
rule for external planning sources (snapshot before ingest, cite the
snapshot) generalises verbatim from the Notion precedent to any external
system. Credential scoping is the agent-independence backstop: a
read-only token makes "the brain never writes to external systems" a
property of the credential, not of any harness's permission model.

Two design details carried the weight. First, path-as-dedup-key: because
`sources/**` is additive-only, "write only if absent" is both the
immutability guarantee and the idempotency mechanism — a re-run cannot
duplicate or clobber. Second, cursors live in one tooling-managed state
file rather than in snapshot frontmatter, so "what have we already
pulled?" is a single cheap read and the snapshots stay pure observations.

## Alternatives

- **Pull-only snapshot-writers** *(chosen)* — deterministic, free,
  credential-scoped, idempotent; the inbox is the only coupling to the
  rest of the mechanism.
- **Webhook/push listeners** — lower latency, but requires a long-running
  daemon with an inbound surface (auth, exposure, uptime) on the
  operator's machine for a harness whose stated posture is
  nothing-urgent. Rejected for 0.x; a listener could later *feed the same
  contract* by writing snapshots + inbox items.
- **Connectors ingest directly into the wiki** — one hop shorter, but it
  either bypasses the confidence floor and authoring conventions or
  requires scheduled model runs, both already rejected. Observation and
  synthesis stay separated.
- **Agent-driven pulls (the agent calls source MCPs at tend time)** —
  no connector code at all, but pulls then only happen when a session
  runs, credentials become harness-coupled, and nothing accumulates
  while the operator is away. Rejected as the primary path; agents can
  still do ad-hoc pulls via `/in` at any time.
- **Do nothing** — Slack/Notion/GitHub context keeps arriving only when
  the operator remembers to paste it. Rejected; that memory tax is the
  thing being automated away.

## Consequences

- **Closes** the ingestion-surface question: anything external reaches
  the wiki as snapshot → inbox item → in-session synthesis, uniformly.
- **Closes** the write-safety question by construction: read-only
  tokens + additive-only sources + no wiki access from connectors.
- **Opens** operator-defined connectors as first-class: the contract is
  documented, the built-ins are worked examples, registration is one
  schedule entry.
- **Opens** the 0.5 serving story cleanly — served consumers read the
  same synthesised wiki; connectors never add a second write path.
- **Costs** snapshot volume growth in `sources/` (bounded by watch-lists
  and cursors); the standard grooming pressure applies to the synthesis
  layer, never to the immutable snapshots themselves.
- **Costs** a per-connector cursor surface to keep honest; mitigated by
  one shared state file and the no-op-when-unconfigured rule.

## Build notes

Shipped with the three built-ins inside the kernel CLI (shared helpers
for config, env, cursors, snapshot-writes) rather than as separate
scripts — one import surface, one test surface; custom connectors remain
external scripts by contract. The GitHub connector auto-discovers
sibling-checkout origins so declaring a repo in the registry is enough to
watch it. Verified end-to-end against a public repository: first run
snapshotted ten releases and a PR batch and queued one inbox item;
the second run pulled nothing — the cursor plus path-dedup held.
