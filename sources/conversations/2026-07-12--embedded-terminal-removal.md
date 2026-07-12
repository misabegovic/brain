---
title: "Conversation capture: should the embedded terminal go too?"
kind: source
captured: 2026-07-12
participants: operator (Muhamed), claude (fable 5)
context: >
  Same-day follow-up to the chat-pane removal (0.14.0) and the
  README presentation pass (0.14.2). The operator asked whether the
  embedded workbench terminal should also be removed.
---

# Conversation capture — embedded terminal removal (2026-07-12)

**Operator:** "ok, should we also remove the embedded terminal?"

**Agent position (summarised):** yes — remove, with the trade named.
The embedded terminal is an arrangement of windows, not a
capability: the operator's own terminal beside a browser tab does
everything it does, better (tmux, tabs, scrollback). It is the most
expensive remaining component relative to value: a hand-rolled PTY
bridge + RFC-6455 websocket slice, an xterm.js asset dependency, and
the one thing a security reviewer flags on a public release
(arbitrary shell over a websocket, however defensibly gated). It
finishes the 0.14 arc: chat went because MCP + CLI cover it; the
terminal is the same argument one step further.

Named losses: (1) one-click harness launch buttons — negligible;
(2) the billing guard's enforcement — it worked by stripping API-key
env vars from subprocesses the app spawned; with nothing spawned it
degrades to a `doctor` warning; (3) the "one window" README story
and screenshot from 0.14.2 need redoing.

Resulting shape: `brain` opens the rendered knowledge under the
ambient strip (health/inbox + auto-reload survive — they never
needed the terminal); `install-agent` remains the harness wiring;
kernel = CLI + MCP + rendered site + queue.

**Operator:** "ok" — approved.
