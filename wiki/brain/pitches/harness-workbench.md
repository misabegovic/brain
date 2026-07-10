---
title: "Harness workbench — a terminal in the brain's local UI, per-harness launch + config adapters, live-reloading results beside it"
kind: pitch
status: draft
updated: 2026-07-10
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-10--harness-workbench-intent.md
  - ../../../sources/research/2026-07-10--openknowledge-terminal-architecture.md
  - ../adrs/sql-views-over-derived-index.md
---

# Harness workbench

Pre-bet pitch per the operator's 2026-07-10 direction: run a
harness's terminal *from the brain* and see/work with the results
right there — the open-knowledge workbench shape, adapted to this
substrate. The architecture study of their actual implementation is
snapshotted as a source.

## Problem

Working with the brain today means two windows: a terminal running
the agent harness, and a browser showing the rendered wiki, views,
and dashboard. The feedback loop crosses windows — the agent edits,
the operator alt-tabs, refreshes, reads, alt-tabs back. And every
harness (Claude Code, Codex, Cursor, OpenCode) needs hand-wired
config to know the brain exists — the agent-independence adapters
the roadmap promised (`install-agent`) don't exist yet. The
workbench closes both gaps: one local surface with the terminal and
the rendered brain side by side, and one command that wires any
harness to it.

## Appetite

Medium — one cycle. The PTY bridge and the split layout are the
core; the launch registry, config adapters, and live reload are
each independently shippable increments.

## Solution

Fat-marker sketch, grounded in the open-knowledge study:

- **A local workbench page** served by the brain's existing local
  server: the rendered brain (dashboard / custom views / pages) on
  one side, an embedded terminal (xterm.js) on the other,
  resizable, terminal collapsible. Loopback-only, with a session
  token and Host-header check — the posture their loopback
  websocket uses, and never wider (the serving plane stays
  read-only and terminal-free by construction).
- **A small PTY–websocket bridge** in the kernel (Python stdlib +
  the pty module): sessions keyed by id with
  create/input/resize/kill/data/exit messages — the exact message
  shape their PTY host uses, minus Electron. It spawns the
  operator's own login shell, never an agent binary directly.
- **A harness launch registry as data**: one row per harness (bin,
  fixed args, prompt flag vs positional) drives "open in
  <harness>" buttons that bake the command into the shell
  invocation so launch lines never land in shell history, with the
  prompt single-quoted against injection. After the agent exits,
  the tab returns to a plain shell.
- **`install-agent` config adapters**, the fan-out-table pattern:
  one row per harness mapping its config file path and nesting key
  — generating the MCP registration and pointing the harness at
  the schema and skills, mirroring how `install-sibling` already
  manages sentinel-fenced blocks. This delivers the
  agent-independence adapters the roadmap names.
- **Live reload on the rendered side**: a file watcher on `wiki/`
  triggers the existing regeneration and pushes a reload signal to
  the workbench page, so terminal-driven edits appear beside the
  terminal within seconds — the watch-and-apply spine of their
  design, with git as the sync layer instead of a CRDT.

## Rabbit holes

- **Building a desktop app.** Their terminal is Electron-only; ours
  is a browser page over a local bridge — no Electron, no packaged
  app, no auto-updater.
- **Exposing the PTY beyond loopback.** The terminal surface never
  ships in the serving profile; token + Host check even on
  localhost. If remote access is ever wanted, that's a new decision
  (probably "use SSH").
- **Conflating the human terminal with agent exec.** The terminal
  is the operator's full shell; agents keep reaching the brain
  through MCP and files. No allowlisted agent-shell surface gets
  built here.
- **Collaborative editing.** No CRDT layer — git and the file
  watcher are the sync; the workbench renders, it doesn't edit.
- **Session persistence/multiplexing.** One tab set, per-window
  lifetime; tmux exists for everything fancier.

## No-gos

- The workbench never lands in `BRAIN_SERVING=1` deployments.
- No harness becomes load-bearing: everything works from a plain
  terminal without the workbench, per the agent-independence
  principle.
- Launch registry and config adapters are data tables, not
  per-harness code paths.
