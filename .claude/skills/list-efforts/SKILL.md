---
name: list-efforts
description: List in-flight (and recent) parallel efforts in the brain. Walks `wiki/_state/efforts/<slug>.json` records (across the primary checkout and any spawned worktrees), joins each against `gh pr list` for the brain repo and any recorded sibling repos, and surfaces the cross-repo state — slug, phase (derived from PR state), brain PR, per-target sibling-repo PRs, branches, worktree paths, spawn age, status. Read-only; never mutates registry records (use `/sync` for reaping). Load when the user says "list efforts", "what's in flight", "what am I working on", "show parallel work", "list spawns", or invokes `/list-efforts`. Pairs with `/spawn` (which creates effort records) and `/sync` (which reconciles records against PR state).
---

# List efforts — what's in flight

Read-only surface for the parallel-effort registry. The decision
shape this skill reflects is recorded in
[`wiki/brain/adrs/parallel-efforts-on-request.md`](../../../wiki/brain/adrs/parallel-efforts-on-request.md).

## Sources of truth (in priority order)

1. **Per-worktree registry records.** Each spawned worktree's
   `wiki/_state/efforts/<slug>.json` reflects the effort's
   intent. The operator's primary brain checkout doesn't have
   the in-flight effort's record on its branch (`main`) until
   the effort merges, so this skill walks `git worktree list`
   and reads each worktree's record.
2. **`main`'s registry directory.** `wiki/_state/efforts/`
   on `main` contains records of efforts whose work has
   merged (status flipped by `/sync`). This is the audit
   trail.
3. **GitHub PR state.** `gh pr list --state all --search
   "<slug>"` for the brain repo and (per record) for each
   recorded sibling repo. Joins the registry's branch /
   slug to live PR state for the surfaced phase.

## Steps

1. **Walk worktrees.** `git worktree list --porcelain` from
   the brain's primary checkout. For each worktree path
   (skip the primary checkout itself): read
   `<worktree>/wiki/_state/efforts/<slug>.json` if present.
   The `<slug>` segment can be inferred from the worktree
   path (`.claude/worktrees/<slug>/`) or by listing the
   worktree's `wiki/_state/efforts/` directory.

2. **Walk `main`'s registry.** `brain.py efforts list
   --json` from the primary checkout reads
   `wiki/_state/efforts/` on the current ref. If invoked
   from `main`, this is the merged-efforts audit. If
   invoked from a feature branch, it's whatever that
   branch sees.

3. **Join with PR state.** For each effort record, run
   `gh pr list --search "<slug>"` against the brain repo
   and against each repo named in the record's `targets`.
   Match PRs whose head ref is the recorded branch name.
   Capture: PR number, state (open/draft/merged/closed),
   mergedAt, last updated.

4. **Compute the phase.** Derive a one-word phase per
   effort:
   - `phase: spawned` — registry record exists, no PR yet.
   - `phase: drafting` — brain PR exists, status `draft`.
   - `phase: review` — brain PR exists, status `open` (not draft).
   - `phase: merged` — brain PR `mergedAt` non-null.
   - `phase: building` — brain PR merged, sibling-repo PR open.
   - `phase: shipped` — all PRs merged.
   - `phase: orphaned` — worktree exists, no record, no PR.

5. **Filter** if `$ARGUMENTS` carries a status filter
   (`in-flight`, `merged`, `abandoned`, `orphaned`).

6. **Surface a table.** One line per effort. Columns:
   slug · phase · brain-branch · brain-PR · target-PRs ·
   owner · helpers · spawn-age · status. Multi-target PRs go
   on continuation lines indented under the slug.

   The `owner` column reads from the registry record's
   `owner_state` plus `owner_agent_id` fields (per
   [`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md)
   § Decision > *Registry-record extension shape*) — render as
   `<state>:<id[0:8]>` when an owner is dispatched, the literal
   `none-dispatched` when the operator passed `--no-owner` to
   `/spawn`, and `-` when neither field is set (pre-spawn or
   legacy record). The four valid `owner_state` values are
   `active`, `completed`, `blocked`, `none-dispatched`. The
   `helpers` column reads `helpers_dispatched` (an integer
   count of helper subagents the owner has fanned out across
   the effort's lifetime); render as the integer when ≥ 1,
   `-` when absent or zero. End with a one-line tally
   ("3 in-flight, 1 orphaned, 7 merged in last 14 days").

## Output convention

```
slug                                  phase      brain-branch                                  brain-PR    targets                          owner                helpers  spawn-age  status
parallel-efforts-on-request           merged     agent/parallel-efforts-on-request-build-…     #264        -                                completed:7f4a2c89   2        15m        merged
search-revamp                         drafting   agent/search-revamp-…                         #271        app: #4680 (review)              active:b1d903e5      4        2h         in-flight
ai-act-record-keeping                 spawned    agent/ai-act-record-keeping-…                 -           app                              active:f9e10ab2      -        30m        in-flight
quick-experiment                      spawned    agent/quick-experiment-…                      -           -                                none-dispatched      -        5m         in-flight
agent-a14c6d45a3d0be241               -          agent/app-graphql-…                           -           -                                -                    -        7d         orphaned

3 in-flight · 1 orphaned · 1 merged in last 14d · 1 owner-opted-out
```

## What this skill does NOT do

- **Does not mutate registry records.** Read-only. Use
  `brain.py efforts mark <slug> <status>` directly, or
  `/sync` for the automated reconciliation pass.
- **Does not create or delete worktrees.** Use `/spawn` to
  create; use `/sync` to reap.
- **Does not pull or fetch.** The PR-state join uses
  `gh pr list` which queries the GitHub API directly; if
  the user wants fresh local refs, they run `/rebase` or
  `/sync` separately.
- **Does not span sibling-repo registries.** v1 reads only
  the brain's `wiki/_state/efforts/`. Sibling repos do not
  carry their own effort registries — the brain is the
  single source of truth.
