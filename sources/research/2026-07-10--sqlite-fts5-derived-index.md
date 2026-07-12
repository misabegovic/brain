---
title: "Research — SQLite/FTS5 as the derived-index substrate"
captured: 2026-07-10
kind: research-note
method: web research (agent) + local verification
---

# SQLite/FTS5 for a rebuild-from-scratch index

**Table type.** External-content FTS5 (`content='pages'`) is the fit
for a disposable index: stores only the FTS index, keeps
highlight()/snippet(), and — single-writer — needs no triggers: bulk
insert, then one `INSERT INTO fts(fts) VALUES('rebuild')`.
Contentless forbids column reads and the rebuild command; plain FTS5
duplicates text. <https://www.sqlite.org/fts5.html>

**Tokenizer.** `unicode61 tokenchars '-_'` keeps `fast-track-v1` and
`json_extract` as single tokens (markdown prose + code identifiers);
porter wrapper optional for stemmed recall; skip trigram (3× index
size for substring search we don't need).

**Ranking.** `ORDER BY rank` (bm25 default, scores negative — sort
ascending); per-column weights via `bm25(fts, w_title, w_body)`;
`snippet(fts, -1, …)` for previews.

**Availability (verified locally).** Ubuntu 24.04 system Python
3.12.3 links SQLite 3.45.1 with ENABLE_FTS5; JSON functions are core
since 3.38. Floor: SQLite 3.38.

**Schema patterns.** Scalar columns for query-driving fields + one
JSON column for the frontmatter long tail (`json_extract`/
`json_each`); tags as JSON arrays (no junction tables at ~5k pages);
`links(src, dst)` indexed on BOTH endpoints (recursive CTEs collapse
otherwise); orphans = anti-join; transitive deps = `WITH RECURSIVE …
UNION` (cycle-safe).

**Rebuild performance (benchmarked on this machine).** 50k ~200-word
rows: 0.12 s insert (one transaction + executemany), 1.43 s full
FTS5 rebuild, 161 MB. Pragmas for throwaway builds:
`synchronous=OFF`, `journal_mode=MEMORY` (not WAL — no sidecar
files).

**Pitfalls.** FTS5 MATCH is its own query language — quote each
whitespace-split user token as `"tok"` (double internal quotes)
before matching; never pass raw strings.
<https://blog.haroldadmin.com/posts/escape-fts-queries>. Build to
`index.db.tmp` then `os.replace()` — atomic, always compact, old
readers unaffected; never VACUUM, never UPDATE. Readers open
`file:index.db?mode=ro`. `executescript()` implicitly commits —
keep DDL separate from data loads.
