---
title: "Human-legible presentation layer — the UI becomes the partner's briefing: opinionated, Shape Up-native, attention-first"
kind: initiative
status: living
updated: 2026-07-12
confidence: medium
supersedes: brain/pitches/human-legible-presentation-layer.md
summary: >
  The UI stops being a neutral doc site: agent-maintained summaries
  on every page, a briefing home that triages what needs the
  operator's eyes, lifecycle-aware Shape Up cards, and attention
  verdicts judged in the tend loop. Humans read the briefing;
  agents keep the verbose wiki.
sources:
  - ../pitches/human-legible-presentation-layer.md
  - ../../../sources/conversations/2026-07-12--ui-rethink-and-rewrite-question.md
---

# Human-legible presentation layer

Graduated from the
[pitch](../pitches/human-legible-presentation-layer.md) on the
operator's 2026-07-12 bet ("ok, do it"). The RFC reactions on the
pitch are requirements here: the grading loop ships *with* the
judgement, "routine" is the default verdict under uncertainty
(Viktor), the ai-suggestion/approved distinction survives into
every card (Priya), the empty state guides rather than blanks
(Noor), and verdict reasons never quote raw connector payloads
(Sam).

## What

Five shipped elements: (1) an agent-maintained `summary:`
frontmatter field on wiki pages, exposed through the views
pipeline; (2) a briefing surface — the app's landing page — with
three judgement bands (Needs you / In flight / On the table) and a
where-we-were/are/going orientation strip; (3) lifecycle-native
components rendering each page kind at its Shape Up stage (betting
cards, in-flight cards, decision cards with supersedes chains, a
trail timeline, a link-graph visual); (4) attention verdicts —
needs-operator / fyi / routine with a one-line reason — attached to
inbox items by the tend session and rendered verbatim in the Needs
you band, plus an operator grading loop that calibrates future
verdicts; (5) a first-class empty state that tells a fresh shell's
operator what to feed the brain first.

## How

Fat-marker (the ADR names the bets): summaries live in frontmatter
and flow through `pages.json`; the briefing is a build-time Astro
page over `pages.json` + the inbox + `state.md`, rebuilt by the
existing self-heal loop; components are dependency-free Astro over
the same data; verdicts and grades are small CLI verbs on the
existing inbox (`judge`, `grade`) so the tend skill records
judgement in-session and reads grades back as calibration; the
kernel's producers stay deterministic and the schedule never runs
an LLM. Staged within one appetite: summaries → briefing → cards →
judgement; the graph visual rides only if the appetite allows.

## Why

The wiki is agent-optimized and must stay that way; the humans it
serves need altitude, judgement, and orientation — the
non-terminal-PM persona can't parse walls of text, and the daily
operator needs connector noise triaged before it reaches his eyes.
The corpus already carries every signal an opinionated surface
needs (kinds, statuses, appetites, ages, state sections, the
inbox); rendering it neutrally wastes what the mechanism knows.
"The brain as true partner" (operator, 2026-07-12) is the mission:
a partner is opinionated about what matters now.

## Now

Shipped 2026-07-12 with the bet: `summary:` in the schema and
validator, summaries authored across the card-rendered kinds,
`pages.json` carrying summary + appetite, `inbox judge`/`grade`
CLI verbs, the briefing page as the app's landing surface with the
three bands + orientation strip + empty-state guidance, decision
cards honouring the ai-suggestion distinction, and the tend skill's
judgement + calibration steps. Trail timeline and link-graph visual
are within-appetite follow-ups.

## Perceived

The risk the RFC names twice: judgement precision. If Needs-you
verdicts miss (alarm fatigue) or summaries drift from bodies, the
briefing reads confident and wrong — worse than the neutral site it
replaced. The grading loop and the groom-time summary check are the
counterweights; whether they hold is only knowable from lived use.

## Target

The briefing is the operator's first read of every session and the
first thing a Priya-shaped colleague sees; connector noise arrives
pre-judged with traceable reasons; grades accumulate into visible
calibration. The trail timeline and graph visual land within the
appetite. A Priya playthrough before and after measures whether the
components actually shorten time-to-understanding — the loop this
initiative exists to serve.
