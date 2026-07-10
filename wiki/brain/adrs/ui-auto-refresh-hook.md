---
title: "UI auto-refresh — editor hook plus CI smoke build"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
  - ../../../tools/ui-build.sh
  - ../../../.claude/skills/sync/SKILL.md
---

Records where the UI rebuild trigger lives: two sites sharing one
wrapper script, `tools/ui-build.sh`.

## Context

The UI at `ui/` renders the wiki, but a build that only runs when
someone remembers to run it drifts from the content — the operator
ends up navigating raw markdown because the rendered surface is
unreliable, and broken markdown that the Python validator accepts
can still choke the site build. The question the decision answers
is where the automatic trigger lives.

The answer is two sites, not one and not three:

- **An agent-harness hook.** A PostToolUse hook fires after any
  Edit or Write whose path falls under `wiki/`, running
  `tools/ui-build.sh`. The wrapper builds into a gitignored sandbox
  directory (`ui/.build-cache/`) so it never collides with
  committed build artefacts or with parallel sessions working on
  the UI itself.
- **A CI smoke step.** The validation workflow runs the same
  wrapper on every change set, after the existing Python gates. A
  build failure fails the check.

The `/sync` skill is deliberately not modified. Three forces drove
the shape. The appetite was small: two trigger surfaces — the
fast-feedback one for agent sessions and the gate at the merge
boundary — cover essentially all wiki writes today, and a third
adds a failure mode without covering a distinct edit path. The
collision concern was load-bearing: the hook must never write to
the committed UI output or the UI configuration, which the sandbox
output directory enforces by construction. And silent failure is
worse than no hook: the wrapper runs strictly (exit on first
error), stays silent on success, and exits non-zero with stderr on
failure, so the harness bubbles the error into the agent transcript
and CI fails the check visibly.

Non-wiki edits short-circuit cheaply inside the hook's path test.
Edits to the generated views folder do trigger a rebuild, but the
regeneration loop settles after one extra pass because rebuilding
the same wiki state is idempotent. Observability stays at the
merge boundary — one audit-log line per merge, not one per hook
fire, which would flood the log for no diagnostic gain: if a merge
lands markdown the SSG cannot build, CI already failed before the
merge.

Because both sites share one wrapper, a passing CI run proves the
local hook will also succeed on the merged state; the invocation
cannot drift between surfaces. Flag changes belong upstream in the
SSG invocation, not accumulated in the wrapper.

## Alternatives

- **Hook plus CI step** *(chosen)* — two surfaces, one wrapper,
  no state, no daemon, no port. Fast feedback in-session, a hard
  gate at the merge boundary.
- **Hook only** — cheaper, but misses the case where a change
  set's markdown breaks the build on the merged state; the CI
  failure surface is also the most legible signal for humans
  debugging a hook they cannot see. Rejected.
- **`/sync` step plus CI** — `/sync` runs on neither the per-edit
  nor the per-merge cadence, so the agent session actually writing
  the wiki would get no feedback at all. Rejected, consistent with
  the no-re-architecture no-go on `/sync`.
- **All three sites** — the third trigger covers no edit path the
  other two miss; it would be three failure modes for two coverage
  gains. Rejected.
- **A file-watcher daemon** — long-running, stateful, owns a
  process, and collides with parallel agent sessions on the same
  machine. Rejected as a named rabbit hole.
- **Status quo (manual builds only)** — the problem being solved.
  Rejected.

## Consequences

- *Closes:* the "should the UI rebuild be automated?" question;
  the freshness-theater failure mode where the rendered UI silently
  lags the wiki; the divergence between wiki content and the last
  manual build, insofar as new merges keep up.
- *Opens:* a documented seam for the wrapper to grow if the build
  invocation evolves (incremental builds, per-route generation);
  a foothold for further hooks — once PostToolUse is wired,
  additional matchers are a small extension (the home-page
  staleness pair in [home-content-shape.md](home-content-shape.md)
  later rode exactly this scaffold).
- *Costs:* every agent session that edits the wiki pays the build
  cost (single-digit seconds); CI gains a Node toolchain step with
  npm caching keyed on the UI lockfile; four small file deltas
  (wrapper script, harness settings block, workflow block,
  gitignore line), all on restricted paths and flagged as such;
  the path filter lives inside the hook command rather than the
  matcher, migrating to matcher globs if the harness grows them.

## Build notes

The wrapper was originally written against the prior SSG's build
command; the substrate swap recorded in
[successor-ssg-for-ui.md](successor-ssg-for-ui.md) rewrote the
invocation to the Astro build while preserving the whole contract —
sandbox output directory, silence on success, non-zero exit with
stderr on failure. Two refinements landed in the shipped script:
it changes into the UI directory before building because the SSG
reads its configuration from the working directory, and it exits
zero early when the UI's dependencies are not installed
(fresh-clone or dependency-less environments), since a cheap
ergonomics hook should not surface missing scaffolding as a
failure.
