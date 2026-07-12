---
title: <one-line statement, e.g. "Adopt OpenTofu in place of Terraform">
kind: decision
status: suggested                   # AI-suggested only — never `accepted` until graduated
ai_suggestion: true
updated: YYYY-MM-DD
team: <owning team or "(inferred)">
repos:
  - <target repo>
confidence: low                     # AI-authored — never above low until human reviews
sources:
  - <observed paths in sibling repo, prep notes, brain pages cited>
---

# <one-line statement>

> **AI-suggested ADR.** Does **not** reflect a human-approved
> decision and does **not** record current product state or
> upcoming product changes. This page is **agent-authored
> synthesis** of observed repo state and (where applicable) prep
> notes — a *suggestion* for a human to review, iterate on, and
> either graduate (drop the `ai_suggestion: true` flag, change
> status to `accepted`, move file from
> `wiki/<repo>/ai-suggestions/adrs/` to `wiki/<repo>/adrs/`) or
> supersede with a different framing.
>
> All "Context" / "Considered options" / "Inferred consequences"
> content below is **inference from observed state, not
> testimony from the deciders**. Treat anything that reads as a
> declarative claim about *why* something was decided as
> hypothesis, not fact.

This template is for ADRs an agent authored on its own initiative
without a human review-iterate-approve loop in the same session.
It lives under `wiki/<repo>/ai-suggestions/adrs/` so the
human-approved trail at `wiki/<repo>/adrs/` stays clean.

> **What does NOT belong in this ADR.**
>
> Same rules as the human-supervised template:
>
> - **No code blocks.** Implementation specifics belong in repo
>   READMEs, `permanent/interfaces.md`, or operational docs;
>   the ADR cites them in prose.
> - **No interface schemas / endpoint payloads / class
>   definitions.**
> - **No how-to instructions.**
> - **Narrative in complete sentences.** Bullet lists for
>   enumerations only.

## Context

The forces at play, **as the agent observes them** from the
sibling-repo state and brain pages cited above. Frame in
present-tense for what's true today; past-tense for what
appears to have led to the decision.

Mark inference explicitly: "the prep notes suggest X" or "the
commit history (link) is consistent with Y" — not "the team
chose X." A human reviewer should be able to read this section
and immediately see which claims are observation and which are
hypothesis.

## Inferred decision

What the agent thinks the decision is, expressed in active
voice. *"The team appears to have adopted X."* / *"The repo
state is consistent with the team having decided to Y."*

Avoid first-person plural ("We will…") — that framing implies
team membership the agent doesn't have. Use
attribution-with-uncertainty.

## Considered options (agent surfacing)

Options the agent thinks are worth surfacing for the human to
weigh. **Not** "the alternatives the team considered" — the
agent has no way to know that without testimony.

Each option gets one paragraph: what it is, why a reasonable
team might pick it, what evidence in the brain or sibling repo
points toward or away from it.

- **Option A** *(matches observed state)* — short summary; the
  current shape of the repo is consistent with this option.
- **Option B** — what it would have looked like; why the agent
  thinks it was likely rejected (or why the agent isn't sure).
- **Do nothing** — the implicit baseline; what staying with the
  prior state would have meant.

## Inferred consequences

What the agent thinks this commits the team to. **All
consequences as the agent infers them** — positive, negative,
neutral. The agent's inference is necessarily incomplete; flag
known gaps explicitly.

Group as makes sense:

- **Closes** doors that this decision shuts.
- **Opens** capabilities this decision enables.
- **Costs** trade-offs the team appears to have accepted.

## Open questions for the human reviewer

What the agent couldn't resolve from observation alone, and
where human testimony or organisational context would change
the framing.

Three to seven specific questions. Not "is this right?" but
"was alternative B considered seriously?" or "is the team
aware of consequence C?" — questions a human can answer in a
review.

## Suggested next step

What the agent recommends the human do with this suggestion:

- **Graduate** if the suggestion captures the decision well.
  (Drop the `ai_suggestion: true` flag, change status to
  `accepted`, move to `wiki/<repo>/adrs/`, fix any factual
  errors the human catches.)
- **Iterate** if the framing needs work. Edit in place; the
  file stays under `ai-suggestions/` until graduated.
- **Reject** if the decision wasn't real or shouldn't be
  recorded. Move to `wiki/_archive/` or delete with a log
  line.
- **Re-author** if the suggestion captures something true but
  the framing is wrong. Discard this file; a human or another
  agent re-pitches.

## Sources

The full list of brain pages, sibling-repo paths, and prep
notes the agent drew from. **Every load-bearing claim above
should be traceable to a source listed here.** A human
reviewer's first check is: do the cited sources support the
inferences?
