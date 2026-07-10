---
name: sync
description: One-shot health sweep of the brain — runs sync-siblings (git-fetch each sibling, list new commits), wiki-lint (broken links, orphans, stale dates, contradictions), check-sources (verify every sources: citation resolves), brain.py validate (frontmatter conformance), and brain.py views (regenerate pages.json + auto indices). Replaces standalone /lint. Load when the user says "sync", "lint", "sweep", "check the brain", "is the brain healthy", or invokes `/sync`.
---

# Sync — one-shot health sweep of the brain

Runs everything that keeps the brain coherent in a single pass. Use
this whenever you finish a batch of ingests, before / after a `/schedule`d
routine, or just want a clean baseline before publishing to the UI.

## Steps

Run each step. If a step surfaces issues, log them under that step but
**keep going** — the goal is one consolidated sweep, not bail-on-first-
error.

**Helper fan-out (parallel-first).** When a step has parallel shape —
the sibling-repo sweep across eight active repos in step 1, the
broken-citation walk across many pages in step 3, the registry
reconcile across multiple in-flight efforts in step 6 — default to
fanning out helper subagents in a single message rather than serial
tool calls. Per
[`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md).

### 1. Sibling-repo sync

```bash
tools/sync-siblings.sh
```

Reports per-repo: commits since the last brain ingest/mine that named
that repo, plus the first 5 commit subjects. Repos with > 0 new commits
are candidates for `/in <repo>` after the sweep.

### 2. Wiki lint

Apply the `wiki-lint` skill in full:

- index integrity (every entry exists; no dead links)
- orphan pages (on disk but not in `wiki/index.md`)
- frontmatter validity
- stale-date flag (only if upstream sources moved)
- contradiction sweep across overlapping pages
- source-citation spot check

Surface judgement calls in the consolidated log line at the end.

### 3. Source-link check

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py check
```

Walks every page's `sources:` frontmatter, verifies each path/URL
resolves. Add `--no-net` if offline or the network is flaky. Broken
sources go into the consolidated log line.

### 4. Schema validate

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py validate
```

Frontmatter conformance, required-section presence per kind,
`depends_on` / `supersedes` / `superseded_by` referential integrity,
orphans, dead index links. Must exit 0 — if not, fix before continuing
(this is structural, not stylistic).

### 5. Reflection-check — drift detectors

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py reflection-check
```

Runs the deterministic drift detectors:

- `links` — every wiki/-internal markdown link resolves.
- `confidence-floor` — `confidence: high` pages > 30 days old.
- `active-scope` — AGENTS.md table matches `wiki/<repo>/` folders.
- `supersedes-cycles` — `superseded_by:` chains have no cycles.
- `page-size` — pages > 500 lines (advisory; not enforced).
- `sources-exist` — every `sources:` path resolves on disk.
- `sync-drift` — sibling-repo HEAD vs cursor commit-count delta.
- `epic-children` — `parent_epic:` claims resolve and the epic
  page mentions the child by slug.
- `sources-immutability` — `sources/` tree has no modifications
  vs git baseline.

Findings are warnings, not errors. Surface them; act on them as
part of the sweep where they're cheap to fix (broken links,
orphaned epic-children, stale sources). Defer judgment-heavy
findings (page-size on epics; confidence-floor demotion) to
`/groom`.

### 6. Regenerate views

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py views
```

Refreshes `wiki/_views/by-{kind,team,repo}.md` and `pages.json` (the
data layer the UI consumes). Always run last so views reflect any
fixes from earlier steps.

### 7. Reconcile parallel-effort registry

If `wiki/_state/efforts/` contains records, walk each:

1. **Match against open PRs.** For each record with a recorded
   `brain_pr` or `target_prs`, run `gh pr view <pr> --json
   mergedAt,state` and update the record's `status` accordingly:
   - All recorded PRs `mergedAt` non-null → `status: merged`.
   - Any recorded PR `state: CLOSED` and `mergedAt` null → keep
     `status: in-flight` and surface for the operator (was
     the PR abandoned or just closed without merge?).
2. **Detect orphaned worktrees.** Walk `git worktree list` (in
   the brain primary checkout *and* in each sibling repo whose
   `.claude/worktrees/` exists). Worktrees whose path doesn't
   match any registry record's `brain_worktree` /
   `target_worktrees` are **orphaned** — surface them, don't
   auto-reap.
3. **Surface stale registry records.** Records older than 90
   days with `status: merged` or `status: abandoned` get
   archived under `wiki/_archive/efforts/<slug>.json` (move,
   not copy) — keeps `wiki/_state/efforts/` scoped to
   recent-and-active efforts.

Use `~/.local/share/mempalace-venv/bin/python3 tools/brain.py
efforts list --json` to read records; `efforts mark <slug>
<status>` to update; `mv` for the archive step. The reconcile
step runs after the views regen so any `wiki/_archive/efforts/`
moves are reflected in the regenerated index.

### 8. Rotate the operations log if oversized

`log/log.md` grows monotonically. When it crosses **2,000 lines** (or
~200 KB), `/sync` rotates it — this step is mechanical, no judgement:

1. Move the current `log/log.md` to `log/archive/log-YYYY-MM-DD.md`
   (date = today, the day rotation runs).
2. Create a fresh `log/log.md` whose first two lines are:

   ```
   # Operations log
   Previous: log/archive/log-YYYY-MM-DD.md
   ```

Archived log files are read-only after rotation; never edit them.
Search across the full history with `grep -r "<query>" log/`.

## Log

Single consolidated log line:

```
YYYY-MM-DD sync — siblings:<N moved>, lint:<N issues fixed/M surfaced>,
   check-sources:<N broken>, validate:<ok|N errors>, views:<regenerated>
```

If the sweep surfaced anything that needs human judgement (a
contradiction, an orphan to delete vs expand, a broken upstream URL),
add a short bulleted block under the line.

## Done check

- [ ] All five steps ran (none silently skipped).
- [ ] `brain.py validate` exited 0 by the end.
- [ ] `wiki/_views/` was regenerated.
- [ ] `wiki/index.md` § What changed updated with merge events
      since the last sync; § Brain trajectory rewritten if the
      brain's trajectory has materially shifted. Per
      [`wiki/brain/adrs/home-content-shape.md`](../../../wiki/brain/adrs/home-content-shape.md):
      every wiki/ edit must be paired with a wiki/index.md edit.
- [ ] One consolidated `sync —` line in `log/log.md`.
- [ ] Anything that needs human judgement is surfaced under that line.
