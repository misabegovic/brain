---
title: "The structure connector gains a findings layer and a write-on-judgment verdict ledger — computed in-kernel, never a ported extractor"
kind: decision
status: accepted
updated: 2026-08-02
confidence: medium
summary: >
  The structure connector extracted facts and computed no findings. It gains a deterministic findings layer (oversized-package, god-file, symbol-blindness) and a verdict ledger with no pending state, both computed in-kernel — rejecting a port of an external graph binary, which would contradict the connector's vendor-neutral position.
sources:
  - ./connector-snapshot-contract.md
  - ../ai-suggestions/prds/deterministic-structure-connector.md
  - ../../../tools/brain.py
  - ../../../brain.config.yml
---

# The structure connector gains a findings layer and a write-on-judgment verdict ledger — computed in-kernel, never a ported extractor

**Decision.** The structure connector already produces deterministic
*facts* — a tracked source-file inventory, per-package counts, and
Python top-level symbols — and reconciles drift by citation. It
produced no *findings*: nothing turned those facts into "here is
something worth a human look". It now does, in-kernel and
deterministically, through three conservative explainers
(`oversized-package`, `god-file`, `symbol-blindness`), reachable as
`brain.py structure findings`. Judgments about those findings are
recorded in a ledger at `wiki/_state/structure/finding-verdicts.json`
via `brain.py structure judge`, with a closed verdict set of
accepted / rejected / noise. **The ledger is write-on-judgment and has
no pending state**: absence of an entry means unjudged rather than
queued, nothing enumerates the unjudged set as work, and no status row
reports an unjudged count. That single rule is what keeps it a memory
rather than a backlog.

## Context

The prompt for this work was a comparison against a sibling brain
instance that had adopted an external architecture-graph binary and
built a substantial consumption layer on top of it — merged findings,
a verdict ledger, blast-radius queries, and graph-checked ingest. The
obvious move was to port that stack.

It was the wrong move, and the connector's own PRD says why: this
kernel deliberately chose *no network, no external binary, no LLM*,
computing code-shape facts itself so that nothing depends on a
particular extractor being installed. Porting a binary-backed graph
would have contradicted a recorded position rather than extended it —
and the sibling repo's conventions do not travel with its code.

What *did* travel were the concepts, because they are substrate-
agnostic. Three of them the connector already had in its own form: a
snapshot fingerprint, drift against the previous snapshot, and a
reconciler (a drift item clears when a wiki page cites the snapshot
that raised it). Three it lacked, and those are what this decision
adds: findings computed on top of facts, a place to record judgment
about them, and the discipline that a finding is a candidate to verify
rather than a verdict.

The explainers are deliberately blunt and carry the numbers that
produced them, so a reader can disagree with a threshold rather than
with the claim. `symbol-blindness` is the one that earns its place
least obviously and matters most: it reports what share of a repo the
substrate *cannot see past file level*, because symbol visibility
exists only for Python. A findings layer that reported only what it
could see, without saying what it could not, would be the more
dangerous artefact.

## Alternatives

- **Port the external graph binary and its consumption layer.**
  Largest capability gain — real call graphs, blast-radius queries,
  cross-repo edge resolution. Rejected because it contradicts the
  connector's vendor-neutral, no-external-binary position, which is a
  recorded decision rather than an accident, and because it would make
  every structure-dependent step conditional on an install the kernel
  cannot guarantee.
- **Facts only; no findings layer.** The status quo. Cheapest, and it
  keeps the connector's surface minimal. Rejected because facts
  without findings put the whole burden of noticing on whoever happens
  to read a snapshot, which is nobody on most days.
- **Findings without a ledger.** Compute and print, record nothing.
  Rejected for the reason the sibling instance found the hard way: the
  same finding is then re-triaged every session, and a judgment that
  something is *not* worth acting on has nowhere to live, so it is
  re-made forever.
- **A blast-radius query.** Genuinely valuable and deliberately **not**
  built: it needs a call graph, and the connector extracts top-level
  symbols rather than call edges. Building one in-kernel is a real
  project, not an increment, and pretending a symbol inventory can
  answer "what breaks if I change this" would be worse than declining.

## Consequences

- **Positive.** A snapshot now yields something a human can act on. A
  judgment is recorded once instead of re-litigated. The
  no-pending-state rule means the ledger cannot quietly become a
  queue. And `symbol-blindness` makes the substrate's own coverage
  limit visible to anyone weighing its other findings.
- **Negative / accepted.** Three explainers is a thin set next to what
  a real graph tool computes, and the thresholds are judgment calls
  that will need revising against evidence. The ledger grows
  monotonically and will want its own grooming pass. Symbol-level
  findings remain Python-only, which is a property of the extractor,
  not of this layer.
- **Boundary.** Findings are never pushed: nothing schedules them into
  the inbox, and the drift-by-citation reconciler stays the connector's
  only producer. A finding is pulled by whoever is already reasoning
  about a repo.

## Build notes

Built 2026-08-02, same session as the decision.

The first run against the kernel's own tree immediately produced a
true finding: `tools/brain.py` declares **167 top-level symbols**
against a repo median of 10. That is the layer working as intended on
its first use — and an observation the kernel should probably act on.

`archived-liveness` and `ledger-hygiene` join the reflection-check
detectors. `archived-liveness` resolves a repo's owner from its
checkout's `origin` remote, matching the github connector's documented
auto-discovery, and falls back to the connector's explicit slugs;
red-green verified against a repo that is genuinely unarchived and
still being pushed to. `ledger-hygiene` judges nothing when no
snapshot exists, so a missing snapshot cannot masquerade as a stale
verdict.

Also landed alongside, as hygiene rather than as part of this
decision: the citation classifier now resolves repo-root and
page-relative paths (two legitimate citations were being reported as
suspicious for their shape alone, with the prefix allowlist kept ahead
of the resolver so a *missing* path still reports broken); `schedule
run-due` records per-operation outcomes to `wiki/_state/schedule.json`
with a `brain.py status` row, because a local timer failing is *less*
visible than a red CI badge, not more; `setup-local.sh` prefers `uv`
and falls back to the stdlib path, since a uv-created venv has no pip
at all; and `/shape` Phase 2 gains a scope-coverage check that
confirms every PRD Scope bullet is carried into the ADR's How or
dropped with a reason.
