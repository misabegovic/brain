---
name: wiki-lint
description: Lint the brain wiki — verify every index.md entry exists, find orphan pages (on disk but not in index.md), flag stale `updated:` dates, flag contradictions across pages, fix mechanical issues, and surface judgement calls to the human in a log.md line. Load when the user says "lint", "check the brain", "find broken links", "find stale pages", or otherwise asks for a sweep.
---

# Lint the brain

A periodic sweep that keeps the wiki coherent. Mechanical issues get fixed
silently; judgement calls get surfaced to the human in a single `log/log.md`
line so they can decide.

## Protocol

### 1. Index integrity

Walk every entry in `wiki/index.md`:

- For each `[Title](path)`, confirm the file exists. If it doesn't:
  - Was it renamed? Search for the title — if found, fix the link.
  - Was it deleted? Remove the entry.
  - Either way, log the action.
- Note any duplicate links to the same page in different sections.

### 2. Orphan pages

Find every `*.md` under `wiki/` (including topic subfolders), excluding
`wiki/index.md`. For each:

- If it's not in `wiki/index.md` *and* nothing else links to it, it's an orphan.
- If it has actual content, add it to `wiki/index.md`. If it's a stub, ask the
  human whether to delete or expand.

### 3. Frontmatter validity

For each wiki page, confirm:

- Frontmatter exists and has `title`, `status`, `sources`, `updated`.
- `updated` is a real ISO date in the past or today.
- `status` is one of `draft | living | superseded | archived`.
- `sources:` is non-empty unless `status: draft`. (A draft can be
  sourceless temporarily.)

Fix anything mechanical. List exceptions in the lint log line.

### 4. Stale-date flag

Compare each page's `updated:` to today. Flag pages older than 90 days for
human review *only if* the underlying source has changed:

```bash
# Did the cited sibling repo move since the page was last updated?
git -C ~/projects/<repo> log --since="<page updated date>" --oneline | head
```

Don't churn dates for pages whose source hasn't moved — the wiki's value is
durability, not freshness theater.

### 5. Contradiction sweep

For pages that overlap (same entity, same concept), look for direct
contradictions:

- Different version numbers for the same dependency.
- Different ownership claims.
- Different decision outcomes.

Surface contradictions in the lint log line with both citations. Don't
unilaterally pick a winner — the human decides.

### 6. Source-citation sweep

Spot-check claims that look load-bearing. If a claim is uncited or its
citation is broken (file moved, URL 404), mark it inline:

```
... the monolith uses Avo for admin (unverified, 2026-04-29).
```

### 7. Log

One `log/log.md` line covering the whole sweep:

```
YYYY-MM-DD lint — <N pages walked, M issues fixed, K surfaced>: <one-line
summary of surfaced issues>
```

If anything was surfaced for human judgement, list it under the lint line in
a short bulleted block — don't wait for a question, the user will see it
next time they open the repo.
