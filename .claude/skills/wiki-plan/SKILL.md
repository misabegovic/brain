---
name: wiki-plan
description: Plan a task against the brain — given a task description, walk index.md and the auto-generated views, identify the smallest set of brain pages an agent (or human) should load to act, surface coverage gaps and in-flight overlapping work, and emit an ordered plan. Load when the user says "plan", "what do I need to read for X", "outline the work for X", or otherwise asks for a brain-grounded plan before doing real work.
---

# Plan a task against the brain

You are working in `~/projects/brain`. Goal #3 of the brain (per
`AGENTS.md`) is to be the primary working memory for autonomous agents.
This skill is the operation that makes that real: take a task and
produce a plan that lists *exactly which brain pages to load*, *what's
missing*, and *what other work is already in flight nearby*.

The output is **a plan, not an implementation.** This skill never
writes wiki content; it tells you (or another skill / another agent)
what to do next.

## When to run

- Before starting a non-trivial task — instead of opening the IDE blind.
- The autonomous-agent persona runs this *as the first step* of
  every task.
- The user says "I want to do X — plan it for me."
- Before kicking off `/ingest` or `/feedback` if you're not sure where
  the material belongs.

## Inputs

- `/plan <task description>` — the task in plain English.
- `/plan` (no arg) — ask the user what the task is before proceeding.

## Protocol

### 1. Frame the task

Read the user's request. Extract:

- **Domain.** Which area of the organisation does this touch?
  (Main app, infra, frontend, agent tooling, etc.)
- **Kind of work.** Reference / initiative / decision / overlap /
  feedback / mining / lint? This is meta-classification.
- **Repos likely affected.** From `wiki/_views/by-repo.md`.
- **Teams likely affected.** From `wiki/_views/by-team.md`.

If the task isn't clearly classifiable from one sentence, ask one
clarifying question and stop. Don't guess.

### 2. Walk the brain

```bash
# Look at the corpus shape first.
cat wiki/index.md
cat wiki/_views/by-kind.md
cat wiki/_views/by-team.md
cat wiki/_views/by-repo.md
```

Then read candidate pages — the ones whose `kind` / `team` / `repos`
match the task's frame. Token budget matters: each page in
`wiki/_views/pages.json` carries an approximate `tokens` field. Sum
your candidate set; if it exceeds your budget, drop the lowest-confidence
or oldest pages first.

### 3. Run mempalace search

```bash
mempalace search "<key phrase from the task>"
```

Across 1–3 distinct phrasings. Hits in `wiki/` confirm the candidate
set; hits in sibling repos suggest source material the wiki may not yet
cover (a coverage gap).

### 4. Run /overlap on the topic

Either invoke `wiki-overlap` directly or do the equivalent: search for
*active initiatives* (`kind: initiative`, `status: living | draft`)
that share teams, repos, or key phrases with the task.

If overlap is found, the plan must call it out — proceeding without
acknowledging in-flight work is the duplication failure mode the brain
exists to prevent.

### 5. Detect coverage gaps

For each repo the task likely touches:

```bash
python tools/brain.py coverage <repo>
```

Note the uncovered top-level dirs. If any of them are central to the
task, the plan's first action becomes "ingest <dir>" — *before* trying
to act.

### 6. Emit the plan

Output (to the user, or to the next skill/agent) a structured plan:

```markdown
## Plan: <one-line task title>

### Frame
- Domain: <area>
- Kind: <reference | initiative | decision | feedback | …>
- Repos: <repo1, repo2>
- Teams: <team1, team2>

### Pages to load (in order)
1. `wiki/<page1>` — <why> (~<tokens> tokens, confidence: <c>)
2. `wiki/<page2>` — …
3. `wiki/_overlaps/<overlap>` — *if any*

Total approx: <N> tokens.

### Coverage gaps (read these from source if needed)
- `~/projects/<repo>/<dir>` — uncovered; cite directly when relevant.
- *(none)* if coverage is complete.

### In-flight overlap to acknowledge
- `wiki/<initiative>` — <team> is already doing <X>; coordinate before
  acting.
- *(none)* if no overlap detected.

### Suggested next operation
- `/ingest <source>` to fill gap A, then plan again, OR
- proceed directly with the work, citing the listed pages, OR
- escalate to the human because <ambiguity>.
```

If any of the four sections is empty, say *"(none)"* explicitly. Empty
sections are still signal.

### 7. Don't write to the wiki

This skill produces a plan. It does not edit `wiki/`, `log/`, or
`sources/`. The plan is consumed by the next operation — that operation
may write.

If the plan reveals that the brain itself needs a fix (a missing
coverage page, a contradictory pair of decisions), surface that in the
output but still don't fix it from inside `/plan`. The fix is its own
next step.

## Token-budget heuristics

- Default agent budget: keep the candidate page set under 30k tokens.
- For tasks the agent runs autonomously: aim for 10k tokens of brain
  context, leaving the rest for code/sources.
- A reference page with `confidence: low` is worth half its tokens —
  if the budget is tight, drop it before a `confidence: high` page.

## Done check

- [ ] The plan names the smallest set of pages, not all candidates.
- [ ] Coverage gaps are explicit (or "(none)").
- [ ] In-flight overlaps are explicit (or "(none)").
- [ ] The plan ends with one suggested next operation, not three.
- [ ] No edits were made to `wiki/`, `log/`, or `sources/`.
