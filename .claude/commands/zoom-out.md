---
description: Per-work-item zoom-out brief — surface big-picture fit during deep focus. Two-half synthesis (technical + product), conversation-first, opt-in persistence.
---

Apply the `zoom-out` skill to: $ARGUMENTS

`$ARGUMENTS` formats:

- `<slug>` — brief on `wiki/<repo>/{prds,adrs}/<slug>.md`.
- `<wiki-relative-path>` — any wiki page (`permanent/architecture/foo.md`, `state.md`, etc.).
- `<sibling-repo-relative-path>` — a sibling-repo file or directory; the skill maps the path to its owning wiki pages via `pages.json`.
- `<PR#>` — in-flight work tied to a PR (brain or sibling-repo); the skill resolves PR → slug → wiki pages.
- (empty) — list the last 5 active work items from `log/log.md` and ask which to zoom out on.

The skill produces a two-half brief — a deterministic technical
zoom-out (hierarchy / cross-cutting / recent activity from
`pages.json` + `_overlaps/` + `log.md`) and an LLM-synthesised
single-paragraph product zoom-out grounded strictly in cited
brain pages (no hallucinated product features). The brief
renders in the conversation by default; the user opts in to
persistence (*"save it"*, *"add to the ADR"*, etc.) and the
captured output lands as a `## Big-picture fit` section wrapped
in a Starlight `:::note` aside on the relevant PRD/ADR.

Auto-fired at `/shape` Phase 1 → 2 and Phase 2 → 3 boundaries
(per the ADR's day-one auto-fire rule); manual elsewhere
(including `/continue`'s pre-push case for v1).
