---
name: spawn
description: Opt-in parallel-effort spawn — create a brain worktree on a fresh branch off `main`, optionally create parallel worktrees on parallel branches in named sibling repos, write a per-effort registry record at `wiki/_state/efforts/<slug>.json`, and surface the spawned paths so the agent (or user) can `cd` in and work without disturbing the primary checkout. Default brain workflow remains single-effort, single-checkout; `/spawn` is the only entry path to parallel efforts. Load when the user says "spawn", "parallel effort", "in parallel", "fresh worktree", "new effort", or invokes `/spawn`. Pairs with `/list-efforts` (read the registry) and `/rebase` (cheap-rebase through `wiki/_views/` conflicts when another effort merges first).
---

# Spawn — opt-in parallel-effort workspaces

You are working in `~/projects/brain`. This skill is the **only**
path to parallel efforts in the brain. Default behaviour of
every other skill is unchanged: single effort, single checkout.
When the user explicitly asks for parallel work, `/spawn`
creates the isolated workspaces and registers the effort.

The decision shape this skill implements is recorded in
[`wiki/brain/adrs/parallel-efforts-on-request.md`](../../../wiki/brain/adrs/parallel-efforts-on-request.md).

## Local-first mode

If `.env` declares `LOCAL_FIRST=true`, worktree + branch creation
runs unchanged — parallel local workspaces are useful regardless
of remote state. What changes:

- The owner-subagent's drive-to-merged-PR loop **collapses to
  drive-to-local-commits**: the owner does its deepdive, lands
  the work as commits in the worktree, surfaces the diff to the
  operator, and stops. No `gh pr create`, no `/pr` chain.
- `gh pr list --search "<slug>"` collision detection still runs
  (it's read-only and useful — a teammate's open PR with the
  same slug is still a signal).
- Registry record (`wiki/_state/efforts/<slug>.json`) is written
  unchanged. The `phase` field reads "local" in place of
  PR-derived phases until the operator pushes.

## Inputs

| Form                                                      | What it does                                                                                       |
|-----------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `/spawn <slug>`                                           | Create brain worktree only at `.claude/worktrees/<slug>/` on branch `agent/<slug>-<timestamp>`.    |
| `/spawn <slug> --target <repo>`                           | Brain worktree + a sibling-repo worktree at `~/projects/<repo>/.claude/worktrees/<slug>/`.         |
| `/spawn <slug> --target <repo1>,<repo2>`                  | Brain worktree + sibling-repo worktrees in each named active sibling repo.                         |
| `/spawn <slug> --target <repo> --notes "<freeform>"`      | Above + record freeform notes in the registry record (PR pointers, parent ADR, etc.).              |
| `/spawn <slug> --no-owner`                                | Skip the mandatory owner-subagent dispatch — the operator (or a later run) drives the effort inline. See § Opting out of owner dispatch. |
| `/spawn` (no args)                                        | Ask the user for a slug.                                                                            |

## Pre-flight

1. **Slug shape.** Validate kebab-case, ≤ 6 words, no leading
   numeric prefix (per AGENTS.md § ADR / PRD filenames). If
   shape is wrong, normalise silently and proceed
   (`feedback_slug_delegation.md` — slug-picking is delegated;
   don't ask the user about it).

2. **Cross-PR slug uniqueness.** Query
   `gh pr list --state all --search "<slug>"` against the brain
   repo. If a PR exists whose head ref matches `agent/<slug>-*`
   or whose body / title contains the slug as an effort name,
   the slug collides. Re-slug (append a discriminator from the
   notes, e.g. `<slug>-v2`) and retry. The cross-PR check is
   the v1 enforcement of the slug uniqueness commitment in the
   ADR; it doesn't yet span sibling repos (that's a follow-up
   if collisions surface there).

3. **Active scope check for targets.** Each `--target` repo
   must be in active scope per AGENTS.md § Active scope (8
   repos as of 2026-05-07). Reject targets that are
   `archived` or `not ingested`.

4. **Sibling-repo handling for targets.** For each `--target`
   repo, the sibling repo's primary checkout must satisfy
   AGENTS.md § Sibling-repo handling: on `main`/`master` with
   clean tree. The skill calls `tools/sync-siblings.sh` (or
   the same checks inline) to verify. If a sibling repo is
   on a feature branch or has uncommitted state, **stop and
   surface** — do not switch branches or stash. Ask the user
   whether to skip that target or pause to clean up.

5. **Branch protection on `main`.** `main` is protected; the
   spawn step never pushes to `main`. The new effort branch is
   created from `main`'s tip but pushed under
   `agent/<slug>-<timestamp>`.

## Steps

1. **Brain worktree.** From the brain's primary checkout:

   ```bash
   git fetch origin --prune
   TS=$(date -u +%Y%m%dT%H%M%S)
   BRANCH="agent/<slug>-$TS"
   WT="$(git rev-parse --show-toplevel)/.claude/worktrees/<slug>"
   git worktree add -b "$BRANCH" "$WT" origin/main
   ```

   The worktree path uses the slug (not the agent UUID
   pattern of the existing locked worktrees) — the slug is
   the identifier going forward.

2. **Sibling-repo worktrees** (per `--target` repo, if any).
   For each target `<repo>`:

   - **Bootstrap** if absent: ensure
     `~/projects/<repo>/.claude/worktrees/` exists; create
     it lazily on first spawn for that sibling repo
     (per the lazy-bootstrap rule in the ADR § Decision).
   - **`.gitignore` line**: ensure the sibling repo's
     `.gitignore` contains `.claude/worktrees/` (a single
     line). If absent, add it on the **brain effort's
     branch view of the sibling repo's worktree** — *not*
     committed to the sibling repo's `main`. The spawn step
     surfaces the `.gitignore` gap; closing it is the
     effort's first sibling-repo commit.
   - **Worktree**: from the sibling repo's primary
     checkout:

     ```bash
     cd ~/projects/<repo>
     git fetch origin --prune
     git worktree add -b "$BRANCH" \
       "$PWD/.claude/worktrees/<slug>" origin/main
     ```

     Same branch name as the brain side. Two parallel
     efforts on the same sibling repo each get their own
     branch + worktree because the `<slug>` and `$TS`
     differ.

3. **Registry record.** Write the effort to
   `wiki/_state/efforts/<slug>.json`. Use:

   ```bash
   ~/.local/share/mempalace-venv/bin/python3 tools/brain.py \
     efforts set <slug> \
     --brain-branch "$BRANCH" \
     --brain-worktree "$WT" \
     --targets <repo1> <repo2> \
     --target-branch "<repo1>=$BRANCH" \
     --target-worktree "<repo1>=~/projects/<repo1>/.claude/worktrees/<slug>" \
     --notes "<freeform>"
   ```

   The record is created on the new brain worktree's branch.
   It is **not** committed yet — the operator's first
   commit on that branch (typically `/shape`'s Phase 1 PRD
   or the consumer skill's first artefact) sweeps it in.

4. **Dispatch the owner subagent (mandatory; opt-out
   `--no-owner`).** Parallel-first is the brain's default
   execution route — every spawn ships with a background owner
   subagent that runs the effort end-to-end (deepdive → author
   → push → watch CI → merge → audit follow-up) per
   [`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md).
   The dispatching agent loads
   [`tools/templates/owner-subagent-prompt.md`](../../../tools/templates/owner-subagent-prompt.md),
   substitutes the placeholders (`{{slug}}`, `{{phase}}`,
   `{{branch}}`, `{{worktree_path}}`, `{{depends_on}}`,
   `{{deepdive_targets}}`, `{{decision_under_authority}}`,
   `{{completion_contract_targets}}`), and fires the owner.
   Capture the owner's agent identifier and immediately update
   the registry record:

   ```bash
   ~/.local/share/mempalace-venv/bin/python3 tools/brain.py \
     efforts set <slug> \
     --owner-agent-id "<id>" \
     --owner-state active \
     --owner-dispatched-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
   ```

   If the operator passed `--no-owner`, **skip** the dispatch
   and instead set `--owner-state none-dispatched` on the same
   registry write. Per the ADR § Decision > *Opt-out flag
   spelling*, the explicit `none-dispatched` value lets
   `/list-efforts` distinguish opted-out from pre-dispatch from
   no-longer-active.

5. **Surface the spawned paths.** Print one line per worktree
   created, with the absolute path, plus the registry
   record's location, plus the dispatched owner's id (or
   `--no-owner` if suppressed), plus a one-line "what to do
   next" (typically: `cd <brain-worktree>; /shape <repo>
   <pitch>` when the operator is taking over inline; otherwise
   "owner subagent dispatched; tail with `/list-efforts`"). End
   with the `/list-efforts` command in case the user wants to
   verify.

## Opting out of owner dispatch

`--no-owner` is the sole opt-out. The flag accepts no
arguments; it is a boolean suppressor of step 4's dispatch.
Use it when:

- The operator is going to drive the effort inline themselves
  in the same session — typically the user explicitly says
  *"I'll run this one"* or *"keep me in the loop turn-by-turn"*.
- The dispatch infrastructure is unavailable in the current
  session (a reduced-capability harness, an interactive-only
  context, etc.).
- The slug is being spawned for staging-only purposes — the
  worktree exists for a manual experiment, not an end-to-end
  build.

The flag's effect is recorded as `owner_state: none-dispatched`
in the registry record so downstream surfaces (`/list-efforts`,
`/sync` reconcile) read *"explicitly opted out"* rather than
*"owner dispatched but no longer active"*. There is no
`--manual-owner` or `--solo` variant — those flag spellings
were considered and rejected in the ADR's § Alternatives on
self-documentation grounds.

## Output convention

```
spawned: <slug>
  brain    : <abs-brain-worktree>  (branch <BRANCH>)
  target   : <repo>  →  <abs-sibling-worktree>  (branch <BRANCH>)
  registry : wiki/_state/efforts/<slug>.json  (uncommitted)
  owner    : <agent-id>  (state=active)         # or `--no-owner` if suppressed

next:
  # owner subagent is running in the background; tail with /list-efforts
  # operator inline mode (--no-owner): cd <abs-brain-worktree>; /shape <repo> <pitch>
  # later: /rebase to pull main + auto-resolve wiki/_views/ conflicts
```

## What this skill does NOT do

- **Does not commit anything to `main`.** Branch protection
  on `main` is enforced; spawn writes to feature branches
  only.
- **Does not push the new branch yet.** The first push
  happens when the operator runs `/pr` after authoring
  some content in the spawned worktree.
- **Does not pre-commit the registry record.** The record
  lives uncommitted in the worktree's working tree until
  the operator's first commit on the effort's branch.
- **Does not modify the user's primary brain checkout's
  branch.** `/spawn` creates a worktree; the primary
  checkout's branch is unchanged.
- **Does not switch branches in any sibling repo's primary
  checkout.** Per AGENTS.md § Sibling-repo handling — only
  reads, never switches.
- **Does not detect "this should be parallel" and offer
  spawn unprompted.** Explicit user opt-in is the only
  entry path *to the workspace layer* (per
  [`wiki/brain/adrs/parallel-efforts-on-request.md`](../../../wiki/brain/adrs/parallel-efforts-on-request.md)
  § Consequences > Closes). At the *execution* layer the rule
  is reversed — once a `/spawn` happens, owner-subagent
  dispatch is automatic, opt-out via `--no-owner`. The
  partial supersession is recorded in
  [`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md)
  § Consequences > Partial supersession of the parent ADR.

## Observed-state checks before reporting success

1. `git -C <brain-worktree> rev-parse --abbrev-ref HEAD`
   returns the new branch name.
2. For each target repo: `git -C <sibling-worktree>
   rev-parse --abbrev-ref HEAD` returns the new branch name.
3. `cat wiki/_state/efforts/<slug>.json` returns valid JSON
   matching what was written.

If any check fails, the spawn is incomplete; report the gap
and offer to roll back (`git worktree remove`).

## Cleanup

Cleanup is the operator's `/sync` step's job, not `/spawn`'s.
When an effort's PR merges, `/sync` reconciles by reading
the registry against `gh pr view --json mergedAt` for each
recorded PR; merged efforts have their registry record
flipped to `status: merged` and their worktrees reaped.
Abandoned efforts are flipped to `status: abandoned`
manually (`brain.py efforts mark <slug> abandoned`) and
then reaped. Stale worktrees with no matching registry
record are flipped to `status: orphaned` and reaped on the
same `/sync` pass.
