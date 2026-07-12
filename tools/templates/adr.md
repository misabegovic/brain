---
title: <one-line decision statement, present tense, e.g. "Adopt OpenTofu in place of Terraform">
kind: decision
status: proposed                    # proposed | accepted | deprecated | superseded
updated: YYYY-MM-DD
team: <owning team>
repos:
  - <target repo>
confidence: medium                  # raised by reviewers as evidence accumulates
# supersedes: <other-slug>.md      # if this ADR replaces a prior one
# superseded_by:                   # filled in when later superseded
sources:
  - wiki/<repo>/prds/<slug>.md     # the linked PRD this ADR answers
  - <relevant sibling-repo paths or AGENTS.md, ~/projects/<repo>/...>
---

# <one-line decision statement>

Architecture Decision Record for `wiki/<repo>/adrs/<slug>.md`.
Records *why* a decision was made and *what* it commits the team
to — **not** *how* it was implemented.

This template is for **human-supervised** ADRs: a human reviewed
the linked PRD, iterated, approved; a human reviews this ADR,
iterates, approves. The ADR is **immutable once accepted** — if a
later decision overrides this one, supersede it with a new ADR
rather than editing this one.

For **agent-authored** ADRs (no human review yet), use
`adr-ai-suggestion.md` and place the file under
`wiki/<repo>/ai-suggestions/adrs/`.

> **Author guidance — what does NOT belong in this ADR.**
>
> - **No code blocks.** Implementation specifics live in the
>   sibling repo + the Developer agent's PR description. Quote
>   names and identifiers in prose where helpful, but do not
>   paste configuration, scripts, or Ruby/TS/HCL fragments.
> - **No interface schemas.** Endpoint shapes, JSON payloads,
>   class definitions belong in `permanent/interfaces.md` or a
>   dedicated reference page; the ADR cites them.
> - **No how-to instructions.** Runbooks, migration steps, and
>   build commands belong in repo READMEs or operational docs.
> - **No bullet-point fragments.** Per Nygard: complete sentences
>   in paragraphs. Bullet lists are fine for enumerations
>   (alternatives, consequences) but not for the narrative.

## Context

The forces at play. Technological, political, organisational,
project-specific. Neutral language — present the facts and the
tensions, not advocacy. Past tense for what happened, present
tense for what's still true. Cite sources for every load-bearing
claim.

This is the section a future reader needs to understand *why
the question even came up*. If the context isn't compelling,
the rest of the ADR doesn't matter.

## Decision

The response to those forces. Active voice, present tense, "We
will…" framing.

One or two paragraphs. The decision itself is usually short; the
*explanation of why this option won out* lives in
**§ Alternatives**.

## Alternatives

The genuine options considered, including "do nothing." Each
gets one paragraph that names what the alternative is, why a
reasonable team might have picked it, and why this team didn't.

Three to five alternatives is typical. Two is sometimes enough;
zero is a sign the decision wasn't really a decision.

- **Option A** *(chosen)* — short summary; full rationale lives
  in § Decision above.
- **Option B** — what it would have looked like; why rejected.
- **Option C** — what it would have looked like; why rejected.
- **Do nothing** — the implicit alternative; what staying with
  the status quo would have meant.

## Consequences

What this commits the team to. **All** consequences — positive,
negative, and neutral — per Nygard. Be specific. The
consequences section is where future readers come to learn what
this ADR enables and forecloses.

Group as suits the decision; one common shape:

- **Closes** what doors this shuts (capabilities the team can
  no longer pursue without superseding this ADR).
- **Opens** what becomes possible (capabilities the decision
  enables).
- **Costs** trade-offs the team accepts (operational, financial,
  organisational).

## Linked PRD

[`wiki/<repo>/prds/<slug>.md`](../prds/<slug>.md) — the user
need and appetite this ADR answers to. (For ADRs that **don't**
have a linked PRD because they record a pre-existing decision,
omit this section.)

## Build notes

*(empty until the corresponding work ships. Developer agent
appends after the build, recording any deviation from the
plan in § Decision and § Consequences. **Append, don't rewrite**
— the ADR is immutable; the build notes are the addendum.)*
