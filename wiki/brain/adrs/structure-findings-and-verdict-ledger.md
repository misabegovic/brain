---
title: "Two tiers over the same repos: an always-available in-kernel structure connector with findings and a verdict ledger, plus an optional binary-backed graph"
kind: decision
status: accepted
updated: 2026-08-04
confidence: medium
summary: >
  The structure connector extracted facts and computed no findings. It gains a deterministic findings layer (oversized-package, god-file, symbol-blindness) and a verdict ledger with no pending state, both computed in-kernel. The initial rejection of an external graph binary was overturned by the operator the same day: enola now ships as an optional second tier over the same repos, with the in-kernel connector as the always-available floor.
sources:
  - ./connector-snapshot-contract.md
  - ../ai-suggestions/prds/deterministic-structure-connector.md
  - ../../../tools/brain.py
  - ../../../brain.config.yml
---

# Two tiers over the same repos: an always-available in-kernel structure connector with findings and a verdict ledger, plus an optional binary-backed graph

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

## Amendments

**2026-08-02 — the rejection is overturned; the graph tier ships as an
optional second tier.** Operator direction, explicit and repeated after
the reasoning below was put to them. The Alternatives section rejected
porting an external graph binary on the grounds that it contradicts the
connector's vendor-neutral position. That reasoning was sound about the
*connector* and wrong about the *brain*: it treated "no external
binary" as a property the whole kernel must hold, when it is a property
that makes the connector a dependable **floor**. A floor does not
forbid a ceiling.

The shape that resolves it is two tiers over the same repos:

- **The structure connector is the floor.** It needs nothing installed
  and therefore always answers. Any workflow that *requires* an answer
  runs on it alone.
- **The graph tier is the ceiling.** `brain.py enola` adds cluster
  snapshots, committed receipts, drift, merged explainer findings, and
  `impact <symbol>` — a real call graph with fan-in, fan-out and named
  callers, which is exactly the capability the original decision
  declined to build in-kernel and correctly called a project rather
  than an increment. It is allowed to be absent, and nothing depends on
  it being installed.

Two adaptations were load-bearing for a kernel rather than an instance.
The cluster is **generated from `brain.config.yml`** rather than
hand-written, so a cloned shell never inherits another operator's
absolute paths and adopting a repo into the brain adopts it into the
graph; the generated cluster file and all `.enola/` artifacts are
gitignored, leaving receipts and judgments as the only committed state.
And the port carried organisation-specific comments from its source —
the kernel's own `denylist` detector caught them on the first run,
which is the guard working exactly as intended.

Verified end to end before the config was restored to empty: the
generated cluster snapshotted this repo at 1,195 facts, produced 52
findings across four explainers, and `impact` resolved a symbol to
fan-in 11 with named callers. The blast-radius query the original
decision declined now exists — because it arrived with the binary
rather than being rebuilt.

**2026-08-02 — the consumption layer lands; the substrate is no longer
wired to nothing.** The port shipped both substrates and zero skills
consulting them, which recreated in this kernel exactly the gap the
sibling instance had described as *"the explainers ran into a void"*.
An operator question caught it — the tooling was at parity and the
consumption at zero.

Twelve of twenty-five skills now consult the substrates: `/sync` gains
an architecture-drift step reporting the finding *count* and never the
list (a list in a sweep's output is a backlog by another name);
`wiki-ingest` gains a substrate-check on its two code-shape routing
rows, with the no-signal path written as the default rather than the
weak branch; `/shape` consults it in the Phase-1 deepdive and for blast
radius in Phase 3; `/continue` before code leaves local; `/groom` gains
three trigger rows (contradicted claims, ledger hygiene, stale receipt
citations); and `/ask`, `wiki-query`, `wiki-plan`, `review`,
`zoom-out`, `wiki-overlap` and `wiki-coverage` each gain the
consultation their own judgment step was already missing.

Every wiring names **both tiers**, in that order — the structure
connector first because it always answers, the graph tier second
because it is allowed to be absent. That ordering is the kernel-shaped
difference from the sibling instance, where a single binary-backed
substrate could be assumed present.

**2026-08-04 — the graph tier reaches parity with its own tool, and
the ordering bug in `/sync` is fixed.** Operator direction, mirroring
the change made in the instance this kernel was extracted from. The
port shipped seven of enola's capabilities; `baseline`, `check`,
`coverage`, `explain`, `doctor` and a `history` family
(`log`/`show`/`diff`/`blame`/`gc`) now all run through `brain.py
enola`. `history` is grouped under one op rather than flattened,
because enola's `diff` means *delta between two revisions* while the
kernel's already means *drift against the committed receipts*, and two
things called diff in one namespace is a trap rather than a
convenience.

**Every new op keeps the two-tier contract intact.** Each degrades to
a named skip — verified by test on a shell with no binary, no cluster
and no configured repos, which is the default state of a fresh clone.
`doctor` is deliberately exempted from the cluster-config guard: it
asks whether *this checkout's* session hooks fire, which is answerable
with nothing configured at all, and a fresh shell wanting exactly that
answer is the case it exists for.

**`check` reports and never gates.** The tool exits 1 on an
architectural regression and the kernel does not propagate it. The
rule it would have broken is the older and more important one — the
graph is the ceiling, never the floor — and a gate fed by an optional
tier would make every workflow conditional on an install the kernel
cannot guarantee. What the wrapper adds is a translated verdict
carrying the distinction that matters: exit 3 means the snapshots were
not comparable, and it prints **treat as NOT ASKED, never as a pass**.
Two tests hold that line: one asserts the wrapper's own exit code is
zero, the other that both phrases survive in the source.

**A real defect surfaced while wiring `/sync`.** Its architecture-drift
step ran `enola generate && enola diff`. `generate` re-records each
repo's receipt as a side effect, so the `diff` that followed compared a
baseline against a snapshot taken seconds earlier and reported every
repo `unchanged` **by construction** — a check that could not fail.
The order is now `diff` first against the still-committed receipts,
then `generate`. This is the same defect the parent instance found and
fixed on 2026-08-03; it was inherited here and had never fired.

**Session hooks are installed, and that relaxes "pulled, never
pushed".** `enola install --hooks` (targets `claude,agents` — the
Cursor and Copilot files it offers are for tools a fresh shell need not
assume) pins a baseline at session start and reports the architectural
delta at session end *only* if the change introduced a regression. That
is the graph speaking unasked. It is recorded rather than smoothed over
because the invariant was real; the argument that won is that the
alternative was a gate nobody remembered to run, which is precisely how
the `/sync` step above spent its whole life reporting `unchanged`. The
hook never blocks and never interrupts on failure, so the cost is a
report nobody asked for rather than work nobody chose. A clone that
does not want it runs `enola uninstall`.
