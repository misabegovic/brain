---
name: ask
description: Single entry point for everything that *queries* the brain. Auto-routes the question to wiki-query (factual), wiki-plan (planning a task), wiki-overlap (checking duplication), or wiki-coverage (gap analysis on a repo). Load when the user says "ask", "query", "what is", "how do we", "plan", "outline", "coverage", "overlap", "duplicate", or invokes `/ask`.
---

# Ask — single entry for querying the brain

You are working in `~/projects/brain`. There are four read-side
operations underneath this one skill — `wiki-query`, `wiki-plan`,
`wiki-overlap`, `wiki-coverage`. This skill picks the right one based
on the phrasing of the question.

## Routing

Default is `wiki-query` (factual lookup). Promote to a more specific
skill when the phrasing matches:

| Phrasing cue                                              | Skill          |
|-----------------------------------------------------------|----------------|
| "who calls X", "what depends on X", "what breaks if I change X", "how coupled is X", "what does repo Y contain" | the **code substrate first** — `brain.py structure findings` / `brain.py enola impact`, then `wiki-query` for the narrative around the answer |
| "plan", "outline the work", "what do I need for X", "how should I approach X" | `wiki-plan`    |
| "overlap", "duplicate", "stepping on", "anyone else doing X", "is anything similar in flight" | `wiki-overlap` |
| "coverage", "what's missing in repo X", "how much do we know about repo X", "what isn't documented in X" | `wiki-coverage`|
| "what is", "where is", "why did we", "have we discussed", "show me", anything else factual | `wiki-query` (default) |

A question can legitimately span multiple skills (e.g. "plan a refactor
of the candidate scoring system — is anyone else working on it?"). In
that case run them in order: `wiki-plan` first, then `wiki-overlap` as
part of step 4 of the plan protocol. Don't fork into parallel skills;
chain them.

The substrate row goes first when the question is structural because it
answers *deterministically* where the wiki answers from synthesis: the
wiki says why a thing exists, the substrate says what actually touches
it. Where they disagree, the disagreement is the finding. Findings are
candidates to verify, not verdicts, and both tiers skip cleanly when
absent.

## Overrides

The user can force a route with a leading marker:

- `query: <question>` — factual lookup, even if phrasing sounds like a plan.
- `plan: <task>` — go straight to `wiki-plan`.
- `overlap: <topic>` — go straight to `wiki-overlap`.
- `coverage: <repo>` — go straight to `wiki-coverage`.

## Announce before acting

Before running, state in one sentence which skill(s) you're picking
and why. Example:

> "Reading this as a coverage question on `infrastructure` — running wiki-coverage."

If you're chaining (plan → overlap), say so.

## Then

Hand off to the chosen skill and follow its full protocol. This skill
is just the dispatcher.

`wiki-query` and `wiki-plan` don't write to the wiki by default;
`wiki-overlap` writes overlap pages; `wiki-coverage` may append to a
reference page. Each underlying skill's done-check applies as written.

## Done check

- [ ] Routing decision was announced.
- [ ] Underlying skill ran its full protocol.
- [ ] If two skills chained, both produced their expected output.
