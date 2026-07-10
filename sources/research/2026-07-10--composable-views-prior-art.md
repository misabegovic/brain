---
title: "Research — prior art for composable views over knowledge corpora"
captured: 2026-07-10
kind: research-note
method: web research (agent)
---

# Prior art: user-composable views

**Obsidian Dataview → Bases.** Dataview (~3M installs): loved
syntax, hated performance (whole-vault freezes; index cost) and
brittleness; read-only output; stagnated. Official successor
**Bases**: a `.base` YAML spec — shared `filters`/`formulas` +
multiple named `views` with local overrides — GUI-editable, fast on
50k-note vaults, and **frontmatter-properties only** (inline fields
lost the ecosystem fight). <https://obsidian.md/help/bases/syntax>

**Logseq.** Advanced queries in Datalog are the cautionary tale:
"pretty alien", non-coders gave up, even programmers refused the
learning curve; three query tiers confused everyone. Lesson:
familiarity beats power; two tiers, not three.

**Notion.** View = layout + filters + sorts + grouping, all local to
the view, many views per source — the UX bar. Export drops exactly
the computed layer (views/rollups/formulas) — the lock-in. View
specs as git files rendered to markdown is the anti-Notion on
portability.

**org-mode.** `org-agenda-custom-commands`: named saved searches,
composable blocks, per-view option overrides — the layering that
survived 20+ years; limited only by specs living in elisp.

**SQL-over-files.** Datasette canned queries (SQL + params in YAML →
pages/APIs; datasette-query-files stores them as .sql files) and
**Steampipe** (schema-per-connector foreign tables — `github.*`,
`datadog.*` — with cross-plugin joins) validate both halves of the
design. octosql's custom engine = missing features; don't build an
engine. **Evidence.dev** ("BI as code": named SQL blocks in markdown
→ static pages) validates queries-render-markdown.

**LLM-era.** Read-only SQLite over MCP is a default pattern; agents
discover schema and write SQL — which neutralizes SQL's residual
friction for non-technical users (the agent authors the spec).

**Design lessons.** Copy Bases' file anatomy (shared filters +
named views with overrides); copy Steampipe's schema-per-connector;
avoid inventing query languages (Logseq) and engines (octosql);
index frontmatter, not inline syntax; keep the index fast and
disposable (Dataview died on index perf); render results back into
the corpus; two tiers — simple filter form + full SQL.
