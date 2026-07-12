---
title: "Harness workbench — the brain's local surface runs your harness terminal beside the rendered results"
kind: initiative
status: living
updated: 2026-07-10
confidence: medium
supersedes: brain/pitches/harness-workbench.md
summary: >
  The local surface that put a harness terminal beside the rendered brain with install-agent MCP wiring. Shipped 0.6.x; the terminal was removed at 0.15.0, install-agent and the app shell remain.
sources:
  - ../pitches/harness-workbench.md
  - ../../../sources/conversations/2026-07-10--harness-workbench-intent.md
  - ../../../sources/research/2026-07-10--openknowledge-terminal-architecture.md
---

# Harness workbench

Graduated from the [pitch](../pitches/harness-workbench.md) on the
operator's 2026-07-10 bet, deepdived against open-knowledge's actual
implementation (research note in sources).

## What

One local surface: the brain's server gains a workbench page with an
embedded terminal (the operator's own login shell) beside the
rendered brain — dashboard, custom views, pages — with the rendered
side reloading as terminal-driven edits land. One-click harness
launches (Claude Code, Codex, Cursor, OpenCode) from a data
registry, and an `install-agent` command that generates each
harness's config so any of them reaches the brain's MCP tools and
schema — the agent-independence adapters the roadmap names.

## How

Fat-marker (the ADR names the bet): a small PTY bridge in the
kernel's server, browser terminal via the UI package's terminal
component, loopback-only with a per-session token and Host check.
Harness launches bake the command into the shell invocation so
launch lines stay out of shell history, with the single
user-influenced token quoted. Config adapters are a fan-out table —
one row per harness mapping its config path and nesting key —
managed with the same sentinel discipline as `install-sibling`.
Reload is a cheap change signal from the server the page polls or
subscribes to; git remains the only sync layer.

## Why

The working loop today crosses windows: harness in one, rendered
brain in another. The workbench collapses that to one surface,
which is also the shell's demo face — an adopter's first session
can be "open the workbench, click your harness, talk". And the
config adapters remove the last hand-wiring between harnesses and
the brain, delivering agent-independence as a command instead of a
principle.

## Now

Shipped 2026-07-10 with the bet: the PTY bridge and workbench page
on the local server, the launch registry (claude, codex,
cursor-agent, opencode), `install-agent` for the same four, and the
change-signal reload. The workbench is excluded from serving-mode
deployments by construction.

## Perceived

Fresh; no divergence recorded. Risks to watch: terminal ergonomics
in the browser (copy/paste, resize) versus a native terminal, and
whether the launch registry rows stay current as harness CLIs
rename their flags.

## Target

Operator adoption as the daily loop: workbench open, tend from the
embedded terminal, results visible without leaving. Follow-ups if
earned: more harness rows, workbench-side inbox affordances, and
the desktop-app question stays explicitly unasked.
