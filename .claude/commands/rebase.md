---
description: Cheap-rebase the current branch onto origin/main, auto-resolving wiki/_views/ via deterministic regen
---

Apply the `rebase` skill.

`$ARGUMENTS` is currently unused; the skill rebases the active
branch onto `origin/main` and force-push is **not** chained —
the operator runs `git push --force-with-lease` separately
after verifying the rebased commit (per
`feedback_force_push_verify_commit.md`'s verify-before-chain
rule).

If the rebase hits conflicts in `wiki/_views/`, the skill
re-runs `brain.py views` and accepts the regenerated output.
If conflicts hit non-views paths (especially `wiki/index.md`),
the rebase pauses and the operator resolves by hand — the
skill surfaces the conflicting paths but does not attempt
auto-resolution.
