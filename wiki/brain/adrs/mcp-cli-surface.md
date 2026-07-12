---
title: "The kernel's interaction surfaces are MCP and the CLI — the embedded terminal retires with the chat pane"
kind: decision
status: accepted
updated: 2026-07-12
confidence: medium
supersedes: brain/adrs/mcp-cli-terminal-surface.md
summary: >
  The kernel's interaction surfaces settle at MCP and the CLI: the embedded terminal (PTY bridge, websocket, xterm) retires; the app page is the rendered knowledge under the ambient strip; the billing guard degrades to a doctor warning.
sources:
  - ../../../sources/conversations/2026-07-12--embedded-terminal-removal.md
  - ../topics/chat-surface-necessity.md
---

# The kernel's interaction surfaces are MCP and the CLI — the embedded terminal retires with the chat pane

**Decision.** The kernel ships two interaction surfaces: the **MCP
server** (any harness or chat client becomes a conversation with the
brain through `install-agent`) and the **CLI** (the deterministic and
scripting path). The embedded workbench terminal — the PTY bridge, the
hand-rolled websocket slice, the xterm.js assets, the harness-launch
registry — is removed. The app page survives as the rendered knowledge
under the ambient attention strip, auto-reloading as the wiki changes;
the operator runs their harness in their own terminal beside it. The
billing guard retires with the terminal: with no app-spawned
subprocesses left to strip, enforcement degrades honestly to a
`doctor` warning when metered API keys sit in the operator's
environment.

## Context

The chat-pane removal two days earlier had explicitly rejected "remove
the terminal too" on the grounds that real use relied on it daily. The
operator re-asked the question after the presentation pass, and the
deletion test cut the other way on inspection: the embedded terminal
is an arrangement of windows, not a capability — the operator's own
terminal emulator beside a browser tab reproduces it exactly, with
better ergonomics. What the kernel was actually paying for it: the
largest remaining maintenance surface relative to value, and the one
component a security review of a public release flags first (arbitrary
shell execution over a websocket, however defensibly gated behind
loopback, token, and Host checks). The pieces that made the app
genuinely useful — the strip, the auto-reload, `install-agent` — never
depended on the terminal.

## Alternatives

- **MCP + CLI only; app = rendered knowledge + strip** *(chosen)* —
  the kernel's riskiest component disappears rather than being
  defended forever; the explanation of what the product is gets one
  clause shorter.
- **Keep the terminal** — the prior ADR's position. Rejected on
  re-inspection: "real use relies on it" conflated the *layout* (agent
  beside knowledge, which any window manager provides) with the
  *component* (a PTY bridge only the kernel provides, and only the
  kernel must then secure).
- **Keep the PTY but drop the launch registry** — smaller surface,
  same reviewer flag, none of the simplification. Rejected.

## Consequences

- **Closes** the interaction-surface question at its fixed point:
  every first-party surface now survives the deletion test.
- **Costs** the billing guard's enforcement — protection degrades to
  advice (`doctor` warns on API-key env vars). Accepted and named at
  decision time.
- **Costs** a second same-week supersede in the trail. Accepted —
  cheap reversals before 1.0 are the mechanism working.
- **Retains** the strip, the auto-reload rebuild, bare-`brain`
  opening the app, and `install-agent` as the sole harness wiring.
