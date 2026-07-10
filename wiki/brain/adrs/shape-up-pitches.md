---
title: "Adopt Shape Up pitches as a pre-bet brain artifact kind"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
  - .claude/skills/shape/SKILL.md
---

# Adopt Shape Up pitches as a pre-bet brain artifact kind

Brain-meta decision: introduce `kind: pitch` as a first-class artifact, sitting upstream of every other commitment-class artifact. A pitch lives at `wiki/<scope>/pitches/<slug>.md` and follows the Shape Up shape — Problem, Appetite, Solution (at fat-marker fidelity), Rabbit holes, and No-gos. Its defining privilege is that, unlike the epic and the PRD, a pitch is allowed to sketch the solution — including architecture and engineering shape — at deliberately rough fidelity. That is the whole point of a pitch: it shows enough of the shape to bet on without freezing the details an ADR would later commit.

The pitch sits upstream of everything. The lifecycle is pitch → bet → committed work: a pitch the team bets on graduates into either an epic plus children (umbrella scale) or a PRD plus ADR(s) (single-initiative scale). On graduation the pitch is marked `status: superseded` with `superseded_by:` pointing at the epic or PRD it became; an un-bet pitch can sit at `status: draft` indefinitely or be archived. This reframes the PRD as strictly post-bet — committed work the team has decided to do — resolving an overload where the PRD quietly played both the pre-bet and post-bet role. Pitch authoring becomes a `--pitch` mode on the [/shape skill](../../../.claude/skills/shape/SKILL.md); `/shape`'s existing forward mode continues to produce post-bet PRD/ADR pairs for work that is already bet on. Pitches are commitment-adjacent but lower-stakes than PRDs and ADRs (they propose, they don't commit), so an agent-authored pitch under operator supervision lands directly in `pitches/` rather than the suggestion shelf; the betting decision — graduating it — is the human gate that matters.

## Context

The brain runs on Shape Up — cycles, appetite, no-gos, and rabbit holes are already first-class, and the authoring skill is literally named `/shape` after Shape Up's shaping phase. Yet the brain had no artifact for the pitch itself: the shaped-but-not-yet-bet proposal that frames a problem and sketches a solution at fat-marker fidelity for a betting table to weigh. A pitch was only ever an ephemeral input — a card in an external planning tool, a line of inline text — that `/shape` consumed and immediately turned into a committed PRD (`kind: initiative`).

The gap surfaced while shaping an exploratory architecture proposal from an innovation-week card. The work had a strong, deliberately-rough solution shape that needed a home, but none of the existing kinds could hold it. An epic explicitly forbids engineering bets and architectural shape (per [multi-prd-epic-shape](multi-prd-epic-shape.md): the umbrella coordinates children, it doesn't decide *how*). A PRD is committed work the team is doing and avoids dictating implementation. An ADR records a decision already made. So an exploratory proposal that genuinely wants to show its solution shape — before anyone has bet on building it — fell through the cracks, and the PRD had been quietly overloaded to play both the pre-bet and post-bet role at once.

## Alternatives

- **Introduce an "engineering bet" kind instead** — a technical-bet artifact capturing the *how*. Rejected: "engineering bet" is a coined term foreign to the brain's vocabulary, whereas "pitch" is native Shape Up; and a bet in Shape Up is the betting-table *commitment*, not the document. A pitch already carries solution shape, so a separate engineering-bet kind would overlap it.
- **Reuse the existing PRD** — keep shaping straight into a PRD. Rejected: it conflates pre-bet exploration with post-bet commitment (the overload this ADR removes), and the PRD and epic conventions discourage the exploratory solution-shaping a pitch needs.
- **Rename the brain's "PRD" to "pitch"** — declare the existing initiative artifact was a pitch all along. Rejected as most disruptive: it would re-label the entire existing `prds/` trail and muddy the clean pre/post-bet split this ADR draws.
- **Do nothing** — keep pitches ephemeral. Rejected: exploratory and architectural proposals would have nowhere to record their solution shape, forcing either a premature epic/PRD or losing the shaping work entirely.

## Consequences

- **Opens** a home for exploratory, pre-bet work that shows its solution shape — innovation-week explorations and architecture proposals in particular.
- A new shelf (`wiki/<scope>/pitches/`), a pitch template, a kinds-table entry, and a `/shape --pitch` mode are added; `pitches/` becomes a reserved shelf alongside `prds/`, `adrs/`, and `epics/`.
- **The PRD is reframed as strictly post-bet.** Existing PRDs are unaffected (they describe work already underway); the convention change is forward-looking. The pre/post-bet boundary is now explicit.
- **Graduation is the human gate.** A pitch proposing a direction is low-stakes; the consequential moment is the bet that turns it into an epic or PRD. Agent-authored pitches under operator supervision land in `pitches/` directly; graduation requires the operator's explicit bet.
- **Costs:** one more kind to learn and one more shelf to maintain; a mild risk of pitches accumulating un-bet (mitigated by grooming sweeps treating stale draft pitches like other stale drafts). The pitch-to-epic/PRD graduation path adds a supersede step to the lifecycle.
