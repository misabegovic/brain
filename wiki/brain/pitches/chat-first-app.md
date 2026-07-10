---
title: "Chat-first app — the conversation is the interface; the mechanism disappears behind it"
kind: pitch
status: superseded
superseded_by: brain/prds/chat-first-app.md
updated: 2026-07-10
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-10--chat-first-simplification.md
  - ../adrs/workbench-pty-bridge.md
  - ../adrs/queue-and-tend-inbox.md
---

# Chat-first app

Pre-bet pitch per the operator's 2026-07-10 direction: simplify and
abstract as much as possible from the user; a chat in the app
instead of the embedded terminal.

## Problem

The brain's surface is powerful and legible to its builders — thirty
CLI subcommands, a slash-command vocabulary, config files, a
terminal in the workbench — but a user shouldn't need any of that
vocabulary to get value. The workbench's embedded terminal is the
tell: it puts the *mechanism* in the user's face, when what they
want is to ask things, decide things, and see results. Great UX
here means one surface that feels like: a conversation, the
knowledge beside it, and a gentle sense of what needs attention.

## Appetite

Medium — one cycle. The chat pane and its harness bridge are the
core; simplification of the rest of the surface follows from it
rather than preceding it.

## Solution

Fat-marker sketch, one load-bearing thesis: **the chat is the
abstraction.** The harness already speaks the entire mechanism —
skills, slash commands, MCP tools, the authoring conventions — so a
conversation wired to a harness abstracts the CLI without
reimplementing a single operation. "What needs attention?" becomes
the agent running the tend queue; "note this decision" becomes a
topic entry; the user never learns the words inbox or views.

- **The app**: the workbench page evolves — chat pane as the
  primary interaction (bubbles, streaming output, message history
  for the session), rendered wiki beside it (unchanged), and the
  attention strip (inbox count + health) as ambient status rather
  than a table the user parses.
- **The chat bridge**: per-harness **print-mode rows** joining the
  existing launch registry — each harness that offers a
  non-interactive text-in/text-out invocation on the operator's
  existing subscription (session-continuing where supported) gets
  one data row; the server spawns per-message invocations in the
  repo. No API billing, no scheduled runs — a chat message is
  interactive use, identical in cost model to typing in a
  terminal. Governance unchanged: the agent behind the chat obeys
  the same skills and gates it obeys anywhere.
- **The terminal**: demoted, not deleted — behind a power-user
  toggle. The PTY bridge ships and works; ripping it out hours
  after its ADR would be churn, and agents-driving-agents
  debugging genuinely wants a raw shell sometimes. The chat is the
  door; the terminal is the service hatch.
- **Simplification sweep** (follows the thesis): the wrapper's
  verb surface collapses toward `brain` = open the app; setup
  stays one command; dash content folds into the app's ambient
  strip; documentation leads with the conversation, not the CLI.

## Rabbit holes

- **Parsing interactive TUIs into bubbles.** Print modes only; if a
  harness has no print mode, it gets a terminal launch row and no
  chat row — never scrape a TUI.
- **Building a chat platform.** No accounts, no persistence beyond
  the session and the brain's own pages, no multi-user presence.
  The brain's memory *is* the persistence.
- **An in-app LLM of our own.** The harness is the model access;
  the kernel stays zero-dependency and subscription-agnostic.
- **Serving-mode chat.** This is the operator's local app; outside
  consumers keep the MCP-first story. The chat never ships in
  BRAIN_SERVING deployments.

## No-gos

- No API-key billing paths in the kernel.
- No mechanism reimplementation in the app layer — if the chat
  can't do something, the fix is a skill, not an app feature.
- Chat rows are data (like TERMINAL_CLIS), never per-harness code.
