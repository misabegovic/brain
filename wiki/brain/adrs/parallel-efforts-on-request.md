---
title: "Opt-in parallel efforts via a /spawn skill that creates per-effort worktrees and a wiki/_state/efforts/ registry, with existing skills becoming worktree-aware"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
summary: >
  Parallel work is opt-in via /spawn: per-effort worktrees and branches plus a registry record; the default workflow stays single-effort, single-checkout.
sources:
  - ../../../AGENTS.md
  - .claude/skills/spawn/SKILL.md
  - .claude/skills/rebase/SKILL.md
---

# Opt-in parallel efforts via a `/spawn` skill that creates per-effort worktrees and a `wiki/_state/efforts/` registry, with existing skills becoming worktree-aware

## Context

The brain serialised work: every in-flight effort shared one checkout, one
branch context, and an in-conversation memory of which effort was active.
The underlying mechanism — git worktrees plus per-effort branches — was
already in ad-hoc use, but no skill created them, no registry tracked them,
no sibling-repo story existed, and no slug-collision check spanned open
PRs. The load-bearing question: surface opt-in parallelism as a new
top-level skill, as flags on the existing skills, or both — and what
registry shape rounds that out?

The forces. The brain has a clean one-verb-one-skill surface; new verbs
earn their own skill rather than colonising existing ones. The
`wiki/_state/` shelf already holds tooling-managed operational state, but
its existing single-file shape would re-create the merge-conflict problem
already seen on generated views and the home index — two parallel efforts
updating one shared file conflict on every cross-write. Several sibling
repos are in active scope, some human-edited daily, so a parallel-efforts
story must bypass the operator's primary checkout; the cleanest shape is
each sibling repo gaining its own worktrees directory mirroring the
brain's convention. Finally, phase serialisation in `/shape` is *within*
an effort; parallelism *across* efforts coexists with it — conflating the
two is what held parallelism back.

The decision. A new top-level **`/spawn`** skill creates a brain worktree
on a fresh branch off main for a named effort, optionally creates parallel
worktrees in named target sibling repos, and writes one per-effort registry
record at `wiki/_state/efforts/<slug>.json` recording the slug, branch,
target repos, sibling branches and worktree paths, spawn timestamp, and
lifecycle status. No existing skill gains a `--parallel` flag.

Existing skills become **worktree-aware** by reading their working tree on
entry — the worktree path *is* the effort context. Invoked from a spawned
worktree, they read that effort's registry record; invoked from the primary
checkout, they behave exactly as before. A companion **`/list-efforts`**
skill walks the registry, joins each record against the open-PR list for
the brain and any recorded sibling repos, and surfaces the effort table —
slug, phase, PRs, branches, worktree paths, spawn age, status. A
**`/rebase`** skill performs the cheap rebase: fetch, rebase the active
branch on origin main, resolve generated-views conflicts by re-running the
deterministic regenerator (its output *is* the correct resolution), keep
both sides' entries on home-index conflicts (additive), then force-push
with lease and verify the commit landed, with one observable checkpoint
before the push.

Sibling-repo worktree directories are created **lazily** on first spawn
against that repo, after checking the repo is in active scope, its primary
checkout is in a clean canonical state, and no path collision exists; any
failed check stops the spawn. Eager pre-creation across all sibling repos
is forbidden per the emergent-structure convention.

Each registry record is its **own JSON file**, never co-mingled in a single
index file — two parallel efforts cannot conflict at merge time because
they touch distinct paths. This is the load-bearing structural choice that
makes the registry compatible with parallel merging. The record is created
on spawn, read and updated by the worktree-aware skills as the effort
progresses (PR opened, merged, abandoned), and kept as an audit artefact;
`/sync` reaps records older than ninety days into the archive. `/shape`'s
slug-uniqueness pre-flight extends to query open PRs, so concurrent shape
invocations cannot land the same slug. Cleaning up pre-existing ad-hoc
worktrees is out of scope; `/list-efforts` surfaces them as orphaned and a
follow-up sweep reaps them.

## Alternatives

- **A — `/spawn` skill (chosen).** One new top-level skill, one registry
  shape, existing skills unchanged except for worktree awareness.
  Discoverable and consistent with the one-verb-one-skill surface. The
  cost is a separate spawn step before the work begins, but the separation
  is clean: spawn is a workspace operation; the other skills are content
  operations.
- **B — `--parallel` flags on every existing skill.** One-step from the
  user's view, but the worktree logic becomes a hidden shared helper, the
  flag cannot carry effort metadata that belongs to no single skill,
  discoverability suffers, and it conflates the spawn verb with every
  other verb. Rejected.
- **C — `/spawn` plus `--parallel` shortcuts on the workhorse skills.**
  Creates a second path through the same logic; two ways to do the same
  thing is exactly the surface drift the single-authoring-path discipline
  exists to prevent. Rejected.
- **D — one committed registry file.** Matches the existing state-shelf
  shape but two parallel efforts collide on every cross-write. Per-effort
  files cost a directory listing on read and win on parallel writes.
  Rejected.
- **E — uncommitted per-checkout registry.** Avoids history churn, but
  uncommitted state is not readable across worktrees without per-machine
  plumbing, and the brain's strength is that the wiki itself is the
  agent's working memory. Rejected.
- **F — no registry; derive from the worktree list plus open PRs.**
  Simplest, but the registry holds metadata those surfaces lack (owning
  slug, target repos, spawn time, cross-repo linkage); without it every
  skill re-derives context from branch-name parsing. Rejected.
- **Do nothing.** Ad-hoc worktrees and stash-and-switch serialisation
  persist. Rejected.

## Consequences

**Closes.** No `--parallel` flag on any existing skill, present or future.
Generated-views regeneration stays a pre-merge concern — parallel PRs still
conflict on view files and `/rebase` is the answer, not a post-merge CI
job. The home-pairing gate on wiki PRs is not relaxed. `/shape`'s
within-effort phase serialisation is unchanged. The brain does not
auto-detect that work should be parallel — explicit opt-in via `/spawn` is
the only entry path. (The execution-layer half of that last clause was
later partially superseded by
[`parallel-execution-agent-teams`](./parallel-execution-agent-teams.md):
the operator still chooses *whether* to spawn, but a spawn now dispatches
an owner subagent by default.)

**Opens.** Multiple shape efforts run simultaneously, each in its own
worktree; multiple builds against the same sibling repo run simultaneously,
each in its own sibling worktree. The slug check spans open PRs.
`/list-efforts` becomes the first first-class answer to "what is this
brain doing right now?", and the cheap rebase removes the per-PR friction
that was the practical bottleneck for parallel throughput.

**Costs.** Six existing skills gain a small worktree-aware pre-flight. The
brain gains three skills and the matching efforts and rebase subcommands.
The state shelf accumulates effort records, capped by the ninety-day reap.
Branch-list noise grows with parallelism — which is the point. Sibling
repos gain a worktrees directory on first spawn, with a matching ignore
entry written at bootstrap so worktree contents never land in the sibling
repo's history. The spawn skill respects the restricted-paths convention
and does not edit tooling or skill surfaces from a spawned worktree's
routine work.
