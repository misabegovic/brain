---
title: "Operator musing — explore SQLite for the views layer"
captured: 2026-07-10
kind: conversation-snapshot
participants: [operator, brain-agent]
---

# Operator (2026-07-10, on the composable-views pitch)

> idk... we could also explore using sqlite

Agent's read at capture time: SQLite as *source of truth* breaks the
markdown+git thesis (binary in git: no diffs, no merges, no agent
ergonomics). SQLite as a **derived, regenerable, gitignored index**
strengthens the pitch: SQL replaces the invented block-filter
language, FTS5 upgrades search, tabular connector extracts become
joinable, and Datasette becomes a candidate read-only serving
surface. Discipline: single writer (the indexer), read-only
consumers, disposable by construction — files stay the only truth.
