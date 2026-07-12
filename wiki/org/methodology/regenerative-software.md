---
title: "Regenerative software — the Phoenix Architecture and how the brain maps to it"
kind: reference
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../../sources/web/aicoding-fowler-phoenix--f0e11r.md
  - https://aicoding.leaflet.pub/
---

# Regenerative software (Phoenix Architecture)

> Agent-authored synthesis of Chad Fowler's *The Phoenix
> Architecture* (ingested 2026-07-10), and the mapping onto this
> brain's mechanism.

## The framework in brief

Generative AI makes implementations cheap and disposable; the asset
shifts to **the organizational system** — constraints, evaluations,
architecture, decision rationales — which must survive while code
cycles. Architecture is defined by *what you can't delete*. The
practical tests: the **deletion test** (a component you can't safely
remove is debt), **n=1** (architecture a single developer can't
operate isn't worth preserving), **conceptual mass** ("small means
safe to delete" — which also cuts token cost). Production
**implementation remembers** lessons never written down (timeouts,
retries, validations); observability feeds regeneration.
**Provenance beats version control**: the unit of change is the
decision rationale, not the diff. "Better shapes beat better
prompts."

## How the brain maps to it

- **Specs as the maintained artifact** → the wiki's permanent +
  trail layers (mission #1).
- **Provenance over version control** → the topics shelf
  (discussion trails), the ADR/PRD trail, and the attributed audit
  log — the brain's unit of change is already the rationale.
- **Architectural-primitives registry** → `permanent/constraints.md`
  per repo (added with this ingest): what cannot be deleted or
  violated, and why.
- **The implementation remembers** →
  `permanent/implementation-memory.md` per repo (added with this
  ingest): the runtime's undocumented lessons, catalogued with
  their causes.
- **Evaluations as the real codebase** → constraint-class assets;
  the brain's own gates (validator, reflection detectors, tests)
  are its evaluation suite.
- **Production as compiler input** → the connector plane (Datadog
  monitor state et al.) feeding state extracts and views.
- **Conceptual mass** → the page-size discipline and the kernel's
  zero-dependency posture.
- **Pace layers** → roadmap slices regenerate at different
  cadences; the UI is deliberately the conservation layer.

## What the brain does not adopt

Full code-regeneration automation (the brain records what
regeneration needs; performing it stays agent-and-operator work),
and any weakening of the immutable-sources rule — snapshots are the
one thing that is *never* regenerated.
