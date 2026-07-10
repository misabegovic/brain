---
title: "zoom-out is a skill called as a step inside /shape and /continue, with conversation-first output and opt-in persistence as an aside-rendered Big-picture fit section"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../../../AGENTS.md
  - .claude/skills/zoom-out/SKILL.md
  - .claude/skills/shape/SKILL.md
---

# zoom-out is a skill called as a step inside `/shape` and `/continue`, with conversation-first output and opt-in persistence as an aside-rendered `## Big-picture fit` section

## Context

The motivating failure mode is the makeup mirror: deep focus on a piece of
work produces internally coherent output that misses the bigger product and
architectural picture. The brain holds the data but does not synthesise a
per-work-item brief at the right moments. An RFC pass surfaced four
load-bearing constraints. First, the brief is a *skill* — agent-actuated,
conversation-output, always fresh — and any persisted section is its
captured output; the UI renders, it never generates, so there is one source
of truth and no parallel pipeline. Second, day-one auto-fire is deliberately
conservative: only at the `/shape` Phase 1 → 2 and Phase 2 → 3 boundaries,
with `/continue`'s pre-push moment covered by manual invocation. Third, the
synthesis is load-bearing: a brief that merely lists parents, siblings, and
log entries is the *data*; the brief is the *paragraph of synthesis* — the
tension named, the bigger picture surfaced — and weak synthesis defeats the
whole tool. Fourth, the persisted section needs visual prominence so
non-technical readers can find and consume it without parsing raw markdown.

The design extends patterns the brain already has. Skill-as-router and
skill-invoked-as-step-of-another-skill are both established shapes, so one
canonical skill with two invocation paths (manual `/zoom-out <target>` and
a named step inside `/shape` and `/continue`) introduces no new pattern.
The UI substrate ships built-in aside directives with visually distinct
rendering (see [`successor-ssg-for-ui`](./successor-ssg-for-ui.md)), so
day-one persistence needs no dedicated component. The generated pages
index already carries reverse edges from file paths to owning wiki pages,
so a path-to-owning-pages lookup is a query plus matching, inline in the
skill protocol with no new subcommand. The operations log is a flat
append-only ledger, so recent-activity context is a cheap filtered scan.
Overlap reports are consumed when they exist; when none exists for the
current work, the brief names that gap and suggests the overlap skill as a
follow-up rather than auto-running the analysis on every brief.

The committed shape. One canonical skill at
[`.claude/skills/zoom-out/SKILL.md`](../../../.claude/skills/zoom-out/SKILL.md)
accepting a slug, page path, file path, or PR reference. Auto-fire happens
only at the two `/shape` phase boundaries, governed by a rule-based skip
heuristic that errs toward firing (skip only when the appetite is small,
the page has no reverse edges, and recent log lines mention no adjacent
slug) — false positives are recoverable; false negatives defeat the fix.
The brief has two halves: a *technical zoom-out* that is deterministic and
lookup-based (hierarchy and cross-cutting edges from the pages index plus
overlap reports, recent activity from the log filtered to the current and
adjacent slugs), and a *product zoom-out* that is a single LLM-synthesised
paragraph answering how this work fits, impacts, or augments the product
offering and what tension or alignment exists with adjacent work, grounded
in the target repo's state and purpose pages and any relevant insight
pages. The grounding rule is hard: every product-narrative claim cites the
brain page it came from as an inline link; ungrounded claims are omitted or
the gap is named explicitly. Conversation is the default output with no
persistence; an explicit user instruction ("save it", "persist to the
PRD") triggers appending a `## Big-picture fit` section to the relevant
PRD or ADR, wrapped at write time in the substrate's note-aside directive
so it renders prominently with no UI-side changes. The synthesis prompt
stays tight (roughly 800 input and 200 output tokens) to keep a typical
brief under about five seconds. If the synthesis quality disappoints in
practice, the fallback is the split-skill alternative below with the
synthesis factored into a focused sub-skill.

## Alternatives

- **A (chosen) — single skill, called as a step inside `/shape` and
  `/continue`.** One canonical skill, two invocation paths, conservative
  auto-fire, conversation default, opt-in persist, aside rendering.
  Extends two established shapes without introducing a parallel pattern,
  adds no directories or infrastructure. The cost is the day-one
  limitation that the operator must remember manual invocation at
  `/continue`'s pre-push moments; a follow-up decision can widen the
  auto-fire set without restructuring the skill.
- **B — split skills (manual plus auto-fire) over a shared synthesis
  backend.** Separates the concerns cleanly but yields three skill files
  with duplicated protocols; manual versus auto-fire is a calling pattern,
  not a different kind of operation. Rejected — the duplication is not
  earned.
- **C — view-first: a generated wiki page regenerated per request.**
  Always discoverable by browsing, but the failure mode is
  moment-of-attention-driven, not browsing-driven; a brief found by
  browsing arrives too late, and a regenerated-on-demand artefact goes
  stale the moment adjacent state moves. Also fits poorly with file-path
  targets. Rejected on timing and freshness grounds.
- **D — checklist-only, no synthesis.** Trivial to ship, but a checklist
  is the data, not the brief; asking the user to do the lookups during
  deep focus is exactly what the brain exists to avoid. Rejected — it
  inverts the value proposition.
- **Do nothing.** The failure mode persists by construction in the absence
  of an active mechanism, and non-technical readers keep lacking a
  consumable "does this fit our product story?" surface. Rejected.

## Consequences

- *Closes:* the makeup-mirror blind spot at `/shape`'s phase boundaries —
  the brief surfaces whether or not the operator remembers to ask, and the
  operator explicitly opts in or out of persisting it before
  commitment-class decisions lock in.
- *Closes:* the cross-disciplinary readability gap when briefs persist —
  the aside is visually distinct and the product half is grounded prose a
  non-technical reader can scan.
- *Opens:* whether `/continue`'s pre-push moment needs auto-fire too, and
  whether any auto-fire moment warrants auto-persistence; day one says no
  to both, reassessed after roughly four weeks of use.
- *Costs:* one new skill and command file, a note-aside formatting
  convention enforced at write time, and edits to two skills and two
  governance files. No infrastructure.
- *Costs:* per-fire latency proportional to synthesis time, controlled by
  the tight prompt envelope.
- *Costs:* the synthesis prompt lives in the skill file, so iterating on
  it changes the skill; because weak synthesis is the failure mode that
  defeats the tool, non-trivial prompt changes warrant their own follow-up
  decision record.
- *Costs:* the day-one aside rendering may prove insufficiently prominent;
  the follow-up is a dedicated UI component introduced organically when
  reader feedback warrants it, deliberately not in scope here.

## Build notes

The build implemented the committed shape with no deviations. Auto-fire
landed as dedicated subsections at the end of the `/shape` Phase 1 and
Phase 2 protocols rather than inline-numbered sub-steps, keeping the
branch logic in one block; `/continue` gained a manual-invocation bullet
in its pre-work checks, with its auto-fire deliberately deferred. No
tooling subcommand was added — the path-to-owning-pages helper is inline
in the skill protocol against the pages index. Persistence wraps captured
output in the note-aside directive titled "Big-picture fit"; the dedicated
component follow-up remains unblocked but deferred. The skip heuristic
landed verbatim, applying to auto-fire only — manual invocation always
fires.
