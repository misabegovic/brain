---
name: rebase
description: Cheap-rebase the active branch onto `origin/main`, auto-resolving `wiki/_views/` conflicts by re-running `brain.py views` (the regenerator is deterministic against the merged tree, so the regenerated output **is** the correct resolution). On conflicts in non-views paths (especially `wiki/index.md`) the rebase pauses and surfaces them — the operator resolves by hand. The force-push is **never** chained — the operator verifies the rebased commit and pushes separately, per `feedback_force_push_verify_commit.md`. Load when the user says "rebase", "pull main and resolve views", "another effort merged first, refresh my branch", or invokes `/rebase`. Pairs with `/spawn` (which creates the branches that need rebasing) and `/list-efforts` (which surfaces the in-flight queue).
---

# Rebase — cheap-resolve `wiki/_views/` conflicts after another effort merges

Parallel efforts cause `wiki/_views/pages.json` to be a
permanent merge-conflict point: every PR regenerates it. The
ADR at
[`wiki/brain/adrs/parallel-efforts-on-request.md`](../../../wiki/brain/adrs/parallel-efforts-on-request.md)
§ Decision committed to *not* moving views regen to a
post-merge CI job (rejected alternative); this skill is the
response — auto-resolve the views conflict via deterministic
regen, surface non-views conflicts for hand-resolution, never
chain the force-push.

## Local-first mode

If `.env` declares `LOCAL_FIRST=true`, this skill still works —
local rebases against `origin/main` (or whatever base) are
useful regardless of remote PR state, especially for keeping a
local feature branch in sync. The deterministic-views auto-
resolve runs unchanged. The "force-push is never chained" rule
becomes a no-op (no push happens at all under local-first); the
operator decides separately when (and whether) to push the
rebased branch.

## Inputs

| Form          | What it does                                                                                  |
|---------------|------------------------------------------------------------------------------------------------|
| `/rebase`     | Rebase the active branch onto `origin/main`, auto-resolving `wiki/_views/`.                   |
| `/rebase <base>` | Rebase onto `<base>` instead of `origin/main`. Rare — used for stacked branches.            |

## Pre-flight

1. **Branch sanity.** Refuse to rebase `main` or `master`
   onto themselves. The operator must be on a feature
   branch.
2. **Clean working tree.** Stash or commit pending changes
   before rebasing. The skill refuses if the tree is dirty
   (`git diff --quiet` and `git diff --cached --quiet` must
   both succeed).
3. **Fetch first.** `git fetch origin --prune` so the rebase
   target is current.

## Steps

1. **Run** `~/.local/share/mempalace-venv/bin/python3
   tools/brain.py rebase`. The command fetches origin,
   rebases the current branch, and on `wiki/_views/`
   conflicts auto-resolves by regenerating views against
   the merged tree.

2. **On clean rebase**: report the new HEAD SHA. Tell the
   operator the next step is *verify locally* (run the
   preflight gates) then `git push --force-with-lease`.
   Do **not** chain the push.

3. **On non-views conflict**: the rebase paused. Surface
   the unmerged paths exactly as `git diff --name-only
   --diff-filter=U` reports them. Common case is
   `wiki/index.md` — both efforts added a "What changed"
   bullet under the same date. The merge is usually
   additive: keep both bullets in chronological order
   (newest at top). Tell the operator to resolve by hand,
   then `git rebase --continue`.

4. **On unrecoverable state**: surface
   `git status` and tell the operator they can `git
   rebase --abort` to roll back. Do not auto-abort.

## Verify-before-chain discipline

Per `feedback_force_push_verify_commit.md` (operator-side
memory rule, captured here for in-skill self-reference): a
husky `commit-msg` hook rejection (or any pre-push
guardrail) does not always propagate cleanly through chained
operations. After the rebase succeeds, the operator must
verify `git log -1` shows the expected commit on the
expected branch *before* the force-push. This skill
deliberately stops short of the push — the verify step
isn't optional, and a chained push erases the operator's
chance to verify.

## Auto-resolution detail (`wiki/_views/`)

The regen guarantee:

- `brain.py views` walks the wiki tree, computes consumed_by
  edges + token counts, and writes
  `wiki/_views/{by-kind,by-team,by-repo,by-epic,ai-suggestions}.md`
  + `wiki/_views/pages.json`.
- The output is a **deterministic function of the wiki
  tree's frontmatter and content**. Two operators running
  it on the same tree produce byte-identical output.
- Therefore: when a rebase produces a merged tree state
  (everything except `wiki/_views/`), running views against
  *that* tree produces the correct `wiki/_views/` for the
  rebased branch. Accepting `theirs` first then regenerating
  is the same as a three-way merge for these files.

The implementation in `brain.py rebase`:

```
git checkout --theirs wiki/_views/<each-conflicted-file>
brain.py views
git add wiki/_views/
git rebase --continue
```

This is correct because the only thing `--theirs` would
discard is the rebased branch's stale view content — which
the regen replaces with the up-to-date content anyway.

## What this skill does NOT do

- **Does not push.** Force-push is the operator's separate
  step after verifying the rebased commit. Memory rule
  applies — verify before chain.
- **Does not auto-resolve `wiki/index.md`.** The
  home-pairing convention can't be safely auto-merged
  without semantic understanding of the bullet additions.
  Surface and stop.
- **Does not auto-resolve content conflicts** (`wiki/<repo>/`
  edits, `tools/`, `.claude/`). Those are real conflicts
  that need real resolution.
- **Does not abort on its own.** If the operator wants to
  give up, they `git rebase --abort` themselves.
