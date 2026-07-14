---
title: "Deepdive: Enola (enola-labs/enola) — a deterministic code-structure extractor for AI agents"
kind: source
captured: 2026-07-14
method: four parallel research agents (architecture, interface, brain-fit, adversarial skeptic), each re-grounding claims against primary source
sources:
  - https://github.com/enola-labs/enola
  - https://raw.githubusercontent.com/enola-labs/enola/main/ARCHITECTURE.md
  - https://raw.githubusercontent.com/enola-labs/enola/main/README.md
  - https://raw.githubusercontent.com/enola-labs/enola/main/mcp-arch.yaml
  - https://api.github.com/repos/enola-labs/enola
  - https://news.ycombinator.com/item?id=48762592
---

# Enola deepdive — validated findings (2026-07-14)

Directed research. Confidence tags: VERIFIED-code (read in source),
VERIFIED-docs (README/ARCHITECTURE prose), CLAIMED (marketing),
INFERRED.

## Disambiguation (VERIFIED)

`enola-labs/enola` is the subject. `docs.enola.dev` /
`enola-dev/enola` is a **different, unrelated** project (Vorburger's
linked-data platform). Do not conflate them; the subject has no docs
site, only in-repo `.md` files.

## What it is (VERIFIED-docs)

Tagline, verbatim: **"a deterministic structural model of your
codebase for AI coding agents — your real architecture, extracted
from source, not guessed."** A single Go binary that parses a
codebase into a typed graph and exposes it to agents over MCP. No
LLM in the extraction.

## Data model (VERIFIED-code)

`Fact{Kind, Name, File string; Line int; Repo string; Props
map[string]any; Relations []Relation}`. Fixed struct; `Props` is the
open extensibility escape hatch. 8 node kinds (module, symbol,
route, storage, dependency, service + internal test_ref/file_ref); 9
relations (declares, imports, calls, implements, depends_on,
instantiates, injects, has_method [synthetic], handled_by).

## Snapshot artifacts (VERIFIED-code) — the load-bearing part for us

Written to `.enola/` (configurable):
- `facts.jsonl` — one JSON fact per line.
- `insights.json` — explainer findings with confidence + evidence.
- `snapshot.meta.json` — per-file SHA-256 content hashes (drives
  incremental).
- `receipt.json` — provenance: enola version, git ref, config hash,
  and a snapshot ID that is a **SHA-256 fingerprint over the
  byte-stable fact serialization** (not a UUID). Same commit + config
  → identical ID → identical artifact.
- `llm_context.md` — token-budgeted architecture summary (≤4000 by
  default). The only renderer; there is no GUI.

## Pipeline (VERIFIED-code)

Eight deterministic stages: file walker → per-language extractors →
in-memory fact store → cross-repo linker → graph index → explainers
→ renderer → artifacts. No model/network dependency anywhere in
extraction. 11 extractors (Go via `go/ast` = exact; others via
tree-sitter = approximate; OpenAPI/gRPC = spec scanners). Framework
awareness is real (Spring, Symfony, Retrofit, Rails/Packwerk, …). 10
explainers: cycles (Tarjan SCC, confidence 1.0), god-class (mean+2σ
fan-in), depth (longest import path), hotspots, complexity outliers,
exported surface, layers, coverage, cross-repo, unused-routes.

## Determinism verdict (VERIFIED-code, qualified)

Test-enforced (`determinism_test.go`) — but for the **normalized**
canonical serialization on a given build/config, not raw byte order.
`cacheVersion` bumps deliberately break cross-version identity. So:
"same commit → same graph" holds within a version; the README's
blanket "byte-for-byte" is CLAIMED and slightly stronger than what
the tests prove.

## Interfaces (VERIFIED)

- CLI: `enola` (stdio MCP server), `enola --explain` (one-shot,
  stdout, writes nothing), `enola --generate` (one-shot snapshot),
  `enola upgrade`.
- MCP: 13 tools, no MCP resources — generate_snapshot, explore,
  query_facts, query_insights, show_symbol, traverse, find_path,
  impact_analysis, coverage_report, set_baseline, diff_snapshot,
  snapshot_receipt, compare_receipts. Read-only over the model; the
  only write is the `.enola/` cache. No auth, local-only, no network.
- Registration is a standard manual `claude mcp add enola enola`;
  `install.sh` only drops a checksum-verified binary.

## Maturity (VERIFIED — GitHub API, 2026-07-14)

Created 2026-02-10 (~5 months). First public release v0.1.5 on
2026-06-19 (~1 month usable). Latest v0.1.34; ~30–34 patch tags in ~4
weeks; **all v0.1.x** (never 0.2, let alone 1.0). 75 stars, 6 forks,
1 open issue, 2 contributors (one dominant → effectively solo).
Apache-2.0. Independent commentary: essentially none (their Show HN,
~10 points). Honest, candid ARCHITECTURE.md. Verdict: real code,
real releases, but an **early-stage, single-maintainer, pre-1.0
project on a fast-moving surface**.

## Claim scrutiny (VERIFIED)

- "Deterministic" — HOLDS for extraction; but insights are
  threshold heuristics (confidence < 1.0); deterministic ≠ correct.
- "Your real architecture" — OVERSTATED; it is the static
  call/type/import graph, a subset. Misses runtime wiring, config,
  reflection, deploy topology, and intent.
- "14+ languages" — tiered: Go exact, 8 others approximate
  (tree-sitter grammar limits, e.g. Swift ~3% files misparsed;
  C/C++ won't merge include/src trees), OpenAPI/gRPC spec-only.
- The dead-code trap (their own caveat): `impact_analysis` /
  `coverage_report` see only consumers *in this snapshot* — an admin
  script, cron, webhook, or external caller won't appear, so
  "unused" means "unused here," not "safe to delete."

## What it structurally cannot capture (VERIFIED-docs)

Runtime/dynamic dispatch, DI/service-locator wiring, config-driven
behaviour, reflection/codegen, data-flow/semantics, and the "why."
Tests are excluded by default. History is per-snapshot only.

## The one-line takeaway for the brain

Enola is the brain's **inverse and complement**: it extracts the
deterministic *what* (structure, from source, no LLM); the brain
synthesizes the *why* (intent, decisions, Now/Perceived/Target).
The strongest fit is Enola-as-a-connector feeding a deterministic
"Now" the brain cites and validates against — never the brain
copying Enola's "determinism over synthesis" thesis, which is the
opposite of what a knowledge wiki needs.
