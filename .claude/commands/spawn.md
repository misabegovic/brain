---
description: Opt-in parallel-effort spawn — create a brain worktree (and optional sibling-repo worktrees) on a fresh branch, register the effort
---

Apply the `spawn` skill to: $ARGUMENTS

`$ARGUMENTS` is the effort slug (kebab-case, ≤ 6 words),
optionally followed by `--target <repo[,repo…]>` to also spawn
worktrees in named sibling repos, and optionally `--notes
"<freeform>"` to record context with the registry record.

Examples:

- `/spawn search-revamp` — brain worktree only
- `/spawn search-revamp --target app` — brain + one sibling repo
- `/spawn org-compliance-followups --target app,api
  --notes "implementing record-keeping substrate"`

If `$ARGUMENTS` is empty, ask the user for a slug. Run the full
protocol: pre-flight (slug uniqueness across open PRs;
sibling-repo handling for each target), brain worktree creation,
optional sibling-repo bootstrap + worktree creation, registry
record write at `wiki/_state/efforts/<slug>.json`, surface the
spawned paths.
