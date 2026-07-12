---
title: "Human-legible presentation layer — an opinionated, Shape Up-native UI that triages attention"
kind: pitch
status: draft
updated: 2026-07-12
appetite: big
confidence: medium
sources:
  - ../../../sources/conversations/2026-07-12--ui-rethink-and-rewrite-question.md
  - ../../insights/quickstart-third-command-fragility.md
---

# Human-legible presentation layer

Pre-bet pitch per the operator's 2026-07-12 direction: the UI
should breathe Shape Up, be highly opinionated about what it shows
and when, bring what needs attention to attention, show where we
are / were / are going — and the agent processing connector signal
should judge whether the operator needs to look. "Making the brain
my true partner."

## Problem

The wiki is agent-optimized and must stay that way: verbose,
complete, every claim cited. But the UI renders that layer
*neutrally* — a generic documentation site where a superseded ADR,
an open bet, a stale draft, and a critical connector finding are
all just pages of equal visual weight. The non-terminal-PM persona
names the cost: humans can't parse walls of text on every visit;
they need to know *what matters now* in seconds. The deeper gap is
that the corpus already **knows** everything an opinionated surface
needs — kinds carry the Shape Up lifecycle (idea → topic → pitch →
bet → PRD/ADR/epic → shipped → superseded), `state.md` carries
past/now/target, appetites and statuses and ages are in
frontmatter, the inbox carries pending work — and the UI uses none
of it as *opinion*. Meanwhile connector signal (a Langfuse error
batch, a Datadog monitor flip) lands as mechanically-prioritised
inbox items: nothing judges whether the operator personally needs
to see it, so the human either reads everything or trusts nothing.
A partner is opinionated; the current UI is a filing cabinet.

## Appetite

Big — the largest UX bet since the workbench, expected to land as
staged slices (schema summaries → opinionated home → lifecycle
components → attention judgement) rather than one drop. The
appetite is a spending limit on the whole arc: if the component
layer alone consumes it, the graph visualisations wait for a new
bet. Explicitly *not* in the appetite: any kernel rewrite — the
same conversation asked about Ruby/Rust and the answer (recorded
in the capture) is that the presentation layer is rebuilt on the
existing Astro stack, where components are already native.

## Solution

Fat-marker, five elements.

**1. Summaries as schema, not UI magic.** Every page gains an
agent-maintained executive summary (a `summary:` frontmatter field
— one to three sentences, present tense, updated whenever content
changes). The validator nudges; the views pipeline exposes it; every
component below renders it. Humans read summaries-of-the-synthesis;
agents keep reading the full page. One source of truth, two
altitudes.

**2. An opinionated home — the partner's briefing, not a page
list.** Three bands, in priority order: **Needs you** (attention
verdicts from the tend loop + failing health + human gates waiting,
e.g. a pitch awaiting a bet, an insight awaiting confirmation);
**In flight** (post-bet work: living PRDs/epics with their state
and age); **On the table** (open pitches with appetite, open
topics, fresh ideas). Beneath them, the orientation strip: where we
were (recent shipped/graduated, from the trail), where we are
(`state.md` § Now + health), where we're going (§ Target + open
bets). Everything above the fold is a judgement, not a listing.

**3. Lifecycle-native components.** The UI knows Shape Up: a pitch
renders as a betting card (appetite, age, problem one-liner); a
PRD as an in-flight card (bet date, now/target delta); an ADR as a
decision card (status chip, supersedes chain); a topic as a
discussion card (last entry, open question). Graduation chains
(`supersedes` edges) render as a trail timeline; the link graph
gets a visual. Built as Astro components over the derived index
and `pages.json` — the data layer already exists.

**4. Attention judgement in the tend loop.** The mechanism half:
when a session digests connector items, the agent adds a triage
verdict — needs-operator / fyi / routine — with a one-line reason,
stored on the item and surfaced verbatim in the **Needs you** band
("Langfuse: novel error class in prod prompts — look today" vs.
"Langfuse: volumes nominal — routine"). Producers stay
deterministic and dumb; judgement happens only in-session
(queue-and-tend unchanged). The operator can grade a verdict
("this wasn't worth my attention"), and the grade feeds the next
session's calibration — the partner learns what its human considers
important.

**5. The empty state is a first-class state.** A fresh shell's
opinionated home says what a partner would say on day one — here's
how to give me something to work with — not a blank dashboard. (The
cold-start insight from the Noor playthrough feeds this directly.)

## Rabbit holes

- **Alarm fatigue** — the daily-operator persona's core
  frustration: three wrong "needs you" verdicts in a week and the
  band is dead. The calibration loop (operator grades verdicts) is
  the counterweight and must ship *with* the judgement, not after.
- **Summary drift** — a `summary:` that no longer matches its body
  is worse than none. Needs a cheap staleness check (summary
  untouched while body changed materially) in the existing gates,
  not a new subsystem.
- **Visualisation scope creep** — graph views can consume the whole
  appetite. Timeline + link graph are in; anything interactive
  beyond hover/click detail is out until a future bet.
- **Starlight's grip** — the opinionated home may outgrow the docs
  theme; custom Astro pages are fine (onboarding already is one),
  but a wholesale theme replacement is its own pitch, not a detour
  inside this one.
- **Judgement without provenance** — an attention verdict the
  operator can't trace ("why did you flag this?") erodes the trust
  it exists to build; every verdict carries its one-line reason and
  a link to the underlying item.

## No-gos

- No kernel or language rewrite; no ERB/ViewComponents layer — the
  presentation rebuild happens in the existing Astro stack (the
  rewrite question is answered in the cited capture).
- No second content store: every human-facing artefact derives
  from `wiki/` + the derived index. Nothing is authored in the UI.
- The UI stays read-only; humans act through their agent and git.
- No scheduled LLM runs — attention judgement is in-session only,
  per the queue-and-tend decision.
- Agents' reading surface is untouched: summaries are additive;
  the verbose layer remains the source of truth.

## RFC

Reactions from the brain's own user personas
(`.claude/personas/users/`):

- **Priya (non-terminal PM):** *"This is the product I was promised.
  Two asks: every card answers 'why should I care' in its first
  line, and the ai-suggestion/approved distinction must survive
  into the components — a draft rendered as a confident card is how
  I get burned in a meeting."*
- **Viktor (daily operator):** *"The 'Needs you' band lives or dies
  on precision. I want the grading loop from day one, and I want
  'routine' to be the default verdict under uncertainty — a partner
  that cries wolf is worse than a filing cabinet I at least
  trust."*
- **Noor (cold-start adopter):** *"An opinionated home is also the
  best empty state you could build — if it tells me what to feed
  the brain first. If the briefing bands render blank boxes on a
  fresh clone, you've rebuilt my giving-up point with nicer CSS."*
- **Sam (security reviewer):** *"Read-only and derived-only keeps
  my sign-off. Watch the dependency surface of graph libraries in
  the UI build, and keep attention verdicts out of any serving-mode
  response if they quote raw connector payloads — error strings
  leak secrets more often than anyone expects."*
