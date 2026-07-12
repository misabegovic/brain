---
title: "Authoring ADRs and PRDs"
kind: meta
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../AGENTS.md
  - .claude/skills/shape/SKILL.md
---

# Authoring ADRs and PRDs in the brain

This page is the binding playbook for every ADR and PRD authored in the
brain. A **PRD** is *the spec*: it makes the user need, the appetite, the
solution sketch, the no-gos, the rabbit holes, and the decision needed
unambiguous. An **ADR** is *the bet*: what gets built and why, with the
rejected alternatives on record. The brain's
[`/shape` skill](../../.claude/skills/shape/SKILL.md) is the *only* path to
`wiki/<scope>/{adrs,prds}/` — never write to those folders by hand. When this
page conflicts with the schema in AGENTS.md, AGENTS.md wins; open a change to
re-align. The skill file wins on *mechanics*; this page wins on *what
required reading applies*.

`/shape` runs in three phases (forward mode) or one (record-existing mode).
Before each phase, consult the required reading: the schema's shaping and
routing sections plus the target scope's `state.md` before pre-flight; the PM
persona and the org's cadence conventions before Phase 1; the PRD plus the
target repo's `permanent/` layer before Phase 2; the ADR plus the sibling
repo's own conventions before Phase 3.

## Hard rules — what never appears in an ADR or PRD

- **No code blocks** of any kind — no application code, no config, no shell.
  Names and identifiers can be quoted in prose; configuration belongs in repo
  READMEs or `permanent/interfaces.md`. ADRs focus on *why*, not *how*.
- **No interface schemas** (endpoints, payloads, class definitions, tables).
  Those live in `permanent/interfaces.md` or a reference page; the ADR cites
  them.
- **No runbooks or migration steps** in the body. Operational docs own those.
- **Narrative in complete sentences.** Bullet lists for enumerations only
  (alternatives, consequences, affected personas).

## Pace and depth

Phase 1 pre-flight runs a **deepdive** on the load-bearing points of the
pitch before a word is drafted: identify the 2–4 places where the decision
pivots on constraints not yet known, fetch the constraining context for each
(sibling-repo code, prior ADRs and PRDs in scope, `permanent/` pages, git
history, external sources verbatim), and weave the findings into the PRD's
background so the Tech Lead sees *why* certain alternatives are pre-empted.
See [`adrs/shape-deepdive-pre-flight.md`](adrs/shape-deepdive-pre-flight.md).

The pace half of the same discipline: shaping is a deliberate multi-step
exercise, not a race to the page. Rushing produces shallow PRDs whose
background reads as a restated pitch, ADRs that miss real alternatives
because the constraints were never loaded, and builds that the pattern-fit
check has to reverse. Both halves are proportional — a small pitch warrants a
small deepdive (sometimes a single grep) and a quick draft; a substantive
pitch warrants reading several files and **slowing down at phase fronts** to
re-read what just shipped before starting the next phase. *"Show me"* /
*"demonstrate"* / *"do it all"* signals from the user are invitations to be
deliberate, not deadlines — the user pays the iteration cost when the agent
rushes, so quiet front-loaded context-fetching compresses total cost. The
discipline is operator-driven judgement, not a validator-enforced step count;
the confidence floor plus the Phase-1 human-approval gate is the backstop.

## Phase 1 — the PRD (PM hat)

Frame the pitch in one sentence — if you can't, decompose it first. Identify
at least one named persona who owns the user need; no phantom users. Set the
appetite (small / medium / big) as a *budget*, not an estimate. Sketch the
solution at PRD fidelity — enough that the Tech Lead can pick a bet, not so
much that you're prescribing implementation. List no-gos and rabbit holes
explicitly, then state the decision the Tech Lead is being asked to make.

Self-review the spec inline before handing it over: scan for placeholders,
internal inconsistencies, scope that needs decomposing, and requirements open
to two readings. PM-authored content starts at `confidence: low`; the ADR
phase bumps the PRD to medium once the bet is documented, and graduation to
high waits for shipped evidence plus human approval — agent-authored content
cannot self-promote in the same change. If the pitch should be rejected (no
clear persona, duplicate, appetite-vs-need mismatch), write a one-paragraph
rejection note and stop.

## Phase 1.5 — optional RFC pass

When the appetite is medium-to-big or the pitch crosses team lines, run an
RFC pass between PRD and ADR: each relevant persona reacts in a single
paragraph, reactions land in an RFC section on the PRD, and the resulting
ADR's alternatives reference the concerns explicitly. Skip in record-existing
mode — there's nothing to RFC about a decision the code already encodes.

## Phase 2 — the ADR (Tech Lead hat)

Read the input in full; the PRD's no-gos and rabbit holes constrain the bet.
Read the target repo's existing patterns and expand established abstractions
rather than special-casing around them. Map the file structure — which files
get created or modified and what each is responsible for. Generate **at least
two alternatives plus "do nothing"** — real rejected options, not strawmen
(in record-existing mode, the options that *were* considered). Apply the
team-persona lenses if the brain ships them; each surfaces a different class
of risk. Then pick the bet and state it concretely, cite the org's testing
strategy rather than restating it, and call out deviations explicitly.
ADR-authored content starts at `confidence: medium` with cited evidence.

## Phase 3 — the build (Developer hat)

The ADR is the input; code in the sibling repo is the output. Read the PRD
and ADR pair in full plus the sibling repo's own agent instructions. Plan the
change as small commits within the appetite. TDD applies with no exceptions —
red, verify red, green, verify green, refactor; wrote code before the test?
Delete it and start over. Verify before claiming done: "tests pass" means you
ran the command and read the output; "should pass" is not a claim you can
make. Self-review your own diff before requesting human review — generated
code is yours.

**The PR body is a short executive summary** — Why + How + spec links,
roughly 150–200 words, and no H2 scaffolding beyond that shape. Two to four
sentences on what's broken or missing today and who feels it; links to the
PRD and ADR; three to six sentences on the bet adopted and the load-bearing
mechanic; a one-line rollout callout only when a rollout step exists. Open as
draft and let the human promote it. What does *not* belong: verification
tables, test-plan checklists, per-file changelogs, restated ADR content — if
the PR is genuinely complex, link to the ADR's decision instead. After the
sibling-repo PR merges, append build notes to the ADR with any deviations,
bump the PRD's status if fully shipped, and append the audit-log line.

## Operator lessons

Short *Why + How to apply* rules graduated from the operator's private
agent-memory store live in two shelves per
[`adrs/operator-lesson-pattern.md`](adrs/operator-lesson-pattern.md):
repo-bound rules as a `## Lessons` subsection on the target repo's
`permanent/conventions.md`, and cross-cutting rules on
[`wiki/org/operator-lessons.md`](../org/operator-lessons.md). Lessons are
subsections, not pages — no frontmatter; provenance lives inline in a
*Graduated from* citation. Missing conventions pages are never auto-created;
orphaned repo-specific lessons land on the org page with a scope note until
the conventions page earns its place.

## Templates and tooling

Start PRDs from `tools/templates/prd.md` (forward mode only) and ADRs from
`tools/templates/adr.md` (both modes). The
[`shape` skill](../../.claude/skills/shape/SKILL.md) is the source of truth
for the flow's mechanics.
