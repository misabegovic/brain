---
title: "Enola (enola-labs/enola) — deterministic code-structure model for AI agents"
kind: source
url: https://github.com/enola-labs/enola
pulled: 2026-07-14
fetched_via: WebFetch (raw README.md + ARCHITECTURE.md)
source_kind: open-source-project (Apache-2.0)
---

# Enola — snapshot of README + ARCHITECTURE (2026-07-14)

Directed-research snapshot. Enola is **"a deterministic structural
model of your codebase for AI coding agents — your real
architecture, extracted from source, not guessed"** (README tagline,
verbatim). Go 1.25+, tree-sitter parsing, MCP-first.

## Data model (verified from ARCHITECTURE.md)

Directed, typed graph.

- **Kinds (nodes):** `module`, `symbol`, `route`, `storage`,
  `dependency`, `service` (whole repo, cross-repo mode).
- **Relations (edges):** `declares`, `imports`, `calls`,
  `implements`, `depends_on`, `instantiates`, `injects`,
  `has_method`, `handled_by`.
- Each `Fact`: `Kind`, `Name`, `File`, `Line`, `Repo`, `Props`,
  `Relations`.

## Snapshot artifacts (verified)

Written to `.enola/` (configurable `output.dir`):

- `facts.jsonl` — one JSON fact per line.
- `insights.json` — computed findings with confidence scores.
- `snapshot.meta.json` — per-file SHA-256 content hashes.
- `receipt.json` — provenance: enola version, git ref, config hash,
  and a `sha256:` fingerprint over the byte-stable fact
  serialization (deterministic snapshot ID, not a UUID).
- `llm_context.md` — token-budgeted architecture summary for agents.
- `previous/` (auto-rotated) and `baseline/` (pinned by
  `set_baseline`).

## Pipeline (verified — eight deterministic stages)

File walker → language extractors (Go `go/ast`; tree-sitter for
others; YAML/JSON config scanners) → in-memory fact store →
cross-repo linker → bidirectional graph index (synthetic edges) →
explainers (deterministic analyses) → renderer (`llm_context.md`) →
artifacts. "Nothing in the graph is guessed by a language model…
Run enola twice on the same commit and you get the same graph, byte
for byte."

## Insights / algorithms (verified)

Tarjan SCC (cycles, confidence 1.0); layer-violation pattern match;
god-class fan-in outliers; hotspot centrality (fanIn×fanOut);
dependency-depth longest-path (cycle-safe); exported-surface ratio;
cyclomatic-complexity statistical outliers; unused-routes
(confidence 0.6); cross-repo edge coverage.

## Incremental / diff / baseline (verified)

Incremental by default: only files whose SHA-256 changed are
re-parsed. `set_baseline` pins a snapshot to `.enola/baseline/`.
`diff_snapshot` computes the architectural delta between baseline
and current — "a delta, not a linter: it judges the current
snapshot against the codebase's own prior state," with
structural-cause classification and a comparability guard.

## Interfaces (verified/claimed)

- **CLI (one-shot):** `enola --generate` (snapshot), `enola
  --explain` (report).
- **MCP server:** long-running, ~13 agent-callable tools
  (`generate_snapshot`, `impact_analysis`, `diff_snapshot`,
  `traverse`, `find_path`, `query_facts`, `query_insights`,
  `set_baseline`, …). Registers with Claude Code / Cursor / Copilot.
- Languages: Go, Java, JS, TS, Python, Kotlin, Swift, Ruby, C/C++,
  PHP, Vue, Svelte, OpenAPI, gRPC — with framework awareness.

## Stated limitations (verified)

Swift split include/src trees not merged; tree-sitter-swift misses
`(A,B).self` (~3% files); Symfony route `resource` includes not
expanded; TS default-imported wrappers not resolved in call-edges;
hand-rolled gRPC clients bypassing generated stubs not recognized.
Structural-from-source only: no runtime/dynamic behaviour, no
data-flow semantics, no "why".

Sources: <https://github.com/enola-labs/enola> (raw README.md,
ARCHITECTURE.md), fetched 2026-07-14.
