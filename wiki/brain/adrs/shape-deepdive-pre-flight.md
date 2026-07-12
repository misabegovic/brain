---
title: "Deepdive on load-bearing points lands as a /shape pre-flight step; pace lands on the binding authoring playbook; the top-level schema is not extended"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
summary: >
  Before Phase 1 of /shape, a deepdive pass reads the affected surfaces so the PRD is grounded in observed state rather than the pitch's assumptions.
sources:
  - ../../../AGENTS.md
  - .claude/skills/shape/SKILL.md
  - .claude/skills/continue/SKILL.md
---

# Deepdive on load-bearing points lands as a `/shape` pre-flight step; pace lands on the binding authoring playbook; the top-level schema is not extended

Brain-meta decision on where two operator-raised discipline rules live — *"always do a deepdive on important points when shaping, to fetch relevant context"* and *"slow down, no need to rush"* — treated as two facets of one discipline: deliberateness in `/shape` Phase 1 pre-flight.

The **deepdive rule** lands as a numbered step in the [/shape skill](../../../.claude/skills/shape/SKILL.md)'s pre-flight, between the slug-uniqueness check and the RFC-flag note. The step names the discipline: identify two to four load-bearing points in the pitch — the places where the decision pivots on constraints not yet known; for each point, fetch the constraining context (affected sibling-repo code, relevant permanent pages and prior ADRs/PRDs in scope, the target repo's git history when a prior decision is suspected, operator-memory rules, and external sources read verbatim rather than paraphrased); and surface the findings woven into the PRD's Background and Now/Perceived/Target sections, not in a separate notes block. The bound is proportional: a tiny shape change warrants a tiny deepdive (sometimes a single grep), a substantive change warrants reading several files — the discipline is deliberate context-fetching, not a fixed step count.

The **pace rule** lands as a one-paragraph *Pace and depth* subsection on the binding authoring-playbook page, next to its per-phase required-reading table. The paragraph names rushing as the failure mode behind shallow PRDs, missed alternatives, skipped pattern-fit checks, and context-free audit entries; frames "show me" / "demonstrate" / "do it all" operator signals as invitations to be deliberate, not deadlines; carries the same proportionality as the deepdive; and asks the agent to pause at phase boundaries to re-read what just shipped before starting the next phase. The top-level agent schema is **not** extended: skill files own protocol, the schema owns governance, and both rules are protocol. The [/continue skill](../../../.claude/skills/continue/SKILL.md)'s pre-work checks gain a one-sentence cross-reference, because `/continue` may resume a Phase-1 PRD authored without a real deepdive and surfacing that gap fits its existing stop-and-ask shape.

## Context

The Phase-1 PRD posed a single load-bearing question: where do the two rules live? Three possible landings were sketched — both rules in the shape skill, the hybrid chosen above, or both rules in the top-level schema as one brain-level discipline.

The brain has a settled convention about where rules live. Skill-specific protocol lands in skill files (the parallel-efforts protocol sits in the spawn skill per [parallel-efforts-on-request](parallel-efforts-on-request.md); the soft-promotion heuristic from [multi-prd-epic-shape](multi-prd-epic-shape.md) sits in the shape skill's pre-flight). The top-level schema owns governance and cross-skill conventions — collaboration rules, path conventions, the audit-log shape — not per-skill mechanics. The deepdive is mechanics, with the same shape as the existing soft-promotion check: a step the authoring agent runs before drafting, in the same skill, section, and phase — except it is judgement rather than heuristic, and it always fires with proportional depth.

The pace rule is broader than `/shape`: it applies to multi-phase shaping, parallel-effort cycles, sibling-repo build phases, and demonstration modes invoked outside `/shape` entirely. A skill-local landing would under-cover it; a schema landing would over-grow the schema for what is fundamentally an authoring-pace concern. The binding playbook page is already where authoring-pace concerns live (per-phase required reading, spec self-review rules), and its established hierarchy — it cross-references the schema, with conflicts resolving in the schema's favour — fits a binding *practice* that is not a governance rule.

Two further forces shaped the outcome. First, the deepdive already operated in fragments across the brain — the soft-promotion signal scan, prior ADRs whose context sections walked the schema infrastructure before committing, the playbook's static required-reading list — but was never named as one rule; the decision names it once and ties the fragments to it, codifying behaviour the brain already exhibits when it works well. Second, the agent's bounded context window is the load-bearing constraint on the deepdive's shape: an unbounded "read everything relevant" rule is unworkable, so the two-to-four-points, one-or-two-reads-per-point bound is preserved as the operative discipline. The PRD also flagged that judgement-shaped rules resist validator enforcement — a Background section can fabricate citations as easily as earn them — so the existing confidence floor and Phase-1 human-approval gate remain the backstop; CI enforcement would be performance theatre.

## Alternatives

- **Hybrid: deepdive in the shape skill, pace on the playbook, no schema change** *(chosen)* — the pace rule's broader reach is signalled by cross-references from the shape and continue skills to the playbook paragraph, not by colonising the schema or duplicating prose across skill files. The deepdive's shape-specificity is honoured by its skill-local landing.
- **Both rules in the shape skill.** The cleanest single landing spot and fewest hops. Rejected because pace is not shape-specific; a skill-local pace rule would either under-cover (other skills lack it) or over-cover (copy-pasted prose that drifts across files). The playbook is the one place authoring pace can land once and bind everything.
- **Both rules in the top-level schema, cross-referenced from pre-flight.** The broadest reach. Rejected because it grows the schema for per-skill mechanics, inverting the brain's consistent choice of skill-local landings when one is available; the extra cross-reference hop is one the agent already pays for comparable rules, and consistency keeps the schema lean.
- **A standalone deepdive command.** Rejected because the deepdive's bound — load-bearing points *in the pitch* — is only meaningful inside `/shape`; a freestanding command either has no bound or invents an artificial one. The deepdive is a step inside Phase 1, not alongside it. The same logic eliminated a standalone pace command: pace is an authoring posture, not a command.
- **Do nothing — leave both as operator-memory entries.** Rejected because rules governing observable agent behaviour belong in skills a fresh session loads automatically, not in private memory the next session won't read. Doing nothing also leaves the existing fragments un-named as one rule, costing every future agent the pattern recognition the rule encodes.

## Consequences

- **Closes** the shallow-Background failure mode (a background section that merely restates the pitch): the pre-flight step is an explicit prompt to fetch constraining context before drafting, and the weave-into-prose convention lets the reviewer see whether the deepdive happened.
- **Closes** the class of failure where Phase 1 sketches a parallel pattern that the build phase's pattern-fit check later has to reverse: the deepdive surfaces the established pattern up front, before the ADR locks in a sketch.
- **Closes** cross-session amnesia on both rules: they bind every agent run through the skill files and the playbook rather than living in one operator's memory.
- **Opens** a default citation posture for PRDs (a Background that cites sibling-repo paths or prior decisions becomes the norm) and a place for `/continue` to flag a deepdive gap on resumed work before advancing.
- **Costs** bounded judgement overhead in pre-flight — a single grep on a small pitch, several file reads on a substantive one — accepted as the iteration-cost-compression trade.
- **Costs** the validator no enforcement teeth, by design: the discipline is review-enforced (confidence floor plus the Phase-1 human gate), since a validator cannot tell a real deepdive from a fabricated one.
- **Does not commit** the brain to a structured-findings object, a load-bearing-point classifier, a time floor on shaping, a deepdive cache, or extensions to later phases, whose disciplines are already covered elsewhere.
