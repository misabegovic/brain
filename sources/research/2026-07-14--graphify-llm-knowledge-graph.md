---
title: "Deepdive: Graphify (Graphify-Labs/graphify) — a code-graph tool with an optional LLM semantic layer, as a Claude Code skill"
kind: source
captured: 2026-07-14
method: four parallel research agents (architecture, interface, brain-fit, adversarial skeptic), each re-grounding claims against primary source and the GitHub API
sources:
  - https://github.com/Graphify-Labs/graphify
  - https://raw.githubusercontent.com/Graphify-Labs/graphify/v8/README.md
  - https://raw.githubusercontent.com/Graphify-Labs/graphify/v8/docs/how-it-works.md
  - https://raw.githubusercontent.com/Graphify-Labs/graphify/v8/ARCHITECTURE.md
  - https://api.github.com/repos/Graphify-Labs/graphify
---

# Graphify deepdive — validated findings (2026-07-14)

Directed research. Tags: VERIFIED-code, VERIFIED-docs, CLAIMED, INFERRED.

## What it actually is (VERIFIED — framing correction)

Marketed as a "mixed-media knowledge graph" skill. In source it is
**primarily a deterministic tree-sitter code-graph tool** (~24–25
languages; README's "36/40" is inflated) — much like Enola. The
"docs/PDFs/images/video" layer is a *secondary, optional* pass and
the **only part that uses an LLM**. PyPI package `graphifyy`
(double-y), CLI `graphify`, v0.9.15, MIT, default branch `v8`.

## Data model (VERIFIED-code)

A NetworkX graph persisted as node-link `graph.json` in
`graphify-out/`.
- Node: `id, label, source_file, source_location, file_type
  (code|document|paper|image|rationale), _origin (ast|semantic),
  community`. No node-type enum — `file_type` + `_origin` carry it.
- Edge: `source, target, relation (calls|imports|uses|
  semantically_similar_to|…), confidence, confidence_score,
  source_file`.
- **`confidence` is a provenance tag** (the borrow-worthy part):
  - `EXTRACTED` — explicit in source; score always 1.0.
  - `INFERRED` — a deduction; discrete rubric 0.95/0.85/0.75/0.65/0.55.
  - `AMBIGUOUS` — uncertain; flagged in `GRAPH_REPORT.md` for human
    review.
- **Caveat (VERIFIED-code):** `INFERRED` is *overloaded* — it tags
  both deterministic cross-file symbol resolution (score 0.8) and
  LLM semantic guesses (0.55–0.95). Same tag, very different trust.

## Pipeline: LLM vs deterministic (VERIFIED)

- **Pass 1 — code:** tree-sitter AST, deterministic, no LLM, no
  network. Code is never sent to the LLM; code-only corpora skip
  Pass 3 entirely.
- **Pass 2 — video/audio:** faster-whisper, local, no API.
- **Pass 3 — docs/PDF/images:** Claude (or other backend) vision
  extraction, `temperature:0` (reduces but does not guarantee
  reproducibility). This is the only token-costing, non-deterministic
  stage.
- **God nodes:** pure degree-centrality top-N — deterministic (= the
  brain's `brain.py links` hubs).
- **Communities:** Leiden via graspologic, `random_seed=42` —
  deterministic partitioning; Louvain fallback; community *naming*
  uses the LLM (optional, else numeric).

## Incremental / cost (VERIFIED-code) — the key correction

SHA-256 cache: unchanged files never re-hit the LLM; code changes →
AST re-extract → $0. **The file watcher only auto-runs the AST
rebuild (no LLM); for doc changes it writes a `needs_update` flag
and asks the user to run `/graphify --update` manually — it never
silently spends tokens.** In `/graphify` skill mode the semantic
pass rides the host agent's own session — "never prompts for API
keys." So Graphify's automation *agrees* with the brain's split:
cheap deterministic work on triggers, expensive LLM only on
deliberate invocation.

## Interfaces (VERIFIED)

- `/graphify` is a classic Claude Code **skill file** (SKILL.md on
  disk) + a `CLAUDE.md` marker + PreToolUse hooks that steer the
  agent away from grep/Read toward graph queries. ~24 per-platform
  install variants (cursor, gemini, codex, opencode, …). Not a
  plugin, not MCP-based.
- CLI: ~30 subcommands (query, path, explain, affected, extract,
  watch, update, export, merge-graphs, hook, save-result, reflect,
  diagnose, …).
- MCP: official `mcp` lib, **~10–11 read-only tools** (query_graph,
  get_node, get_neighbors, get_community, god_nodes, graph_stats,
  shortest_path, list_prs, get_pr_impact, triage_prs). stdio + HTTP
  with optional bearer auth. No LLM in the server; reads graph.json.
- Exports (deterministic): graph.json, GraphML, SVG, Neo4j Cypher,
  FalkorDB, Obsidian vault + Canvas. The HTML viz uses vis-network
  9.1.6 from a CDN (SRI-pinned) — so not fully offline. Edge
  confidence is rendered as **dashing/opacity** on the HTML graph.
- LLM-dependent outputs: `GRAPH_REPORT.md`, community labels.

## Maturity (VERIFIED-API + skeptic) — large but hype-heavy

85,267 stars, 8,417 forks, 517 open issues, created 2026-04-03
(~3.5 months). Two agents independently flagged the star count as
**implausible for a pre-1.0 package** — treat popularity as
hype-velocity, not proof of quality. Pre-1.0 (v0.9.15, branch `v8`),
shipping ~daily. ~30 contributors but **one holds ~84%** (severe bus
factor). Reportedly YC S26-backed (secondary). Independent
adversarial scrutiny: essentially none — a wall of near-identical
"70x!" content-marketing posts, no critical HN/Reddit threads.

## The 71.5x claim (skeptic) — cherry-picked

Real methodology but a best-case corpus: a 52-file *multimodal* set
(code + PDFs + images) whose raw-context baseline is dominated by
expensive PDFs/images. Independent measurements land at ~7x; pure
code ~5–10x; small corpora ~1x. For a code/markdown wiki, expect
single-digit. It confirms the brain's own token-efficiency thesis
rather than teaching it.

## Limits (VERIFIED)

Pass-3 doc/media extraction is LLM-generated → non-deterministic and
can hallucinate nodes/edges. Cross-file code resolution is heuristic
(under-links rather than mislinks). `semantically_similar_to` edges
have no embedding backing (LLM judgment). The deepest anti-pattern:
"read the graph instead of the source" *hides* extraction errors
from the reader — the opposite of the brain's sources-immutability +
cite-back-to-source discipline.

## One-line takeaway for the brain

Graphify is a **near-peer**, not a complement: an LLM-assisted
knowledge graph for agents, overlapping the brain's own thesis. Its
biggest gift is *validation* — it independently confirms the brain's
bets (token-efficiency, the deterministic-triggers/deliberate-LLM
split, provenance discipline). The one genuinely-new borrow is
**edge-level provenance tags** (the brain's confidence is per-page;
its graph edges carry none). Its collapse-source-into-graph
posture is a cautionary counter-example that reinforces the brain's
cite-back-to-source rule.
