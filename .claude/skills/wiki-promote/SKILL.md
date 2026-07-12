---
name: wiki-promote
description: Graduate a `kind: insight` page into a `kind: initiative` — scaffold the new initiative page from the insight (carry over team/repos/sources, set supersedes), mark the insight superseded with superseded_by, then synthesise the initiative's What/How/Why from the insight's Pattern/Implications. Load when the user says "promote", "graduate this insight", "turn this insight into an initiative", or otherwise asks to commit to action on a feedback insight.
---

# Promote an insight into an initiative

You are working in `~/projects/brain`. When `/feedback` writes a
`kind: insight` page and a team commits to acting on it, the insight
graduates into a `kind: initiative`. This skill makes that transition
mechanical and auditable.

## When to run

- A PM/EM has reviewed an insight and decided to act.
- The insight has accumulated enough evidence (`confidence: medium` or
  better) that an initiative is justified.
- Multiple insights point at the same action and you want to roll them
  up.

## Inputs

- `/promote <insight-page>` — wiki-relative path to a `kind: insight`
  page (e.g. `application-form-friction.md`).
- `/promote <insight-page> --slug <name>` — override the initiative's
  slug.

## Protocol

### 1. Read the insight in full

Don't promote from the title alone. Read `## Pattern`, `## Evidence`,
`## Affected personas`, and especially `## Implications` — these are
the inputs that shape the initiative.

If `## Status` already says *acted-on* or *dismissed*, stop and ask
the user to confirm.

### 2. Run the mechanical scaffold

```bash
python tools/brain.py promote <insight-page>
```

This:

- creates `wiki/<slug>-initiative.md` (or `<slug>` if `--slug` was
  passed) from the initiative shape,
- carries `team` / `division` / `repos` / `sources` from the insight,
- sets `supersedes: <insight-page>` on the new initiative,
- sets `status: superseded` and `superseded_by: <new-page>` on the
  insight,
- leaves TODO markers in the initiative's What/How/Why/Now/Perceived/
  Target sections.

Don't skip this step in favour of hand-editing — the supersession
metadata is bookkeeping that's easy to forget.

### 3. Synthesise the initiative content

Open the new initiative page and replace each TODO using the insight
as the source:

- **What.** Derived from `## Pattern`. State the work concretely:
  *"reduce application-form drop-off on mobile"*, not *"address
  insight"*.
- **How.** From `## Implications`. Pull out the concrete sub-actions
  the insight surfaced. If implications were vague, this section may
  be brief — that's fine; the initiative will earn detail through
  later edits.
- **Why.** Cite specific evidence from the insight's `## Evidence`
  and the user-personas listed in `## Affected personas`. The Why
  should be defensible to a skeptic: *"X% of feedback from <persona>
  cited this; <persona2> hits it weekly."*
- **Now.** What's true today. If the initiative hasn't started, write
  the *baseline* — the current state of the affected surface, cited
  from sibling repos or other reference pages.
- **Perceived.** What the org currently believes. For a fresh
  promotion, this is often *"team unaware of the pattern's
  prevalence"* — that's the gap the insight just closed.
- **Target.** The desired end state. If it's not yet decided, mark
  *(needs decision)* and link a follow-up `kind: decision` page if one
  is in flight.

Bump `confidence:` from `low` (the scaffold default) to `medium` once
the synthesis cites real material from the insight.

### 4. Update the index

`wiki/index.md` gets a new entry under `## Initiatives`. The insight's
existing entry under `## Insights` should be visibly marked
*(superseded → <initiative>)* — don't delete it; it's still the
evidence record.

### 5. Cross-link affected personas

The insight already lists affected user personas. The initiative
inherits this through `supersedes` but should also reference the
personas directly in its `## Why` section so a reader doesn't have to
chase the chain.

### 6. Log

```
YYYY-MM-DD promote — <insight>.md → <initiative>.md
   personas: <comma-separated slugs>
   confidence: <new value>
```

### 7. Validate

```bash
python tools/brain.py validate
python tools/brain.py views
```

Validate must pass — the new initiative must have all six required
sections, even if some still have TODO content. (The required-sections
check is on heading presence, not on heading content; TODO is fine but
empty is not.)

## What promote is *not*

- **Not silent supersession.** The insight stays in the wiki; the
  evidence doesn't disappear. Future readers can see the chain.
- **Not the decision.** A team decides to act; this skill records that
  decision structurally. If the decision itself is contested, that's a
  `kind: decision` page that should exist *before* the promotion.
- **Not a one-way door.** If the initiative later turns out to be
  misguided, mark *it* superseded and re-open the insight. The history
  remains.

## Done check

- [ ] `python tools/brain.py promote` ran cleanly; both pages updated.
- [ ] All six initiative sections have synthesis content (no remaining
      TODO markers).
- [ ] The initiative's `## Why` cites the affected personas and at
      least one specific piece of evidence from the insight.
- [ ] `wiki/index.md` lists the new initiative and marks the insight
      as *(superseded → ...)*.
- [ ] `log/log.md` records the promotion.
- [ ] `python tools/brain.py validate` is clean.
