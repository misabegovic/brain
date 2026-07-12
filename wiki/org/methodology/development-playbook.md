---
title: "Development playbook — code quality, testing, AI usage, PR reviews"
kind: reference
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
---

# Development playbook — engineering standards

The four-pillar standard for engineering work across the
organisation: **code quality**, **testing**, **AI usage**, and
**PR reviews**.

## Why this page exists

The playbook isn't an aesthetic preference — it's the org's stated
position on what *gets shipped*. Quality, test coverage, review
rigour, and disciplined AI usage are framed as direct business
value: they reduce outages, avoid rollbacks, and translate into
agent-iteration speed. Before authoring an ADR or PRD that touches
production code in any active repo, the playbook is required
reading — `/shape`'s phase 2 (Tech Lead) and phase 3 (Developer)
explicitly cite it.

## 1 — Code quality

**Standard:** solid, readable, high-quality code. The cost of
interpretation, maintenance, upgrades, and extension drops sharply
when code is well-named, well-bounded, and well-tested.

**Stable abstractions over one-offs.** Reuse existing components,
modules, classes, and utility functions. If what you're building
doesn't fit, *expand the abstraction* rather than special-case
around it. Maintain the integrity of the abstraction so it makes
sense in a wider context. Copy-paste sometimes works, but every
duplication is a future-inconsistency hazard.

**Domain language matters.** Reusable abstractions written with
natural domain language amplify everyone's velocity.

**Curating abstractions is collective work** — we are responsible
for evolving them, not preserving them.

## 2 — Testing

**Why testing.** Code quality + test coverage stand between us and
outages, data loss, breaches. Tests double as documentation of
intent. AI agents iterate against test results, so a fast and
comprehensive suite is now also an *agent productivity multiplier*.

### Three test abstractions

| Layer           | Tests                                              | Cost                       | What to assert                                                                       |
|-----------------|----------------------------------------------------|----------------------------|---------------------------------------------------------------------------------------|
| **Unit**        | Individual objects + their logic                   | cheapest                   | *What* the code does (return values, behaviour) — not *how* (internal method calls)  |
| **Integration** | Controller actions, UI components — orchestration  | medium                     | The boundaries interact correctly                                                     |
| **System**      | Full stack through the UI                          | most expensive, most flaky | Frontend + backend contract compatibility (only place that catches it)                |

**Distribution:** many unit, fewer integration, even fewer system.
This follows naturally from the cost gradient.

**Workflow is flexible.** Top-down (failing system test as
acceptance) or bottom-up — either works. *What matters is that
every layer has appropriate coverage when the work is done.*

**Test data:** prefer in-memory objects over persisted records when
behaviour doesn't need the database. Shared fixtures for common
records; factories remain the right call for edge cases.

**Couple to the public interface, not internals.** A test that
asserts the return value survives refactoring; one that asserts
which internal methods were called in which order breaks every
refactor — even when behaviour is still correct.

**If you're testing more than orchestration at the integration
level**, that's a signal the logic belongs in the model layer where
it can be tested more easily and cheaply.

### Regression and flakiness

- **Bug found** = hole in test coverage. Identify *which*
  abstraction failed its responsibility, plug that hole as part of
  the fix.
- **Flaky tests** are net-negative. CI randomly fails, passes on
  retry → submit a PR that skips the test and notify the author
  immediately. Tests that aren't 100% deterministic cause more harm
  than good.

## 3 — AI usage

AI is essential in a programmer's arsenal and unlocks work that was
prohibitively expensive before — but **we are ultimately responsible
for any code we ship.**

**Three rules:**

1. **Understand it.** AI-generated code is reviewed by *you* before
   you request a human review. Don't ship code you can't explain.
2. **Self-review first.** Reach out to a colleague before the
   regular review process if you're unsure about what an agent has
   produced.
3. **Function ≠ correctness.** Code that *seems* to function and
   passes tests still poisons the well if quality is bad. The
   human-in-the-loop catches that gap.

The brain's `confidence:` floor (agent-authored content starts at
`low` or `medium`, never self-promotes to `high`) is the brain-side
mirror of this rule.

## 4 — PR reviews

PRs are where teams learn together. They're significant, important
interactions that — done right — improve products and grow teams.
**It's not the only time to interact with colleagues** — early
architectural conversations save downstream rework.

### As an author — the be's

| Be                   | What it means                                                                                                        |
|----------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Be prepared**      | Aim to have ~1 week of appetite left when you submit your last PR. Good reviews need time on both sides.              |
| **Be rigorous**      | Final QA round in the user hat: copy makes sense? edge cases? accessibility? dark mode? Reviewer doesn't verify it works. |
| **Be reflective**    | Self-review *before* marking ready. Significant rearchitectures often surface here.                                   |
| **Be clear**         | The reviewer reads the PR alone — no chat history, no original pitch. Preempt all reviewer questions.                 |
| **Be communicative** | Approved → make meaningful changes → request review again. Lint fixes are fine, architecture changes are not.         |
| **Be incremental**   | Smaller increments = faster customer feedback + lower risk. Use feature flags for rollouts and preview environments for internal feedback. |
| **Be deliberate**    | Pick reviewers across five lenses: framework experts, platform experts, technical-domain experts, design/UX experts, business-domain experts. Get at least one *external* review. |

**PR description must include** (when applicable): why the PR
exists (business value), screenshots/recordings of before/after,
what to look out for + how to test, decisions and trade-offs, how
the author tested, follow-up changes deferred to other PRs,
roll-out plan, roll-back plan. Not every section applies to every
PR — a dependency bump doesn't need before/after screenshots.

**Three "ship-or-not" questions for incremental PRs:**

1. Can it be shipped to real customers?
2. Does it leave the campsite at least as clean (or cleaner) than I found it?
3. Am I happy with this change if nothing else is shipped?

### As a reviewer — the be's

| Be                | What it means                                                                                                        |
|-------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Be respectful** | The author has done their best; PRs can almost always be improved — that's normal. Point out what you like, not just what to change. |
| **Be responsive** | Treat review requests as urgent. Next context switch = the review. The author may be blocked.                        |
| **Be thorough**   | Read the *Why* twice. Question the architecture (strong + stable abstractions?). Trace data flow. Mind the details.  |
| **Be clear**      | "Can we refactor this function to a utility module that we then use here?" beats "can we do this better?".           |
| **Be deliberate** | Pick the right review status: **Accept** (understood, can't improve), **Comment** (cosmetic), **Request changes** (bugs, deprecated patterns, perf concerns, mismatched abstractions). |

**Formatting.** Code feedback as line-review comments (each
suggestion resolves individually). Use the review description for
short context and praise — visible to all, not buried in threads.

## How this propagates into the brain

- **`/shape` phase 2 (Tech Lead)** — the ADR's `## How` section
  cites this page for testing strategy and abstraction stance.
- **`/shape` phase 3 (Developer)** — TDD, self-review, and
  small-increments rules apply directly to the implementation PR in
  the sibling repo.
- **PR templates** — the brain's `/pr` skill ships PR descriptions
  that include the playbook's required sections (Why / What to look
  out for / Test plan / Trade-offs / Roll-out / Roll-back).
