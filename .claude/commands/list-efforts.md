---
description: List in-flight (and recent) parallel efforts — joins `wiki/_state/efforts/` with `gh pr list` to surface the cross-repo state of each effort
---

Apply the `list-efforts` skill.

`$ARGUMENTS` is currently a status filter or empty:
- `/list-efforts` — list all efforts (in-flight first, then merged, abandoned, orphaned).
- `/list-efforts in-flight` — only currently-running efforts.
- `/list-efforts merged` — only completed efforts (audit view).
- `/list-efforts orphaned` — efforts whose worktree exists but no PR or registry consistency.

Surface, for each effort: slug, status, brain branch, brain PR
(if any), per-target sibling-repo PRs, spawn age, notes.
