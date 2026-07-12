---
title: "Does the kernel need its own chat surface, or do MCP + CLI + the terminal cover it?"
kind: topic
status: superseded
superseded_by: brain/adrs/mcp-cli-surface.md
updated: 2026-07-12
confidence: medium
summary: >
  Settled twice in one week: the chat pane, then the embedded terminal, both failed the deletion test against MCP + CLI coverage. Surfaces settle at MCP + CLI.
sources:
  - ../../../sources/conversations/2026-07-12--chat-surface-reconsidered.md
  - ../adrs/chat-print-mode-bridge.md
---

# Does the kernel need its own chat surface, or do MCP + CLI + the terminal cover it?

## Question

The operator is reconsidering the 0.12 chat pane two days after it
shipped: the kernel maintains a chat UI, endpoint, per-harness
print-mode registry, and continuation state — while every function
it serves may already be covered elsewhere. Is the chat a
load-bearing surface or a component that passes the deletion test?

## Discussion

- **2026-07-12** (`by: claude (fable 5)`) — position: **remove it;
  the operator's instinct is right.** The coverage argument: (1) an
  interactive harness in the workbench terminal *is* a chat with
  the brain — richer than ours (streaming, tool visibility,
  permission prompts, persistent context) and cheaper per turn
  (print-mode spawns reload context each message); (2) every
  MCP-aware chat client (Claude Desktop, Cursor, ChatGPT
  connectors) already gives non-terminal users chat-with-the-brain
  via `install-agent` + the MCP server — with far better chat UX
  than a stdlib-rendered pane; (3) the CLI covers the deterministic
  path. The Phoenix lens we ingested says it directly: the chat
  pane can be safely deleted, which is the definition of
  not-load-bearing. What must survive the removal: the **ambient
  attention strip** and knowledge-first layout (the genuine UX win
  of 0.12), the **billing guard** (it protects PTY harness sessions
  too), `install-agent`, and bare-`brain`-opens-the-app. The two
  chat-authored product pages remain valid content. Removal is a
  *superseding* ADR (direction changes), not an amendment.

- **2026-07-12** (`by: claude (fable 5)`) — the question reopened
  the same day for the terminal: the operator asked whether the
  embedded terminal should also go. Position: yes — it is an
  arrangement of windows, not a capability (your own terminal
  beside a browser tab reproduces it), and it is the kernel's
  largest security/maintenance surface relative to value. Named
  loss: the billing guard degrades from enforcement to a `doctor`
  warning, since nothing is spawned to strip. The operator
  approved. This supersedes the two-day-old ADR's explicit
  rejection of "remove the terminal too" — the layout was
  load-bearing, the component was not.

## Outcome

**Settled 2026-07-12, twice** — the operator decided: remove the
chat pane (recorded as
[adrs/mcp-cli-terminal-surface.md](../adrs/mcp-cli-terminal-surface.md)),
then the embedded terminal the same week (recorded as
[adrs/mcp-cli-surface.md](../adrs/mcp-cli-surface.md), which
supersedes the former). The kernel's surfaces settle at MCP + CLI;
the app page is the rendered knowledge under the ambient strip.
