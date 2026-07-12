---
persona: .claude/personas/users/priya-non-terminal-pm.md
scenario: first read of the rewritten UI — briefing, decision trace, views
version: 0.17.0
date: 2026-07-12
executed_by: claude (fable 5)
---

# Playthrough — Priya reads the new UI (presentation-layer rewrite)

Run in the rewrite's shipping session, against the live local build
(real fetches + headless-Chrome screenshots at 1560px and narrow
widths).

## Step 1 — the briefing (/)

Renders three bands + orientation. In character: "I know in five
seconds that one hypothesis needs confirmation, one bet is in
flight, and three discussions are open — with a one-line why on
every card. This is the meeting brief I used to assemble by hand."

**Finding A (grooming, fixed in-session).** The In-flight band's
first render showed **six** bets in flight — five of them shipped
initiatives (0.5–0.16) whose PRDs were never flipped to
`superseded` per the shipped-PRD convention. The opinionated
surface exposed the stale statuses within a minute of existing;
all five superseded to `brain/state.md`. Exactly the class of
Now-vs-Perceived gap the briefing exists to surface.

## Step 2 — decision trace

`/brain/adrs/workbench-pty-bridge/`: chips (decision · superseded ·
confidence · updated), the superseded banner linking to the
successor, the executive summary as a lead. In character: "I can
cite this in a meeting without reading it, and I can't mistake it
for current policy — the banner does the work."

**Finding B (defect, fixed in-session).** The page body's own `# H1`
rendered under the chrome's title — a duplicate heading on every
page (the retired theme used to strip it). Fixed in the renderer.

**Finding C (defect, fixed in-session).** `/search/` returned the
JSON API's `{"error": "missing q"}` — a route collision between the
API's `/search?q=` and the UI's search page. The API now claims the
path only when `?q=` is present.

## Step 3 — narrow screens

At the narrowest viewport headless Chrome honours, the layout is
single-column, nav wraps, nothing overflows.

**Measurement note for future playthroughs:** headless Chrome
floors the layout viewport at **500px** (`innerWidth=500` at
`--window-size=390`) and crops the screenshot — which first
presented as a phantom mobile-overflow bug and consumed a
fix-and-reshoot cycle before a probe page exposed it. Sub-500px
checks need real device emulation, not `--window-size`.

## Not verifiable this walk

The ai-suggestion banner and the briefing's AI-draft cards ship in
code but no `ai-suggestions/` page exists in the corpus to render —
untested against live content. First real suggestion exercises it.

## Give-up verdict (in character)

"Nothing here made me want to leave. The one thing I'd watch: the
Needs-you band mixes verdict cards (from connector judgement) with
gate cards (bets, hypotheses) — fine at this volume, but if both
grow, I'd want the interrupts visually louder than the standing
gates."

## Disposition

- Finding A — grooming applied in-session (five PRDs superseded);
  transcript-only.
- Findings B, C — fixed in-session; transcript-only.
- Measurement note — transcript-only (playthrough craft, not
  product).
- Band-mixing observation — below the decision threshold at
  current volume; stays here.
