---
title: Render-prove the AI-draft trust chrome instead of waiting for the first real draft
kind: initiative
status: draft
ai_suggestion: true
updated: 2026-07-12
team: brain
repos:
  - brain
appetite: small
confidence: low
summary: >-
  Two playthroughs, two versions apart, both found the ai-suggestion banner
  shipped in code but never rendered against live content — the corpus has
  zero AI-draft pages, so the product's load-bearing trust distinction is
  unproven exactly where its most trust-sensitive reader would look.
  Suggested fix is a build-time render check that fails the UI build when
  the banner path goes unexercised.
sources:
  - sources/playthroughs/2026-07-12--priya-non-terminal-pm--agent-sweep.md
  - sources/playthroughs/2026-07-12--priya-non-terminal-pm--briefing-first-read.md
---

# Render-prove the AI-draft trust chrome instead of waiting for the first real draft

> **AI-suggested PRD.** Does **not** reflect a human-approved
> initiative and does **not** record committed work or upcoming
> product changes. This page is **agent-authored synthesis** —
> a *suggestion* a human can review, iterate on, and either
> graduate (drop the `ai_suggestion: true` flag, change status
> to `living`, move file from `wiki/brain/ai-suggestions/prds/`
> to `wiki/brain/prds/`) or supersede with a different framing.
>
> Treat the personas / problem / appetite / metrics below as
> **the agent's hypothesis**, not the team's commitment. The
> PM (human) owns whether this becomes a real initiative.

## Why the agent suggests this

The Priya agent-sweep playthrough (2026-07-12, v0.19.3) probed
whether the ai-suggestion/approved distinction survives into what a
non-terminal reader sees. It found the distinction render-proven for
*superseded* decisions (the retired chat-surface ADRs each carry a
visible "Superseded. The record moved on" banner) but structurally
unprovable for *AI drafts*: the corpus contains zero pages under any
`ai-suggestions/` shelf, the aggregated view reports "0
suggestion(s)", and no build has ever rendered the banner against
real content. The earlier Priya walk (v0.17.0,
`briefing-first-read`) recorded the same condition and deferred it —
"first real suggestion exercises it." Two versions later nothing
had, which the sweep reads as evidence that waiting is not a
mechanism. The sweep itself then authored the first live suggestion
(this page) and render-verified the banner by building the UI — a
one-off proof that decays the moment this page graduates or is
rejected, returning the corpus to zero examples.

## Inferred objective

If the UI build (or CI validate step) rendered a synthetic
`ai_suggestion: true` page on every run and failed when the banner
or its chips were absent from the output, the trust distinction
Priya depends on would stay continuously proven, independent of
whether the corpus happens to contain a live draft that day.

## Affected personas (agent-inferred)

- `priya-non-terminal-pm` (.claude/personas/users/priya-non-terminal-pm.md) —
  her stated giving-up point is discovering that a page she cited in
  a meeting was an unreviewed AI draft; she has no way to audit the
  banner mechanism herself, so the product must prove it for her.
- `noor-cold-start-adopter` (.claude/personas/users/noor-cold-start-adopter.md) —
  a fresh instance starts with zero drafts by design, so every new
  adopter inherits the unproven-banner window until their first
  agent-authored suggestion lands.

## Now / Perceived / Target (agent's read)

- **Now** — the banner logic exists in the page renderer (path- and
  frontmatter-detected) and the onboarding deck tells readers "trust
  the banner", but the live corpus has no page that exercises it;
  the only render evidence is the one-off build in the sweep
  transcript.
- **Perceived** — the onboarding deck and AGENTS.md present the
  banner as a standing, load-bearing safety property; nothing
  records that it is unverified between drafts.
- **Target** (hypothesis) — every UI build proves the trust chrome:
  a deliberate fixture page (clearly marked, excluded from search
  and the briefing) or an equivalent build-time assertion renders
  the ai-suggestion banner, the superseded banner, and the
  kind/status/confidence chips, and the build fails loudly if any
  are missing.

## Scope (suggested)

A build-time or validate-time check that renders the trust chrome
against synthetic frontmatter and asserts the banner text and chips
appear in the output; a decision on whether the fixture lives as a
hidden test page or a renderer-level assertion; a one-line note in
the onboarding deck only if the mechanism changes what readers see.

## No-gos (suggested)

- No permanent fake content in the reader-visible corpus — the
  fixture must never appear in search, the briefing bands, the
  trail, or the dashboard counts.
- No weakening of the folder-separation rule; the check proves the
  chrome, it does not relax where suggestions may live.

## Rabbit holes (suggested)

Snapshot-testing the whole page HTML would couple the check to
styling churn; assert on the banner's presence and its
distinguishing text, not on layout. Deciding between fixture-page
and renderer-unit-test could stall — either satisfies the
objective.

## Appetite (estimated)

Small. The renderer already branches on the flag; the work is one
test surface plus a CI wire-up.

## Suggested success metrics

The UI build fails when the ai-suggestion banner branch is removed
or broken; a reader-facing statement ("trust the banner") is backed
by a check that has run on every release since adoption; the next
persona playthrough finds the distinction verifiable without
authoring a suggestion first.

## Open questions for the human reviewer

- Is a hidden fixture page acceptable in the corpus, or must the
  proof live entirely in the UI's test layer?
- Should the same check cover the superseded banner and confidence
  chips, or is the AI-draft banner the only chrome worth gating?
- Does this overlap with UI test work already planned that the
  agent cannot see?

## Suggested next step

Iterate or graduate: if the team agrees the trust chrome needs
continuous proof, graduate with the fixture-vs-test decision made;
if the team prefers to rely on live drafts existing, reject with a
log line so the next playthrough stops re-flagging it.

## Sources

- sources/playthroughs/2026-07-12--priya-non-terminal-pm--agent-sweep.md
  — the sweep that found the unexercised banner and render-verified
  it once by authoring this page.
- sources/playthroughs/2026-07-12--priya-non-terminal-pm--briefing-first-read.md
  — the v0.17.0 walk that first recorded the banner as untested
  against live content.
