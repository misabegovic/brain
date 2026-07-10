---
title: "Parallel-first execution: every /spawn dispatches a background owner subagent (opt-out via --no-owner), helper fan-out is named in the skills, and the rule recurses to the parent session"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
  - .claude/skills/spawn/SKILL.md
  - .claude/skills/list-efforts/SKILL.md
---

# Parallel-first execution: every `/spawn` dispatches a background owner subagent (opt-out via `--no-owner`), helper fan-out is named in the skills, and the rule recurses to the parent session

## Context

The workspace-layer decision at
[`parallel-efforts-on-request`](./parallel-efforts-on-request.md) delivered
per-effort worktrees, a per-effort registry under `wiki/_state/efforts/`, the
`/list-efforts` join surface, and cheap-rebase tooling. What it deferred is
*who runs the work inside each spawned worktree*. The implicit assumption
that the parent session would operate inside the new worktrees one at a time
collapsed observed parallelism back into serial coordination — the operator
surfaced exactly that failure the morning after the workspace layer shipped.

The operator's direction reframed the question the original sketch posed
(mandatory vs. advisory vs. size-conditional dispatch): parallel is the
default route; everything is parallel first. With that binary closed, this
decision is no longer pattern selection but protocol-shape commitment. Five
sub-decisions remained, and this ADR commits a position on each.

**Owner-subagent prompt template location.** The prompt template lives at
[`tools/templates/owner-subagent-prompt.md`](../../../tools/templates/owner-subagent-prompt.md),
alongside the existing artefact templates — one canonical templates
directory. The prompt covers the working directory (the spawned worktree),
authority gating (the `/shape` phase gates still apply), deepdive-first
discipline per [`shape-deepdive-pre-flight`](./shape-deepdive-pre-flight.md),
end-to-end ownership (the owner runs the effort to a merged PR or a
documented blocker, never to a partial state), and the reporting protocol
(surface to the parent at phase boundaries, on blockers, and on completion).

**Opt-out flag spelling.** The opt-out flag on `/spawn` is `--no-owner`, a
boolean suppressor of the dispatch step. It names the thing turned off
(matching git's `--no-verify` precedent) and so reads self-documenting at
the call site. Its effect is recorded in the registry record so
`/list-efforts` can distinguish an explicit opt-out from an owner that is no
longer active.

**Registry-record extension.** The per-effort record gains four optional
flat fields: the owner subagent's identifier, the dispatch timestamp, an
owner-state value (one of `active`, `completed`, `blocked`,
`none-dispatched`), and a count of helpers fanned out over the effort's
lifetime. The efforts subcommands accept matching flags, and the efforts
listing gains an owner column.

**Helper fan-out named in skill bodies.** A single shared phrasing — when a
step has parallel shape (multiple files to read, multiple subtasks to
evaluate, multiple targets to inspect), default to fanning out helper
subagents in a single message rather than serial tool calls — is added at
the natural fan-out point in five skills: the `/shape` Phase 1 deepdive,
`/pr`'s CI watch, `/continue`'s state ingestion on resume, `/sync`'s sweep
across sibling repos, and the intake path's multi-source ingest. Each
insertion cross-links this ADR. The phrasing is descriptive on what makes a
step parallel-shaped and prescriptive on the default tilt; series remains
the exception, taken when later calls genuinely depend on earlier results.

**Recursion to the parent session.** The rule recurses beyond `/spawn`:
parent-session tool-call discipline is parallel-first by default — multiple
independent shell or read calls in one message, multiple independent agent
dispatches in one message. The rule lands as a top-level governance section
in [`AGENTS.md`](../../../AGENTS.md) titled *Agent teams — fan-out and
parallelism*, naming the three-level model: the parent coordinates and is
itself parallel-first; owners run efforts end-to-end in the background and
fan out by default; helpers parallelise subtasks within an effort.

This ADR **partially supersedes** the parent ADR's closing clause that
explicit opt-in is the only entry path to parallelism — at the *execution*
layer only. Workspace parallelism stays operator-initiated via `/spawn`;
once a spawn happens, owner dispatch is the default route, opted out via
the flag rather than re-confirmed each time.

## Alternatives

Alternatives are grouped by sub-decision; the operator's parallel-first
direction had already closed the pattern-selection options.

- **Template location** — chosen: the shared templates directory. Rejected:
  inlining the prompt in the spawn skill body (couples prompt evolution to
  the skill's protocol surface); a second templates directory (splits one
  canonical shelf into two with no load-bearing distinction).
- **Flag spelling** — chosen: `--no-owner`. Rejected: `--solo` (requires
  knowing what with-owner means to read it), `--inline` (name collision
  with other inline/block senses), `--manual-owner` (ambiguous),
  `--skip-dispatch` (surfaces the mechanism, not the user-visible
  distinction).
- **Registry shape** — chosen: four optional flat fields. Rejected: a
  nested owner object (breaks the existing flat-record precedent); deriving
  owner state from PR state (misclassifies pre-PR deepdive work as no owner
  active); a heartbeat field (requires the owner to keep its own
  bookkeeping, which drifts when an owner crashes mid-run).
- **Fan-out wording** — chosen: one shared phrasing across five skills,
  cross-linked here. Rejected: per-skill bespoke wording (dilutes one rule
  into five and invites drift); governance-file-only (invisible at the
  point of use); a single mention in `/shape` only (misses four equally
  natural surfaces).
- **Recursion** — chosen: yes, via a new top-level governance section.
  Rejected: burying it in the sibling-repo subsection (hides it from
  brain-side readers); a per-skill protocol step in every skill (wrong
  layer); confining the rule to dispatched contexts (the direction reads
  brain-wide).
- **Do nothing** — leave the protocol shape implicit and hope in-session
  habit catches it. Rejected: the failure mode had already surfaced the
  morning after the workspace layer shipped.

## Consequences

**Closes.** The owner prompt is a template edit, never a skill edit.
`--no-owner` is the canonical opt-out; the owner-state values stay at the
four documented ones unless a successor ADR supersedes this one; the
registry record — not a heartbeat or PR state — is the source of truth on
owner state; helper fan-out is named in the skills rather than left to
habit; the parent session is not exempt from parallel-first.

**Opens.** Multi-effort cycles execute in parallel at the agent layer, not
just the workspace layer. The operator reads `/list-efforts` and sees owner
state at a glance. Fan-out at the natural points surfaces in tool-use
traces and behaves the same across fresh sessions because the rule lives in
skill files, not in-session memory.

**Costs.** One new template file, edits to six skills (the dispatch step in
`/spawn` plus the shared phrasing in five others), a mechanical extension
of the efforts subcommands, an extra column in the efforts listing, and a
new governance section. Registry records grow by up to four optional
fields per effort.

## Build notes

The build landed the five sub-decisions as committed. The dispatch step
became a numbered step in the spawn skill's protocol with the opt-out
documented in its own subsection; the owner prompt template shipped at the
committed path; the four registry fields and their flags landed flat; the
efforts listing renders the owner state (with a short-form agent id when
active); the shared fan-out phrasing landed in all five skills; and the
governance section landed between the core-operations and conventions
sections. The only divergence was cosmetic: the listing's owner value slots
into the existing tab-separated row format rather than a fixed-width
column.
