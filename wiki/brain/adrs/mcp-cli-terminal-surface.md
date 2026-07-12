---
title: "The kernel's interaction surfaces are MCP, CLI, and the terminal — no first-party chat pane"
kind: decision
status: superseded
superseded_by: brain/adrs/mcp-cli-surface.md
updated: 2026-07-12
confidence: medium
supersedes: brain/adrs/chat-print-mode-bridge.md
summary: >
  Superseded: removed the chat pane in favour of MCP + CLI + the embedded terminal. The terminal followed it out the same week (mcp-cli-surface).
sources:
  - ../topics/chat-surface-necessity.md
  - ../../../sources/conversations/2026-07-12--chat-surface-reconsidered.md
---

# The kernel's interaction surfaces are MCP, CLI, and the terminal — no first-party chat pane

**Decision.** The kernel ships three interaction surfaces and no more:
the **MCP server** (any chat-capable client — desktop assistants, editor
agents, connector platforms — becomes a chat with the brain through
`install-agent`), the **CLI** (the deterministic and scripting path), and
the **workbench terminal** (an interactive harness session beside the
rendered knowledge — which *is* conversational use, with streaming,
visible tool activity, permission prompts, and persistent context). The
first-party chat pane, its per-harness print-mode registry, and its
endpoint are removed. What survives from the chat era because it was
never really about chat: the knowledge-first app layout with the ambient
attention strip, the bare `brain` entry point, the `install-agent`
adapters, and the billing guard — which now explicitly governs every
harness subprocess the app spawns.

## Context

Two days of reality after the chat-first decision. The pane was used
exactly twice — both times productively, proving the print-mode concept —
and then the operator asked the right question: what does it do that
isn't already covered? The answer was nothing. An interactive harness in
the terminal toggle is a strictly richer conversation at strictly lower
per-turn cost (print-mode invocations reload the whole context each
message; an interactive session keeps it). MCP-aware chat clients give
non-terminal users a better chat UI than a standard-library-rendered
pane ever will, over the same read tools. The Phoenix-Architecture
ingest supplied the test verbatim: a component that can be safely
deleted is not load-bearing. The prior decision's own alternatives
analysis had flagged the coupling risk; what it underweighted was that
the harness ecosystem already ships the chat experience, and the
kernel's job is to be the substrate those experiences plug into — not
to compete with them using a worse renderer.

## Alternatives

- **MCP + CLI + terminal, no first-party chat** *(chosen)* — the
  kernel stays a substrate; conversation UX is delegated to the tools
  that do it best; roughly two hundred lines of surface retire.
- **Keep the chat as-is** — carries a renderer, an endpoint, a
  registry, and continuation state for an experience inferior to the
  terminal one pane over. Rejected by the deletion test.
- **Keep the chat, add streaming** — deepens investment in exactly the
  duplication being questioned. Rejected.
- **Remove the terminal too, pure MCP/CLI** — deletes the one surface
  that pairs a live harness with the rendered knowledge, which real use
  (including building this product) relies on daily. Rejected.

## Consequences

- **Closes** the chat-surface question with a recorded reversal — the
  trail shows the bet, two days of evidence, and the correction; this
  is the mechanism working, not churn.
- **Opens** kernel simplification as precedent: surfaces must survive
  the deletion test against MCP, CLI, and terminal coverage.
- **Costs** the reversal itself: the chat ADR is superseded within
  days of acceptance. Accepted — cheap reversals are exactly what
  pre-1.0 and the provenance trail are for.
- **Retains** the billing guard across all harness subprocesses, the
  attention strip, `install-agent`, and the app entry point.
