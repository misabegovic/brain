---
title: "Superpowers — agent workflow methodology (brainstorm → plan → TDD → verify)"
kind: reference
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
  - https://github.com/obra/superpowers
  - https://blog.fsck.com/2025/10/09/superpowers/
---

# Superpowers — the agent workflow

A complete, composable workflow for coding agents, published
upstream at [obra/superpowers](https://github.com/obra/superpowers)
(language-specific forks exist). This page synthesises the
*workflow* skills — the universal pieces that govern *how* a coding
agent should move from idea → spec → plan → implementation → review
→ ship. Stack-specific skills live in the upstream forks and are
consulted on demand by sibling repos that match — they're outside
this synthesis.

## The workflow at a glance

```
brainstorming      → spec
   ↓
writing-plans      → plan
   ↓
subagent-driven-development OR executing-plans
   ↓                     ↓
test-driven-development  test-driven-development
   ↓                     ↓
requesting-code-review   requesting-code-review
   ↓                     ↓
verification-before-completion
   ↓
finishing-a-development-branch → merge / PR / discard
```

Two principles run end-to-end:

- **Evidence over claims** — never declare success without fresh
  verification output. ("Should pass" / "Looks correct" = not
  enough.)
- **Process over guessing** — every phase has a *next step* baked
  in. Don't free-style.

## Phase 1 — Brainstorming (idea → spec)

**Hard gate:** no implementation, no scaffolding, no code, no other
skill — until a design has been presented and the user has approved
it. *Every* project goes through this, regardless of perceived
simplicity. "Simple" projects are where unexamined assumptions
cause the most wasted work.

The shape:

1. **Explore project context** — files, docs, recent commits.
2. **Decompose if needed** — if the request describes multiple
   independent subsystems, flag it; don't refine details of a
   project that should be split. Each sub-project gets its own
   spec → plan → implementation cycle.
3. **Ask one question at a time** — multiple choice when possible.
   Focus on purpose, constraints, success criteria.
4. **Propose 2-3 approaches** with trade-offs and your
   recommendation up front.
5. **Present the design in sections** scaled to complexity. After
   each section: "does this look right so far?"
6. **Spec self-review** — placeholder scan, internal consistency,
   scope check, ambiguity check. Fix inline; don't re-review.
7. **User reviews the written spec** before plan-writing starts.

**Design for isolation and clarity.** Smaller, well-bounded units
each with one purpose, communicating through well-defined
interfaces. The test: can someone understand what a unit does
without reading its internals? Can you change the internals without
breaking consumers? If not, the boundaries need work.

The terminal state is **invoking writing-plans**. No other skill.

## Phase 2 — Writing plans (spec → plan)

A plan is comprehensive enough that an enthusiastic-but-junior
engineer with poor taste, no project context, and an aversion to
testing could follow it. **DRY. YAGNI. TDD. Frequent commits.**

Every plan starts with a header: goal, architecture (2-3
sentences), tech stack. Then a **file structure** map — which files
get created or modified, what each one is responsible for. *This is
where decomposition decisions get locked in.*

**Bite-sized tasks** (2-5 minutes each):
- Step 1: write the failing test
- Step 2: run it to confirm failure
- Step 3: implement minimal code
- Step 4: run tests to confirm pass
- Step 5: commit

**No placeholders.** "TBD", "TODO", "implement later", "add
appropriate error handling", "write tests for the above" — these
are *plan failures*, not allowed steps. Every step has actual
content the engineer needs.

**Self-review checklist:**
1. Spec coverage — point each spec section to a task.
2. Placeholder scan — kill every red flag.
3. Type consistency — function names and signatures match across
   tasks (`clearLayers()` in Task 3 must not be `clearFullLayers()`
   in Task 7).

Save plans to a dated plans folder in the working repo (e.g.
`docs/plans/YYYY-MM-DD-<feature>.md`).

## Phase 3 — Test-driven development (plan → code)

**The Iron Law:**

> NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

Wrote code before the test? **Delete it. Start over.** Don't keep
it as reference; don't adapt it while writing tests; delete means
delete.

The cycle: **RED → verify-RED → GREEN → verify-GREEN → REFACTOR**.

- **RED** — one minimal test for one behaviour, with a clear name.
- **Verify RED** is mandatory. The test must *fail*, and fail for
  the *right reason* (feature missing, not typo). Test passes
  immediately = you're testing existing behaviour, fix the test.
- **GREEN** — simplest code to pass the test. No "while I'm here"
  improvements; no extra options for hypothetical needs.
- **Verify GREEN** is mandatory. Other tests still pass. Output
  pristine — no errors, no warnings.
- **REFACTOR** — only after green. Remove duplication, improve
  names. Don't add behaviour. Stay green.

**Why order matters.** Tests-after answer "what does this do?";
tests-first answer "what *should* this do?". Tests-after are biased
by your implementation: you verify what you remembered, not what's
required. Tests-first force edge-case discovery *before*
implementation.

**No exceptions** for "throwaway" prototypes, "I'll write tests
after," "I already manually tested it", "deleting work is wasteful"
(sunk-cost fallacy), "TDD is dogmatic". *Violating the letter of
the rules is violating the spirit of the rules.*

## Phase 4 — Verification before completion

**The Iron Law:**

> NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.

If you haven't run the verification command in *this* message, you
cannot claim it passes.

The gate function before any success claim:

1. **Identify** — what command proves this claim?
2. **Run** — execute the full command (fresh, complete).
3. **Read** — full output, exit code, count of failures.
4. **Verify** — does output confirm the claim? If no: state actual
   status with evidence. If yes: state claim *with* evidence.
5. **Only then** — make the claim.

| Claim                 | Requires                        | Not sufficient                   |
|-----------------------|---------------------------------|-----------------------------------|
| Tests pass            | Test command output: 0 failures | Previous run, "should pass"      |
| Linter clean          | Linter output: 0 errors         | Partial check, extrapolation     |
| Build succeeds        | Build command: exit 0           | Linter passing, "logs look good" |
| Bug fixed             | Test original symptom: passes   | Code changed, assumed fixed      |
| Regression test works | Red-green cycle verified        | Test passes once                 |
| Agent completed       | VCS diff shows changes          | Agent reports "success"          |
| Requirements met      | Line-by-line checklist          | Tests passing                    |

Red flags: "should", "probably", "seems to"; expressing
satisfaction before verification ("Great!", "Done!"); about to
commit/push/PR without running the command.

## Phase 5 — Subagent-driven development (the execution loop)

For multi-task plans where tasks are mostly independent, dispatch a
**fresh subagent per task** with two-stage review after each.

**Why fresh subagents:** isolated context, focused instructions,
zero pollution from your session history. The controller (you) also
keeps context for coordination work.

**Per task:**

1. Dispatch implementer subagent (full task text + scene-setting
   context — never have them read the plan file).
2. Implementer asks questions? Answer before they proceed.
3. Implementer implements + tests + commits + self-reviews.
4. Dispatch **spec reviewer subagent** (compliance: does the code
   match the spec? Nothing missing, nothing extra).
5. Spec issues? Implementer fixes; re-review.
6. Dispatch **code quality reviewer subagent** (Critical →
   Important → Minor; fix Critical and Important before
   proceeding).
7. Quality issues? Implementer fixes; re-review.
8. Mark task complete in the todo list.

After all tasks: dispatch a **final code reviewer subagent** for
the entire implementation, then proceed to
finishing-a-development-branch.

**Implementer status handling.** Subagents report `DONE`,
`DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`. Never ignore
an escalation; never force the same model to retry without changing
something. If the implementer is stuck, *something needs to
change* — context, model, or task scope.

**Model selection.** Use the least powerful model that can handle
each role. Mechanical tasks (1-2 files, complete spec) → cheap.
Multi-file integration → standard. Architecture, design, review →
most capable.

**Alternative:** `executing-plans` (same-session, batch execution
with human checkpoints) when subagent dispatch isn't available or
tasks are tightly coupled.

## Phase 6 — Requesting code review

Mandatory after each subagent task, after major features, before
merge to main. Optional but valuable when stuck or before a big
refactor.

Mechanics:

1. Get the SHAs (`BASE_SHA=$(git rev-parse HEAD~1)`,
   `HEAD_SHA=$(git rev-parse HEAD)`).
2. Dispatch the code-reviewer agent with: what was implemented,
   what it should do (plan or requirements), the SHA range, and a
   one-line description.
3. Act on feedback by severity:
   - **Critical** — fix immediately.
   - **Important** — fix before proceeding.
   - **Minor** — note for later.
   - **Reviewer wrong?** Push back with reasoning + tests that
     prove it works.

## Phase 7 — Finishing a development branch

When implementation is done and tests pass, present **exactly four
options**:

1. Merge back to `<base>` locally
2. Push and create a Pull Request
3. Keep the branch as-is
4. Discard this work *(typed "discard" required for confirmation)*

**Don't elaborate** the options — keep them concise. Verify tests
pass *before* presenting. Clean up the worktree only for options 1
and 4.

## Cross-cutting — systematic debugging

The Iron Law:

> NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST.

Four phases, each gating the next:

1. **Root-cause investigation** — read errors carefully; reproduce
   consistently; check recent changes; gather evidence at each
   component boundary; trace data flow backward.
2. **Pattern analysis** — find working examples; compare against
   reference implementations *completely* (don't skim); list every
   difference; understand dependencies.
3. **Hypothesis and testing** — *one* hypothesis at a time;
   smallest-possible-change to test it. Hypothesis fails? Form a
   new one — don't stack fixes.
4. **Implementation** — failing test first; single fix; verify.

**If 3+ fixes have failed, STOP and question the architecture.**
That's not a hypothesis problem; it's a *wrong abstraction* signal.
Discuss with the operator before fix #4.

## Cross-cutting — writing skills

When authoring a skill (or editing one), TDD applies to *the
documentation itself*:

| TDD concept         | Skill creation                                     |
|---------------------|-----------------------------------------------------|
| Test case           | Pressure scenario with subagent                    |
| Production code     | The SKILL.md document                              |
| Test fails (RED)    | Agent violates rule *without* the skill (baseline) |
| Test passes (GREEN) | Agent complies *with* the skill present            |
| Refactor            | Close loopholes while maintaining compliance       |

**Iron Law:** no skill without a failing test first — applies to
new skills *and* edits.

CSO (Claude Search Optimisation):

- Description starts with `Use when...` and lists triggering
  conditions only — *never* summarise the workflow. (A description
  saying "code review between tasks" caused the agent to do *one*
  review even though the skill flowchart showed two.)
- Keyword coverage in the body — error messages, symptoms,
  synonyms, tools.
- Verb-first names (`creating-skills`, not `skill-creation`).
- Token budget: getting-started workflows under 150 words,
  frequently-loaded skills under 200, others under 500.

Bulletproof discipline skills against rationalisation: state the
rule, then forbid specific workarounds; add a "spirit-vs-letter"
clause; build a rationalisation table; expose a "Red Flags — STOP
and start over" list.

## How this propagates into the brain's `/shape` flow

| `/shape` phase             | Maps to superpowers                                      |
|----------------------------|-----------------------------------------------------------|
| Phase 1 — PM agent → PRD   | brainstorming + writing-plans (the PRD = spec)           |
| Phase 1.5 — RFC pass       | brainstorming's "review the spec" gate                   |
| Phase 2 — Tech Lead → ADR  | writing-plans' file-structure + alternatives             |
| Phase 3 — Developer → code | TDD + verification + subagent-driven-development         |
| Post-implementation review | requesting-code-review + finishing-a-development-branch  |

The `/shape` skill at
[`.claude/skills/shape/SKILL.md`](../../../.claude/skills/shape/SKILL.md)
is the brain's authoring path. The methodology *here* is the
underlying discipline.
