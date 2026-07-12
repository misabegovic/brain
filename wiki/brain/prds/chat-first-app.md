---
title: "Chat-first app — conversation as the interface, ambient status, one command to open it all"
kind: initiative
status: living
updated: 2026-07-10
confidence: medium
supersedes: brain/pitches/chat-first-app.md
summary: >
  The 0.12 chat-first app: conversation as the interface over per-harness print-mode rows, terminal demoted to a toggle. Shipped, then the chat pane was removed at 0.14 — the layout and strip survive.
sources:
  - ../pitches/chat-first-app.md
  - ../../../sources/conversations/2026-07-10--chat-first-simplification.md
---

# Chat-first app

Graduated 2026-07-10 on the operator's explicit picks: per-harness
print-mode registry; terminal demoted to a power toggle; **full
surface collapse** in the same cycle.

## What

The app becomes: a chat as the primary interaction (wired to any
harness with a print mode, on the operator's existing subscription),
the rendered knowledge beside it, and an ambient attention strip
(queue count + health) instead of tables to parse. The terminal
survives behind an advanced toggle. The command surface collapses to
its simplest form: `brain`, alone, opens the app.

## How

Chat rows join the harness registry as data (print-mode invocation +
continuation form per harness); the server gains a chat endpoint
that runs one print-mode invocation per message in the repo, under
the same token/host gating and serving-mode exclusion as the PTY.
The page reorders around the conversation; the attention strip
reads the same sources the dashboard reads. The wrapper's bare
invocation becomes the app. Documentation leads with the
conversation; the CLI remains fully present as the power surface.

## Why

The operator's direction: abstract the mechanism away for great UX.
The thesis that makes it cheap: the harness already speaks the whole
mechanism, so the conversation abstracts the vocabulary without
reimplementing an operation — a chat message costs what a terminal
keystroke costs, and governance travels with the agent.

## Now

Shipped 2026-07-10 with the bet (see the ADR's build notes for the
shapes chosen in-flight).

## Perceived

Fresh. Risks to watch: print-mode UX latency (a message can run
minutes when the agent works; v1 blocks with a typing indicator —
streaming is the named follow-up), and permission friction (chat
sessions inherit project permissions; deep write actions may want
the terminal toggle).

## Target

Streaming responses; chat transcript capture into sources/ on
request; the chat as the onboarding path (first-run message
suggestions). Reassess the toggle's discoverability after real use.
