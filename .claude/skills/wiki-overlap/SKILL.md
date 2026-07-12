---
name: wiki-overlap
description: Find cross-team / cross-repo / within-repo overlaps in the brain — for a given topic (or all live initiatives), use mempalace search to surface candidate related material, run LLM-as-judge over candidate pairs, and write findings to wiki/_overlaps/<slug>.md so two teams independently building the same thing become visible. Load when the user says "overlap", "find duplicates", "what else are we doing like X", "are any teams stepping on each other", or otherwise asks for cross-team / cross-repo overlap analysis.
---

# Find overlaps in the brain

You are working in `~/projects/brain`. Goal #2 of the brain (per
`AGENTS.md`) is to make cross-team / cross-repo / within-repo overlaps
*visible* — when two teams independently build the same abstraction or
work on adjacent problems, the brain should surface that, not hide it.
This skill is the operation that does it.

This is a protocol-level skill: the agent (you) is the LLM-as-judge. The
mechanical primitive is `mempalace search`. There is no Python pipeline
yet — when the corpus grows beyond what's tractable to run pair-wise by
hand, that's the signal to build one.

## When to run

- The user asks "what else are we doing like X?" or "are any teams
  stepping on each other?"
- After a batch of `/ingest` operations, to see what new material
  overlaps with existing pages.
- As periodic hygiene (the user runs `/overlap` with no arg to scan all
  live initiatives).

## Inputs

- **Targeted:** `/overlap <topic>` — the topic is a wiki page slug, a
  concept, or a free-text phrase ("rate limiting", "candidate scoring").
- **Untargeted:** `/overlap` — sweep all `kind: initiative` pages
  (`status: living` or `draft`) and look for clusters.

## Protocol

### 1. Build the candidate set

For a targeted run:

- Read the named wiki page (or, if the topic isn't a page, identify the
  pages most plausibly related from `wiki/index.md`).
- Extract 3–5 key phrases that characterize the topic (concrete enough
  to retrieve well, e.g. *"rate-limit Redis bucket"* not *"rate
  limiting"*).

For an untargeted run:

- Walk `wiki/index.md`, take every page with `kind: initiative`.
- For each page, extract 2–3 key phrases from `## What` and `## How`.

### 2. Search mempalace per phrase

For each phrase:

```bash
mempalace search "<phrase>"
```

Read the top hits (default ~10). Note which wing / file each hit comes
from. Drawer-match scores below ~0.30 are usually noise; above ~0.45
deserve a closer look.

Aggregate hits across phrases per *source location* (e.g. a specific
file in `~/projects/<repo>`, or a specific Notion export). A source
appearing under multiple phrases is a stronger candidate than one
appearing under a single phrase.

### 3. Promote candidates to pairs

A *pair* is `(target, candidate)` where target is the input topic / page
and candidate is one of the aggregated source locations. Take the top
~5–10 pairs by aggregate signal.

For each pair, read both items in full. Don't judge from the snippet
alone — the snippet is only the trigger.

### 4. LLM-as-judge

For each pair, decide one of:

- **Same problem, same solution.** Two teams / parts of a team are
  building the same thing. *This is the case that most demands
  alignment.*
- **Same problem, different solution.** Adjacent work; coordination
  needed; compare approaches.
- **Different problem, same vocabulary.** False positive; record so
  future runs don't re-flag.
- **Adjacent / dependent.** One depends on or constrains the other; not
  a duplicate but worth surfacing.
- **Unrelated.** Drop.

For each non-dropped pair, write a one-paragraph rationale citing the
specific passages from each side.

### 5. Write the overlap page

For each cluster of pairs that share a target (or that the pairs
collectively cluster around), write:

`wiki/_overlaps/<slug>.md`

```yaml
---
title: Overlap — <short description>
kind: overlap
status: living
updated: YYYY-MM-DD
confidence: high | medium | low
teams:
  - <team A>
  - <team B>
repos:
  - <repo>
sources:
  - <pair 1 location>
  - <pair 2 location>
---
```

Required sections:

```markdown
## Items
A bulleted list of every item in the cluster, with full source paths and
a one-line gloss.

## Overlap
What's actually shared. Be concrete: which abstraction, which user
story, which constraint. If "Same problem, same solution," say what the
duplication is and what each side currently does.

## Recommendation
What to do about it. Options: pick one to canonicalize, merge, escalate
to a decision page (then create one with `kind: decision`), or just
flag for awareness. The brain doesn't decide — it surfaces.
```

If a cluster turns out to be a false positive on closer reading, *do
not* write the page. Mention the dismissed candidate in the log instead
so a future run can de-prioritize it.

### 6. Update `wiki/index.md`

Add a `## Overlaps` section if not present, and one line per overlap
page:

```
- [Overlap — <short description>](_overlaps/<slug>.md) — <one-line hook>
```

### 7. Cross-link from the affected pages

On each wiki page implicated in a written overlap, add a one-line
"Related work" reference back to the overlap page. This is what makes
overlaps actually surface during normal browsing.

### 8. Append `log/log.md`

```
YYYY-MM-DD overlap — <topic or "sweep"> → <overlap pages written>
   dismissed: <count> false positives [optional, with brief notes]
```

## What overlap is *not*

- Not a lint pass. Lint catches mechanical and contradiction issues
  inside the wiki; overlap detects that two distinct concepts are
  secretly the same one across the corpus.
- Not authoritative. The agent's judgement here is heuristic. Surface,
  don't decide.
- Not deduplication. We don't merge or delete pages on overlap detection
  — we write a third page that describes the overlap and let humans /
  future decisions resolve it.

## Done check

- [ ] Each candidate pair was read in full on both sides before judging.
- [ ] Every written overlap page has all three sections (Items / Overlap
      / Recommendation).
- [ ] `wiki/index.md` lists the new overlap page(s).
- [ ] Affected source pages got a "Related work" cross-link.
- [ ] `log/log.md` records the run, including dismissed false positives.
