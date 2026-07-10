---
title: "Brain — home"
kind: meta
status: draft
updated: 2026-07-10
confidence: high
sources:
  - ../AGENTS.md
---

# Brain — home

An empty brain shell — an LLM-maintained knowledge base awaiting its
organisation's content. Fill `brain.config.yml`, add per-repo
shelves under `wiki/<repo>/`, and the dashboard sections below
start filling in as the slash-command surface runs.

## What changed

<!-- home-section; maintained-by: /shape -->
- **2026-07-10** — kernel hardening from the ADR review: the
  client-specific compliance countdown became a generic
  `deadline-countdown` op over `wiki/_state/deadlines.json`, the
  state-refresh schedule ops now bootstrap from `brain.config.yml`
  and no-op cleanly on an empty shell, and a new `internal-refs`
  reflection detector enforces the standalone guarantee.
- **2026-07-10** — kernel decision trail ported: 11 brain-meta ADRs,
  the authoring guidance page, and the org methodology shelf
  (way-of-working, development playbook, superpowers) landed in
  sanitized, organisation-agnostic form. The shell is now fully
  standalone — every internal reference resolves.

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Open initiatives

<!-- home-section: empty; maintained-by: /shape -->
*(empty — no /shape run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Recent decisions

<!-- home-section; maintained-by: /shape -->
- [Kernel ADR trail](brain/index.md#adrs) — 11 mechanism decisions
  (shape pitches, epics, deepdive pre-flight, parallelism, zoom-out,
  home shape, UI substrate, operator lessons, competitor intel)
  recorded 2026-07-10 as ports from the origin deployment.

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Drift surface

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no /groom run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Insights now

<!-- home-section: empty; maintained-by: /feedback -->
*(empty — no /feedback run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Brain trajectory

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no /groom run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Curated picks

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no /groom run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Where to find things

- [Brain — meta level](brain/index.md)
- [Org — methodology + cross-product](org/index.md)
- Per-repo shelves arrive as you add them: `wiki/<repo>/index.md`
