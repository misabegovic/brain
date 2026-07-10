---
name: zoom-out
description: Produce a per-work-item zoom-out brief that surfaces big-picture fit during deep focus. Two halves — a deterministic technical zoom-out (hierarchy from `pages.json`, cross-cutting from `affects:` + `_overlaps/`, recent activity from `log/log.md`) and an LLM-synthesised single-paragraph product zoom-out grounded in `state.md` § Now/Target + `permanent/purpose.md` + feature inventories + applicable `wiki/insights/`. Conversation-first output; opt-in persistence as a `## Big-picture fit` section on the relevant PRD/ADR (wrapped in a Starlight `:::note` aside for visual prominence in the brain UI). Load when the user says "zoom out", "big picture", "how does X fit", "step back", "where does this sit", or invokes `/zoom-out <slug-or-page-or-path-or-PR#>`. Auto-fired at `/shape` Phase 1 → 2 and Phase 2 → 3 boundaries; manual elsewhere (including `/continue`'s pre-push). Pairs with `/shape` (start new), `/continue` (resume in-flight), `/ask` (factual lookup).
---

# Zoom-out — surface big-picture fit during deep focus

You are working in `~/projects/brain`. This skill produces a
**zoom-out brief** that places a piece of work in its bigger
product + architectural picture. The brief addresses the
*makeup-mirror failure mode* named in
[`wiki/brain/adrs/zoom-out-on-current-work.md`](../../../wiki/brain/adrs/zoom-out-on-current-work.md):
deep focus on a small surface produces internally-coherent work
that turns out to miss the bigger picture; the brief zooms out
*for* the user (and the agent) at the right moments.

The skill is invoked two ways:

- **Manually** by the user: `/zoom-out <slug-or-page-or-path-or-PR#>`.
- **As a step** inside `/shape` (auto-fired at Phase 1 → 2 and
  Phase 2 → 3 boundaries) and as an explicit affordance inside
  `/continue` (manual reference; auto-fire inside `/continue` is
  deferred to v2).

The decision shape and load-bearing constraints live in the ADR
at
[`wiki/brain/adrs/zoom-out-on-current-work.md`](../../../wiki/brain/adrs/zoom-out-on-current-work.md);
this skill is the implementation of that decision.

## Inputs

| Form                                         | Meaning                                                                                                                                |
|----------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `/zoom-out <slug>`                           | Brief on `wiki/<repo>/{prds,adrs}/<slug>.md` (the canonical case during `/shape` work).                                                |
| `/zoom-out <wiki-relative-path>`             | Brief on any wiki page (`wiki/<repo>/permanent/architecture/foo.md`, `wiki/org/methodology/way-of-working.md`, `wiki/brain/state.md`, etc.).        |
| `/zoom-out <sibling-repo-relative-path>`     | Brief on a sibling-repo file or directory (`~/projects/<repo>/app/models/user.rb`). Used during Phase 3 builds + `/continue`. |
| `/zoom-out <PR#>`                            | Brief on the in-flight work tied to a PR (brain or sibling-repo). Maps PR → slug → wiki pages.                                         |
| `/zoom-out` (no args)                        | List the last 5 active work items from `log/log.md` and ask which to zoom out on.                                                      |
| Step-invoked from `/shape`                   | Phase 1 → 2 boundary: the just-written PRD slug. Phase 2 → 3 boundary: the just-written ADR slug.                                      |
| Step-invoked from `/continue` (deferred v2)  | *Not on day one.* The user runs `/zoom-out` manually before pushing if they want pre-push verification.                                |

## Skip heuristic (auto-fire only)

When invoked as an auto-fire step from `/shape`, the skill
skips emitting a brief if **all** of the following are true:

- The target page's `appetite:` frontmatter is `small`, AND
- The target page has no `affects:` reverse edges in
  `pages.json`, AND
- `log/log.md`'s last 50 lines mention no adjacent slug.

Otherwise the brief fires. Manual invocation always fires
(no skip). When skipped, the skill emits a single line —
*"zoom-out: skipped (no cross-cutting concerns flagged)"* —
and appends a log entry so the skip is auditable.

The skip rule errors-on-the-side-of-firing. False positives
(unnecessary briefs) are recoverable noise; false negatives
(missing the makeup-mirror moment) defeat the tool's
purpose.

## Protocol

### 1. Resolve the target

Map the input form to a concrete target shape:

- **slug** → `wiki/<repo>/{prds,adrs,epics}/<slug>.md` (PRD takes precedence if both exist; epic page if neither prds/ nor adrs/ slug matches).
- **wiki path** → the page directly.
- **sibling-repo path** → use the *path → owning wiki pages* lookup (step 2.5 below).
- **PR#** → `gh pr view <PR#> --json title,body,headRefName,files` and search the PR body / branch name for a brain slug, or fall back to mapping `files[].path` via the path → owning wiki pages lookup.
- **(no args)** → read `log/log.md` last 50 lines; surface the top 5 active work items (by frequency of mention); ask user which.

**Target-kind branch.** Read the resolved target's frontmatter `kind:` field. Three cases drive the brief shape (per [`wiki/brain/adrs/multi-prd-epic-shape.md`](../../../wiki/brain/adrs/multi-prd-epic-shape.md) § Decision):

- **`kind: epic`** → the **epic-targeted four-section brief shape** in step 4 (umbrella narrative + children + cross-cutting + product zoom-out). The technical halves are deterministic structural lookups; only the umbrella-narrative + product zoom-out halves consume LLM tokens.
- **`kind: initiative` or `kind: decision` with `parent_epic: <slug>` set** → the **regular two-half brief shape** PLUS an `## Umbrella narrative (parent epic)` section between the two halves, sourced as a verbatim ≤200-token excerpt of the parent epic's Objective + Background first paragraph. No additional LLM call (the excerpt is verbatim).
- **All other kinds (or PRD/ADR with no `parent_epic:`)** → the **regular two-half brief shape** unchanged.

### 2. Load deterministic data (technical zoom-out)

Read the brain data sources by hand — no shell-out, no new
tooling:

- **Hierarchy.** From `wiki/_views/pages.json`: the target's
  `kind`, parent topic (deduce from path, e.g.
  `wiki/<repo>/permanent/architecture/ai-features.md`
  → parent area is `<repo>/permanent/architecture/`),
  and sibling pages under the same area. Plus any ADRs/PRDs
  in the same `<repo>` whose slug stem matches the target's
  area.
- **Cross-cutting.** The target page's `affects:` and
  `affected_by:` reverse edges from `pages.json`. Plus any
  `wiki/_overlaps/<...>.md` reports that mention the
  target's slug or area in their `## Items` section.
- **Recent activity.** `log/log.md` — read the last 50
  lines, filter for entries mentioning the target's slug,
  adjacent slugs (sibling pages above), and any path strings
  in the target's `sources:` list.

### 2.5. Path → owning wiki pages helper (sibling-repo path inputs)

When the target is a sibling-repo path, find the wiki pages
that own / describe it:

- Read `wiki/_views/pages.json`.
- Iterate pages; match the target path against each page's
  `sources:` list (substring match on `~/projects/<repo>/<path>`)
  and `affects:` list (repo-name match).
- Top 1-3 matching pages by specificity become the target's
  hierarchy anchor. If no page matches, the brief emits a
  single line — *"zoom-out: no wiki page owns this path; brain
  has a coverage gap here. Suggest `/in` to ingest, or
  `/ask coverage: <repo>` to find the right shelf."* — and
  stops.

### 3. Load product-narrative sources (product zoom-out)

For the LLM-synthesis half, gather these grounding sources:

- The target repo's `wiki/<repo>/state.md` § Now and § Target
  (the relevant excerpt — by area name match, not the whole
  page).
- The target repo's `wiki/<repo>/permanent/purpose.md` (full).
- The relevant subset of the target repo's feature inventory
  (e.g.
  `wiki/<repo>/permanent/architecture/ai-features.md`,
  filtered to the rows whose names match the target's area).
- Applicable `wiki/insights/` pages: pages whose `affects:`
  includes the target repo. (`wiki/insights/` is the
  customer-feedback-derived pattern shelf.)

If a source doesn't exist or doesn't carry relevant content
for this target, omit it. Don't fail the brief.

### 4. Construct the two-half synthesis

Emit the brief in the conversation as Markdown. The exact
section shape depends on the target-kind branch from step 1.

**Regular two-half shape** (default — for `kind: initiative`,
`kind: decision`, or any non-epic page):

```markdown
# Zoom-out brief — `<slug-or-target-name>`

## Technical zoom-out

- **Hierarchy:** parent area is `<area>`; sibling pages: `<list>`
- **Cross-cutting:** affects `<X, Y>` (per `affects:`); affected by `<Z>` (per `affected_by:`); overlaps in `<_overlaps/...>` (when present)
- **Recent activity:** last activity in this area: `<excerpt of recent log lines>`

## Product zoom-out

<one paragraph of natural-language synthesis grounding every claim with an inline markdown link to the cited brain page>
```

**Two-half shape with parent-epic insertion** (when target
has `parent_epic: <slug>`):

```markdown
# Zoom-out brief — `<slug-or-target-name>`

## Technical zoom-out

- **Hierarchy:** parent epic is [`<epic-slug>`](<link>) (`<epic-title>`); parent area is `<area>`; sibling pages: `<list>`
- **Cross-cutting:** ...
- **Recent activity:** ...

## Umbrella narrative (parent epic)

<verbatim ≤200-token excerpt of the parent epic's Objective + Background first paragraph>

## Product zoom-out

<one paragraph as above, but with explicit context that this is a child of the named epic>
```

**Epic-targeted four-section shape** (when target has
`kind: epic`):

```markdown
# Zoom-out brief — `<epic-slug>`

## Umbrella narrative

<single LLM-synthesised paragraph from the epic's Objective + Background, ≤ 150 output tokens, grounded in cited brain pages>

## Children (N total: M shipped, K in flight, X pending)

- **PRDs:**
  - [<title>](<link>) — *<status-mapping>*
  - ...
- **ADRs:**
  - [<title>](<link>) — *<status-mapping>*
  - ...

## Cross-cutting

- **Affects (deduped across children):** `<repo-list>`
- **Recent activity in this umbrella's area:** `<excerpt>`

## Product zoom-out

<one paragraph synthesising how the umbrella fits the product offering, grounded in cited brain pages>
```

**Status-mapping for the children list** (deterministic, no
LLM):
- `draft` → *"in flight (PRD draft)"*
- `living` → *"in flight (ADR shipped, build pending)"*
- `superseded` → *"shipped"*
- `archived` → *"rejected/abandoned"*

The `## Children` section pulls children from the epic's
`pages.json` entry's `child_prds` and `child_adrs` reverse-
edges. Statuses come from each child's frontmatter `status:`
field via the mapping above. **No LLM call** for this section
— it's pure structural lookup.

**The product-zoom-out paragraph is the load-bearing half.**
It synthesises *how does this work fit / impact / augment the
product offering, and what tension or alignment do I see
between this and adjacent work?* — answered as a *single
paragraph*, not a list of bullet points.

**Grounding rules** (non-negotiable):

- Every product-narrative claim cites the brain page it came
  from, as an inline markdown link.
- No hallucinated product features. If the cited sources
  don't ground a claim, the synthesis omits the claim.
- If sources are missing for an area the brief should cover,
  *name the gap explicitly*: *"the brain doesn't carry a
  product-narrative source for X — flag for `/in` follow-up."*
  Don't paper over the gap with generic prose.
- If the technical-zoom-out half surfaces a tension with
  adjacent work (e.g. the target overlaps with a slug
  shipped last week, or contradicts a recent ADR), call it
  out *first* in the product-narrative paragraph. Tension
  is the load-bearing signal of the makeup-mirror failure
  mode being caught.

**Prompt-budget envelope** (per the ADR's latency budget):

- Total source-excerpt input tokens: ≤ 800.
- Synthesis output tokens: ≤ 200.
- Rationale: keeps brief generation under the 5-second
  target latency for typical wiki-page targets; avoids
  prompt-cache-window misses for repeated invocations in a
  session.

### 5. Render and stop

Print the brief in the conversation. *Do not* persist by
default. The brief is conversation-first; the user opts in
to persistence via step 6.

### 6. Opt-in persistence (only on explicit user instruction)

If the user follows up with *"save it"*, *"persist to PRD"*,
*"add to the ADR"*, *"capture this on the PRD"* (or any
unambiguous variant), append or update a `## Big-picture
fit` section on the relevant PRD/ADR. The persisted shape
wraps the brief's content in a Starlight `:::note` aside for
visual prominence on the brain UI:

```markdown
## Big-picture fit

:::note[Big-picture fit]

**Technical zoom-out:** parent area is `<area>`; sibling pages: `<list>`. Affects `<X, Y>`; affected by `<Z>`. <Optional: overlaps / recent activity excerpt.>

**Product zoom-out:** <the paragraph from the brief, with its inline citations preserved>

*Brief generated by `/zoom-out` on YYYY-MM-DD.*
:::
```

If the section already exists from a previous run, **update**
it (don't append a second one). The aside's title is
*"Big-picture fit"*.

If the persistence target is ambiguous (e.g. the target was
a sibling-repo path that maps to multiple wiki pages),
surface the candidate pages and ask the user which to
persist on.

### 7. Log

Append a single line to `log/log.md`:

```
YYYY-MM-DD zoom-out — <target> [persisted]
```

The `[persisted]` tag is added only when step 6 fired.

## Auto-fire integration with `/shape`

`/shape`'s Phase 1 protocol (after the PRD frontmatter is
written and the phase-1 log line is appended) gains a
sub-step that calls this skill against the just-written
PRD slug. Same shape at Phase 2 (after the ADR is written).
The skip heuristic above applies.

The auto-fire happens *before* the human-approval gate at
the phase boundary — it's information *for* the human's
decision to approve, not after. If the brief surfaces a
load-bearing concern, the agent surfaces it alongside the
PR URL and waits.

## What `/zoom-out` is NOT

- **Not a re-author.** The skill produces the brief as a
  read-side synthesis; it doesn't edit the target page's
  body (only optionally appends/updates `## Big-picture
  fit`).
- **Not `/ask`.** `/ask` is factual lookup. `/zoom-out` is
  *synthesis* — it answers a different question (*"how does
  this fit?"*, not *"what is this?"*).
- **Not `/overlap`.** `/overlap` produces a structured
  duplicate / collision report between two named pages.
  `/zoom-out` consumes overlap reports when they exist but
  doesn't generate them. If the brief surfaces a candidate
  overlap that's not yet in `_overlaps/`, it suggests
  running `/overlap` as a follow-up.
- **Not auto-persistent.** Day-one persistence requires
  explicit user instruction. Auto-persistence on
  significant auto-fire moments is a future-amendment open
  question, not a v1 capability.

## Done check

- [ ] Brief rendered in conversation with both halves
      clearly labelled.
- [ ] Product-zoom-out paragraph cites every claim back to a
      brain page (no ungrounded claims).
- [ ] Where sources are missing, the gap is named explicitly
      (not papered over).
- [ ] Tension with adjacent work, if any, surfaces *first* in
      the product paragraph.
- [ ] If persisted: `## Big-picture fit` section exists on
      the target PRD/ADR, wrapped in `:::note[Big-picture
      fit]` aside, with a generation timestamp.
- [ ] `log/log.md` line appended (with `[persisted]` if
      step 6 fired, with `[skipped: <reason>]` if the skip
      heuristic fired).
- [ ] Latency budget respected (typical wiki-page brief
      under 5 seconds end-to-end).
