---
title: "Ground the brain's architecture 'Now' against a deterministic structure extractor — Enola as reference implementation"
kind: initiative
status: superseded
ai_suggestion: true
superseded_by: brain/state.md
updated: 2026-07-14
team: "(inferred)"
division: "(inferred)"
repos:
  - brain
appetite: medium
confidence: low
summary: >
  A deterministic, LLM-free code-structure extractor (Enola is the
  reference implementation) could run as a brain connector: it writes
  a ground-truth "Now" snapshot into sources/, and its baseline-diff
  turns architectural drift into inbox items — a strict upgrade over
  the git-name-only sync-cursor diff. Fits the connector contract and
  queue-and-tend by construction. Gated on the tool's pre-1.0 solo
  maturity; the pattern matters more than the specific binary.
sources:
  - ../../../../sources/research/2026-07-14--enola-deterministic-architecture-extractor.md
  - ../../../../sources/web/enola-labs-enola--e01a2b.md
  - ../../adrs/connector-snapshot-contract.md
  - ../../adrs/queue-and-tend-inbox.md
  - ../../adrs/sql-views-over-derived-index.md
---

# Ground the brain's architecture 'Now' against a deterministic structure extractor — Enola as reference implementation

> **Built (0.22.0, 2026-07-14) — superseded by
> [`brain/state.md`](../../state.md) § Now.** The operator directed
> this build. It shipped **vendor-neutral** (the RFC's lead craft
> finding): rather than depend on the pre-1.0 Enola binary, the brain
> computes the structure facts itself, deterministically, from
> read-only git + `ast`. The RFC's other gates landed as code — a
> citation-based drift reconciler, the security guards (scrubbed env,
> read-only sibling with a git-clean post-condition, secret-scan,
> structural-only summaries, brain-computed filenames), and the
> honest accuracy tier (exact Python symbols, file-level elsewhere).
> Ships off; the live capability is described in `state.md`.

## Why the agent suggests this

The operator asked how the brain could benefit from Enola
(`enola-labs/enola`), which extracts a deterministic, typed graph of
a codebase from source — no LLM — and exposes it over MCP. Four
research agents deepdived and validated the findings against primary
source and against the brain's own ADRs (research note in `sources/`).

The honest conclusion: Enola is the brain's **inverse and
complement**. Enola produces the deterministic *what* (structure);
the brain synthesizes the *why* (intent, decisions,
Now/Perceived/Target). That is exactly why it fits — the brain's
`connector-snapshot-contract` and `queue-and-tend` ADRs were built to
accept deterministic, zero-LLM producers, and Enola is one.

Two caveats keep this a suggestion, not a commitment. First, Enola is
a **pre-1.0, single-maintainer project** (~5 months old, all v0.1.x,
75 stars, no independent validation) — depending on the specific
binary is a risk. Second, the transferable value is the *pattern* (a
deterministic structure snapshot as a cited "Now"), not Enola's
"determinism beats synthesis" thesis, which is the opposite of what a
knowledge wiki needs. So this proposes a **vendor-neutral connector**
with Enola as today's reference implementation.

## Inferred objective

If the brain ran a deterministic structure extractor as a connector,
an agent (and the operator) could see, deterministically, when a
sibling repo's real architecture drifts from what the wiki records —
turning the brain's central-but-hard-to-detect Now-vs-Perceived risk
into low-noise inbox items, and giving `architecture.md` a citable
ground truth instead of hand-inferred structure.

## Affected personas (agent-inferred)

- [Viktor — daily operator](../../../../.claude/personas/users/viktor-daily-operator.md)
  — would tend drift items ("a route disappeared; `architecture.md`
  still lists it") instead of re-discovering structure by hand. The
  reviewer should confirm operators want structural drift surfaced,
  and that the false-positive rate stays low.

## Now / Perceived / Target (agent's read)

- **Now** — the brain's `sync-cursor diff` reports only *which files
  changed* (git name-only). No producer tells the brain that a
  route vanished, a new cycle appeared, or a module gained a
  dependency — the exact changes that silently rot `architecture.md`.
- **Perceived** — the brain records that its connectors are
  pull-only snapshot-writers and its producers are deterministic; a
  structure extractor is simply a producer the contract already
  anticipates.
- **Target** *(hypothesis)* — a deterministic structure connector
  writes an immutable `sources/enola/<repo>--<snapshot-id>` snapshot
  on the timer; `diff_snapshot` against a brain-held baseline queues
  drift inbox items; a tend session synthesizes the facts into
  `architecture.md`/`interfaces.md` under the confidence floor,
  citing the snapshot.

## Scope (suggested)

- **The connector (substrate).** Wrap the extractor's *one-shot*
  mode (`enola --generate`, not the persistent MCP daemon) as a
  `brain-schedule.yml` producer. It reads a sibling repo, writes an
  immutable dedup-keyed snapshot into `sources/enola/`, and queues an
  inbox item per new batch. The snapshot ID (a SHA over the facts)
  *is* the connector contract's `--<shortid>` dedup key.
- **Drift → inbox (the highest-value slice).** Hold the baseline in
  brain state; `diff_snapshot` each run; each delta (new/removed
  route, new coupling, new cycle/god-class) becomes an inbox item
  routed to `state.md § Perceived`.
- **Facts as a cited source.** `query_facts` output is raw material a
  tend/ingest session synthesizes into `architecture.md`,
  `interfaces.md`, `domain.md` — cited, never pasted.
- **A structure plane in the derived index.** Index `facts.jsonl`
  as one more plane so view specs can join code structure × wiki
  synthesis ("routes with no `interfaces.md` coverage"). The
  `sql-views-over-derived-index` ADR explicitly invites new planes.

## No-gos (suggested)

- **Enola output is a cited source, never wiki content.** The
  connector writes `sources/`; only a tend session writes `wiki/`,
  under the confidence floor.
- **Never mutate the sibling tree.** Point the extractor's output at
  a brain-owned scratch dir; copy only the artifact into `sources/`.
- **No serving-plane exposure.** A live code-analysis MCP for
  outside consumers breaks the read-only-over-synthesis serving
  posture; rejected.
- **No hard dependency on a pre-1.0 binary.** The connector contract
  stays vendor-neutral; Enola is one implementation, swappable.
- **Don't adopt the "determinism over synthesis" thesis.** The
  brain's value is the synthesis; determinism is for the *input*,
  not the wiki.

## Rabbit holes (suggested)

- **The dead-code trap.** "Unused route" means "no consumer in this
  snapshot" — an admin script or external caller won't appear. Drift
  items must be framed as candidates to verify, never facts to act on.
- **Accuracy tiering.** Extraction is exact only for Go; other
  languages are approximate (tree-sitter limits). Drift noise scales
  with the sibling's language.
- **Staleness masquerading as truth.** A confidently-wrong stale
  snapshot is worse than live grep. The receipt's git-ref +
  content-hash provenance is the guard; surface it.
- **Baseline management.** Keeping the "wiki was synthesized from
  this commit" baseline honest is the crux; a wrong baseline makes
  every diff noise.

## Appetite (estimated)

Medium — on technical complexity only. The connector + drift-to-inbox
is the core (small on top of the existing schedule/inbox machinery);
facts-as-source and the index plane are near-free follow-ons. The
agent has no read on team capacity or strategic weight.

## Suggested success metrics

- Structural drift the git-name-only cursor would have missed shows
  up as inbox items and gets tended before `architecture.md` rots.
- Drift items are low-noise (the operator grades them useful, per the
  attention-calibration loop).
- `architecture.md`/`interfaces.md` cite `sources/enola/` snapshots
  instead of hand-inferred structure.
- No settled invariant regresses: no scheduled LLM, no sibling
  mutation, no serving-surface exposure, sources stay immutable.

## Suggested next step

Do not build the connector yet. Run one cheap experiment: point
`enola --generate` at one real sibling repo, land a single
`sources/enola/` snapshot by hand, and eyeball whether `diff_snapshot`
against a prior commit produces a drift signal worth tending. If it
does — and if the tool (or an alternative) reaches enough maturity to
depend on — `/shape` this into a real connector PRD. If the signal is
noisy or the tool churns too fast, the pattern is recorded and the
specific tool is parked.

## Open questions for the human reviewer

- Is a pre-1.0 solo tool safe to build a connector around, or should
  the brain define a vendor-neutral "structure snapshot" contract and
  treat Enola as one swappable implementation? (The suggestion leans
  vendor-neutral.)
- Does Go-exact / others-approximate accuracy matter for the repos
  the brain will actually track?
- Is structural drift a signal the operator wants surfaced, or noise
  they would grade away?
- Does this overlap with in-flight work the agent can't see?
