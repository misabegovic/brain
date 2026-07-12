---
description: Universal ADR/PRD authoring path — forward (pitch→PRD→ADR→build) or record-existing (decision→ADR)
---

Apply the `shape` skill to: $ARGUMENTS

`$ARGUMENTS` formats:

**Forward mode** (default — pitch becomes future work):

- `<scope> <inline pitch>` — full run; `<scope>` is one of the active repos declared in `brain.config.yml` (mirrored in `AGENTS.md` § Active scope) or the meta-scopes `org` / `brain`.
- `<scope> --from-notion <url>` — pitch sourced from a Notion page.
- `<scope>` — list the scope's open pitches and ask which to shape.

**Record-existing mode** (capture a decision the code already encodes):

- `<repo> --record <description>` — describe the decision in line.
- `<repo> --record --from-notion <url>` — past decision recorded in Notion.
- `<repo> --record --from-source <repo-relative-path>` — decision encoded in sibling-repo source.

**Epic mode** (umbrella-scale multi-PRD initiative — produces a `kind: epic` page, no umbrella ADR pair):

- `<scope> --epic <inline pitch>` — author a new umbrella at `wiki/<scope>/epics/<slug>.md`. Children spawn later via regular forward `/shape <scope> <child-pitch>`, with the pre-flight epic-detection question surfacing the umbrella as a candidate parent.
- `<scope> --epic --from-notion <url>` — Notion-sourced umbrella pitch.

(empty) — list active repos and ask which one.

`/shape` is the *only* skill that writes to `wiki/<repo>/prds/`, `wiki/<repo>/adrs/`, or `wiki/<scope>/epics/`. `/in` hands off here when it spots pitches or pre-existing decisions. Refuse anything outside active-scope repos.
