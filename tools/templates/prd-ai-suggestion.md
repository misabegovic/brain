---
title: <one-line user-facing title>
kind: initiative
status: suggested                   # AI-suggested only — never `living` until graduated
ai_suggestion: true
updated: YYYY-MM-DD
team: <owning team or "(inferred)">
division: <umbrella division or "(inferred)">
repos:
  - <target repo>
appetite: small | medium | big      # the agent's appetite estimate; the human can revise
confidence: low                     # AI-authored — never above low until human reviews
sources:
  - <issue source / Notion URL / feedback insight / brain pages / observed gaps>
---

# <one-line user-facing title>

> **AI-suggested PRD.** Does **not** reflect a human-approved
> initiative and does **not** record committed work or upcoming
> product changes. This page is **agent-authored synthesis** —
> a *suggestion* a human can review, iterate on, and either
> graduate (drop the `ai_suggestion: true` flag, change status
> to `living`, move file from `wiki/<repo>/ai-suggestions/prds/`
> to `wiki/<repo>/prds/`) or supersede with a different framing.
>
> Treat the personas / problem / appetite / metrics below as
> **the agent's hypothesis**, not the team's commitment. The
> PM (human) owns whether this becomes a real initiative.

This template is for PRDs an agent authored on its own initiative
without a human review-iterate-approve loop in the same session.
It lives under `wiki/<repo>/ai-suggestions/prds/` so the
human-approved trail at `wiki/<repo>/prds/` stays clean.

> **What does NOT belong in this PRD.**
>
> Same rules as the human-supervised template:
>
> - **No code samples.**
> - **No technical interface definitions** (endpoints, JSON
>   schemas, function signatures, database tables).
> - **No "how" detail beyond feasibility-check level.**
> - **No commitments to specific libraries / vendors.**

## Why the agent suggests this

A short paragraph: what the agent observed (an open thread in
a synthesis page, a flagged gap in a state.md, a customer-
feedback insight, a pattern from a sibling repo) that motivates
the suggestion. Cite the source(s) explicitly.

Mark inference: "the brain's `agent-surfaces-converging` insight
flags X" or "the prep notes mention Y as an open question." Not
"the team needs Z" — the agent has no way to know what the team
needs without testimony.

## Inferred objective

What the agent thinks would ship if this PRD became work, and
what user outcome that would produce. One sentence. Frame in
hypothesis-mode: *"If the team adopted X, it would produce Y for
Z personas."*

## Affected personas (agent-inferred)

- `[<persona-name>](../../../.claude/personas/users/<slug>.md)` —
  the agent's read on the persona's relevance. The human
  reviewer should validate that this persona is real and
  affected as described. If the persona doesn't yet exist in
  `users/`, propose adding it (don't fabricate a persona).
- (one entry per primary persona)

## Now / Perceived / Target (agent's read)

- **Now** — what the agent observes is true today, citing
  sibling-repo paths and brain reference pages.
- **Perceived** — what the brain currently records as the
  org's belief. The agent can read this from existing brain
  pages but **cannot** know the org's actual belief without
  human input.
- **Target** — the state the suggestion points toward. Frame
  as hypothesis.

## Scope (suggested)

What the agent thinks would be in scope, at PRD fidelity. The
human reviewer adjusts.

## No-gos (suggested)

What the agent thinks should be explicitly out of scope. The
human reviewer adjusts.

## Rabbit holes (suggested)

Where the agent thinks engineering would risk getting stuck if
this became work. The human reviewer often catches more.

## Appetite (estimated)

Small | medium | big — the agent's first-pass estimate. The
agent has no organisational context for capacity, competing
priorities, or strategic weight; treat the estimate as
load-bearing only on the technical-complexity dimension.

## Suggested success metrics

What the agent thinks "shipped well" would look like. The
human reviewer validates that these are the right metrics for
the team's goals.

## Open questions for the human reviewer

Specific questions a human can answer in a review:

- Is the affected persona real and the framing accurate?
- Does this overlap with in-flight work the agent doesn't
  know about?
- Is the appetite plausible given current team capacity?
- Does the metric framing match what the team would actually
  measure?
- Is the suggestion landing in the right repo?

## Suggested next step

What the agent recommends the human do with this suggestion:

- **Graduate** if the suggestion captures a real initiative
  the team should pursue. (Drop `ai_suggestion: true`, change
  status to `living`, move to `wiki/<repo>/prds/`, fix any
  factual errors, hand to Tech Lead for ADR.)
- **Iterate** if the framing needs work. Edit in place; the
  file stays under `ai-suggestions/` until graduated.
- **Reject** if the suggestion doesn't reflect a real
  initiative. Move to `wiki/_archive/` or delete with a log
  line explaining why.

## Sources

The full list of brain pages, sibling-repo paths, issues,
feedback items the agent drew from. Every load-bearing claim
above should be traceable to a source listed here.
