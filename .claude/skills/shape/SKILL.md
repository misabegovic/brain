---
name: shape
description: The universal authoring path for ADRs and PRDs. Two modes — forward (pitch → PRD → ADR → build) and record-existing (decision encoded in code → ADR only). Sources can be inline pitches, Notion URLs, or sibling-repo observations. Produces `wiki/<repo>/prds/<slug>.md` and `wiki/<repo>/adrs/<slug>.md` (slug-only, no numeric prefix — see AGENTS.md § ADR / PRD filenames). Load when the user says "shape", "pitch", "PRD", "ADR", "let's build X", "record decision", "capture this choice", or invokes `/shape <repo> ...`. **`/shape` is the only skill that writes to `prds/` or `adrs/`** — `/in` hands off here when it spots pitches or pre-existing decisions.
---

# Shape — universal ADR/PRD authoring path

You are working in `~/projects/brain`. This skill is the **only**
path that writes to `wiki/<repo>/adrs/` or `wiki/<repo>/prds/`.
Every ADR and every PRD in the brain comes through here — whether
the source is a fresh pitch, a Notion RFC, or a decision the code
already encodes.

The skill loads agent personas (`.claude/personas/agents/`) and
wears the right hats per phase.

## Local-first mode

If `.env` declares `LOCAL_FIRST=true`, **phase boundaries collapse
to local commits** per AGENTS.md § Local-first mode:

- **Phase 1 (PRD)** — author the PRD, run local validations
  (`brain.py validate` / `check --no-net` / `views`), commit on the
  current branch with the same commit message shape `/pr` would
  have used. **Don't open a PR.** Surface the diff to the operator
  and pause briefly for inline approval before Phase 2.
- **Phase 2 (ADR)** — same shape: author, validate, commit, surface,
  pause for inline approval.
- **Phase 3 (build)** — sibling-repo work still happens in the
  sibling repo, but no draft PR opens automatically; commits land
  on the current branch in that repo. The operator decides when to
  push.

The artefact-shape rules (paths under `<scope>/{adrs,prds}/` vs.
`<scope>/ai-suggestions/`, banner + frontmatter for AI-suggestions,
no-code-blocks, etc.) are unchanged — they're properties of the
artefact, not the ritual. The human-gate-per-phase rule still
applies; it just moves from PR-approval to inline conversational
approval.

```bash
[ -f .env ] && grep -q '^LOCAL_FIRST=true$' .env && LOCAL_FIRST=1
```

## Decision policy — manual by default, `--auto` opts in to autonomous

`/shape` is **manual by default**: the agent pauses at every
load-bearing decision and lets the user pick. The agent's job is
to *surface options + tradeoffs*, not to decide for the user.
Phase boundaries pause for approval (the existing rule); under
the manual default, **in-phase decisions also pause**.

The pauses cover:

- **Slug selection** — propose 1–3 candidate slugs with one-line
  rationales; let the user pick or supply their own. Don't pick
  silently.
- **Appetite** (Phase 1) — propose `small` / `medium` / `big` with
  the trade-off; let the user confirm before the PRD is written.
- **Persona selection** (Phase 1) — list the candidate personas
  from `.claude/personas/users/` matching the pitch; let the user
  confirm which persona owns the user need.
- **No-gos + rabbit holes** (Phase 1) — propose them; let the user
  accept / amend / add.
- **Decomposition** (Phase 1, `--epic` mode) — propose the
  anticipated children; let the user shape the list.
- **Alternatives + bet** (Phase 2) — generate at least three
  options + "do nothing" with trade-offs; **do not pick the bet**.
  The user picks the bet; the Tech Lead then writes the ADR
  reflecting that choice.
- **Pattern-fit divergence** (Phase 2 + Phase 3) — when the
  codebase has an established pattern but the work has a reason
  to diverge, surface both options and the reason; let the user
  decide whether to extend or go parallel. Default-extension is
  still the recommendation per `AGENTS.md` § Working inside a
  sibling repo rule 5; the pause is for the *deliberate
  divergence* case.
- **Soft-promotion to `--epic`** (already a pause per pre-flight
  step 7) — unchanged.
- **Epic-detection `parent_epic:` prompt** (already a pause per
  pre-flight step 6) — unchanged.

The pauses are *conversational*, not blocking PRs. In LOCAL_FIRST
mode they're inline messages; in PR mode they happen *before* the
PR opens (the agent doesn't draft the PR until the user has
picked).

**Override: `--auto`.** When invoked as `/shape <scope> <pitch>
--auto` (combinable with any other mode flag — `--epic`,
`--record`, `--from-notion`, `--rfc`), the agent runs
autonomously through every in-phase decision, picking the option
it would recommend and recording the choice + reasoning visibly
so the user can course-correct. Phase boundaries **still pause**
for approval — `--auto` only disables in-phase pauses, not
phase-end gates. `--auto` also unlocks parallel execution: the
agent can fan out helper subagents (parallel-first per the
`parallel-execution-agent-teams` ADR) for the deepdive, the
Phase 2 alternatives generation, and any other parallel-shape
work under the same flag.

**Default tilt.** When in doubt about whether a decision is
load-bearing enough to pause for, **pause**. The cost of an
extra one-line confirmation is far smaller than the cost of an
ADR/PRD that locks in the wrong bet because the agent guessed
silently. Per the user's 2026-05-08 direction.

## Modes

| Mode                | Trigger                                                        | Phases                                              | Output                                                         |
|---------------------|----------------------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------|
| **Pitch** (pre-bet) | `/shape <scope> --pitch <inline-pitch>` <br> `/shape <scope> --pitch --from-notion <url>` | PM → pitch page (Phase 1 only — a pitch is pre-bet; no ADR pair). May sketch solution/architecture at fat-marker fidelity. | `wiki/<scope>/pitches/<slug>.md` only |
| **Forward** (default) | `/shape <repo> <inline-pitch>` <br> `/shape <repo> --from-notion <url>` | PM → PRD → Tech Lead → ADR → (optional) Developer → code | `wiki/<repo>/prds/<slug>.md` + `wiki/<repo>/adrs/<slug>.md` |
| **Record-existing** | `/shape <repo> --record <description>` <br> `/shape <repo> --record --from-notion <url>` <br> `/shape <repo> --record --from-source <repo-path>` <br> Or invoked by `wiki-ingest` when it spots a pre-existing decision while ingesting | Tech Lead only (PM phase skipped — there's nothing to *shape* about a decision the code already encodes) | `wiki/<repo>/adrs/<slug>.md` only |
| **Epic** | `/shape <scope> --epic <pitch>` <br> `/shape <scope> --epic --from-notion <url>` | PM → epic page (Phase 1 only — umbrellas have no Phase 2 ADR pair; decisions live in children) | `wiki/<scope>/epics/<slug>.md` only |

Pitch mode is *pre-bet*: shape a proposal into a `kind: pitch` page
that frames the problem, sets an appetite, and may sketch the
solution (including architecture) at fat-marker fidelity — the one
artifact allowed to do so. A pitch is upstream of everything; on a
bet it graduates → an epic+children or a PRD+ADR (mark the pitch
`superseded`, set `superseded_by:`). Phase 1 only, no ADR pair.
Use the `tools/templates/pitch.md` template. See
[`wiki/brain/adrs/shape-up-pitches.md`](../../../wiki/brain/adrs/shape-up-pitches.md).
Forward mode is *future*: shape a (bet-on) pitch into work to do.
Record-existing mode is *past*: capture a decision the code already
encodes, with alternatives and consequences synthesised post-hoc.
Epic mode is *umbrella*: shape multi-PRD/multi-ADR work that needs
a coordinating narrative; produces a single `kind: epic` page (no
ADR pair — see [`wiki/brain/adrs/multi-prd-epic-shape.md`](../../../wiki/brain/adrs/multi-prd-epic-shape.md)
§ Decision for why).

Forward + record-existing feed the same `adrs/` shelf — the trail
mixes forward bets and historical decisions on equal footing.
Epic feeds the new `<scope>/epics/` shelf; children of an epic
spawn via regular forward mode and carry `parent_epic:`
frontmatter linking back to the umbrella.

## Inputs

| Form                                                             | Mode                          | What it means                                                                       |
|------------------------------------------------------------------|-------------------------------|--------------------------------------------------------------------------------------|
| `/shape <repo> <inline pitch text>`                              | Forward                       | A new pitch from the user.                                                           |
| `/shape <repo> --from-notion <url>`                              | Forward                       | A Notion pitch / RFC describing forward work.                                        |
| `/shape <repo>` (no pitch)                                       | Forward                       | Pick the most-recently flagged pitch from `wiki/<repo>/state.md` § Target, or ask.   |
| `/shape <repo> --record <description>`                           | Record-existing               | Capture a decision the code already encodes (operator-supplied description).         |
| `/shape <repo> --record --from-notion <url>`                     | Record-existing               | Notion contains a past decision / ADR; record it in the brain's trail.               |
| `/shape <repo> --record --from-source <repo-relative-path>`      | Record-existing               | Decision is encoded in the sibling-repo source itself (e.g. a package.json choice). Read the source and synthesise the ADR. |
| `/shape <scope> --epic <inline pitch text>`                      | Epic                          | A new umbrella-scale pitch that should produce a `kind: epic` page (no ADR pair).    |
| `/shape <scope> --epic --from-notion <url>`                      | Epic                          | Notion-sourced umbrella-scale pitch.                                                 |
| (invoked by `wiki-ingest` when it spots a pitch or decision)     | Forward or Record-existing    | `wiki-ingest` hands off; the input description includes which mode applies.          |
| `/shape` (no args)                                               | —                             | List active repos and ask which one + which mode.                                    |

The `--auto` flag (combinable with any mode above) flips the
in-phase decision policy from manual-default to autonomous —
see § Decision policy. Phase-end approval gates always apply
regardless.

## Pre-flight

1. Confirm the target scope is in active scope.
2. Choose a slug — kebab-case, ≤ 6 words. The slug **is** the
   filename: `wiki/<scope>/prds/<slug>.md` for forward (and the
   matching ADR uses the same slug); `wiki/<scope>/epics/<slug>.md`
   for `--epic` mode. No numeric prefix — see
   AGENTS.md § ADR / PRD filenames are slug-only.
   **Manual default (per § Decision policy):** propose 1–3
   candidate slugs with one-line rationales and let the user
   pick or supply their own. Under `--auto`, pick the
   highest-ranked candidate and record the choice visibly.
3. Verify the slug doesn't collide with an existing file in `prds/`,
   `adrs/`, or `epics/` for that scope. If it does, refine the slug
   (don't add a suffix counter — slugs should describe the content).
   **Also check open PRs across the brain repo**:
   `gh pr list --state open --search "<slug>" --json number,headRefName,title`.
   A PR whose head ref matches `agent/<slug>-*` or whose title /
   body names this slug is a parallel-effort collision (per
   [`wiki/brain/adrs/parallel-efforts-on-request.md`](../../../wiki/brain/adrs/parallel-efforts-on-request.md)
   § Decision: slug uniqueness now spans open PRs, not just the
   local filesystem). Re-slug — the agent picks the new slug per
   `feedback_slug_delegation.md`, no need to ask the user.
4. **Deepdive on load-bearing points.** Before drafting the PRD,
   identify the 2–4 load-bearing points in the pitch — the places
   where the decision pivots on constraints not yet known. For
   each point, fetch the constraining context: read the affected
   sibling-repo code, walk relevant `wiki/<scope>/permanent/`
   pages and prior ADRs/PRDs in scope, scan the target repo's git
   history (`git log -p --grep`) when a prior decision is
   suspected, search operator-memory rules under
   `~/.claude/projects/-home-muhamed-projects/memory/` for slug-
   relevant feedback, and read any external sources verbatim
   rather than paraphrased. **Helper fan-out (parallel-first).**
   When the deepdive has parallel shape — multiple files to read,
   multiple subtasks to evaluate, multiple targets to inspect —
   default to fanning out helper subagents in a single message
   rather than serial tool calls. Per
   [`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md). The bound is proportional: a tiny
   shape change warrants a tiny deepdive (sometimes a single
   grep), a substantive shape change warrants reading several
   files. Surface the findings *woven into* the PRD's
   `## Background` and `## Now / Perceived / Target` sections —
   not in a separate "deepdive notes" block — so the Tech Lead
   reading the PRD sees *why* certain alternatives are pre-empted
   by the discovered constraints, in the same prose that explains
   the bet. The discipline is deliberate context-fetching, not a
   fixed step count; the existing fragments — the soft-promotion
   check's three-signal scan in step 6 below, the
   [`multi-prd-epic-shape`](../../../wiki/brain/adrs/multi-prd-epic-shape.md)
   ADR's investigation paragraph that walked schema infrastructure
   before committing, the binding playbook's static required
   reading at Phase 0 — are instances of the same rule. The pace
   half of this discipline lives at
   [`wiki/brain/authoring-adrs-and-prds.md`](../../../wiki/brain/authoring-adrs-and-prds.md)
   § Pace and depth; *"show me / demonstrate / do it all"* user
   signals are invitations to be deliberate, not deadlines. Per
   [`wiki/brain/adrs/shape-deepdive-pre-flight.md`](../../../wiki/brain/adrs/shape-deepdive-pre-flight.md).
5. Note the `--rfc` flag if present. It inserts an RFC pass between
   Phase 1 (PRD) and Phase 2 (ADR) — see § Phase 1.5.
6. **Epic-detection on regular forward mode** (skip for `--epic`,
   `--record`, `--from-source`). Query `wiki/_views/pages.json` for
   `kind: epic` pages in the target scope. If any exist, surface a
   one-line prompt:

   *"Existing epics in `<scope>`: `<epic-slug-1>` (`<title-1>`),
   `<epic-slug-2>` (`<title-2>`). Is this pitch part of one?
   (`<slug>` / `no`)"*

   User picks a slug or types `no`/proceeds. **Default: decline**.
   If picked, the new child PRD will carry `parent_epic: <slug>`
   in its frontmatter (Phase 1's write step handles this).
   Per [`wiki/brain/adrs/multi-prd-epic-shape.md`](../../../wiki/brain/adrs/multi-prd-epic-shape.md)
   § Decision: one line, no wizard, default = decline.

7. **Soft-promotion suggestion** (regular forward mode only). Check
   three signals on the pitch text + frontmatter intent:
   - **All-three-must-fire (Muhamed's *quiet-on-day-one* ask)**:
     (a) appetite reads as `big`; (b) pitch mentions multiple
     subsystems (LLM judgment); (c) ≥ 3 distinct named personas
     are implied. If **all three** fire, surface:

     *"This pitch reads as umbrella-scale (appetite=big AND
     multiple subsystems AND ≥3 personas). Want `--epic` instead?
     (yes / no)"*

     Default = `no`. If user accepts, restart Phase 1 with
     `--epic` mode; if no, proceed as a regular PRD with no
     further nagging.

   The asymmetric default (decline) reflects the
   cache-formatted-resume-text learning: false positives are
   expensive (the agent's suggestions become noise the user
   dismisses); under-suggestion is recoverable; over-suggestion
   isn't.

## Phase 1 — PM agent (pitch → PRD) — *forward mode only*

**Skip this phase entirely in record-existing mode.** A decision
the code already encodes doesn't have a *pitch* to shape; jump
straight to phase 2 with the input description as the ADR's seed.

Load `.claude/personas/agents/pm-agent.md` and follow its protocol:

1. Frame the pitch in one sentence.
2. Identify the affected `users/` personas. At least one named
   persona must own the user need.
3. Set the appetite (small / medium / big).
4. Sketch the solution at PRD fidelity.
5. List no-gos and rabbit holes.
6. State the decision the Tech Lead agent is being asked to make.

**Manual default (per § Decision policy):** before writing the
PRD, surface the framing, persona choice, appetite, and proposed
no-gos / rabbit holes to the user as a short structured summary
and let the user confirm or amend. Don't write the PRD file
until the user has signed off. Under `--auto`, write the PRD
directly with each choice + reasoning recorded visibly in the
agent's narration; the user can still course-correct after.

Write `wiki/<repo>/prds/<slug>.md` from
`tools/templates/prd.md`. Frontmatter:

```yaml
kind: initiative
status: draft
confidence: low      # PM-authored content starts low
appetite: <small|medium|big>
team: <as inferred from repo or pitch>
repos: [<target>]
```

Update `wiki/<repo>/index.md` to list the PRD under a `## PRDs`
section. Append to `log/log.md`:

```
YYYY-MM-DD shape — pitch → wiki/<repo>/prds/<slug>.md (PM agent)
```

If the PM agent decides the pitch should be rejected (no clear user
persona, duplicates an existing PRD, appetite-vs-need mismatch),
write a one-paragraph rejection note in the log line and stop. Don't
create a PRD just to satisfy the workflow.

### Child-spawn maintenance — `parent_epic:` children

If pre-flight step 5 (epic-detection) set `parent_epic: <slug>`
on this PRD, **two extra write steps** at PRD-write-time per
[`wiki/brain/adrs/multi-prd-epic-shape.md`](../../../wiki/brain/adrs/multi-prd-epic-shape.md)
§ Decision:

1. **Set `parent_epic: <slug>`** in the new PRD's frontmatter
   (alongside `kind: initiative`, `status: draft`, etc.).
2. **Prepend a Starlight aside** to the PRD body, immediately
   after the H1 title, capturing a snapshot of the parent
   epic's title and one-line Objective excerpt:

   ```markdown
   :::note[Part of <epic-title>]
   This work is a child of [`<epic-slug>`](../epics/<epic-slug>.md).
   Umbrella objective: <one-line excerpt of parent epic's Objective>.
   :::
   ```

   The excerpt is captured at spawn-time (snapshot, not live
   sync). If the parent epic's title or Objective changes later,
   this aside drifts — that's a v2 sync concern.
3. **Append to the parent epic's `## Children` section** a new
   line in the format:

   ```markdown
   - [<new PRD title>](../prds/<slug>.md) — *draft*
   ```

   The status is the new PRD's frontmatter `status:` value
   ("draft" at this Phase). At Phase 2 (ADR shipped) this line
   updates to *living*; at Phase 3 (build merged) to
   *superseded*. The agent maintains this status during
   `/continue` runs as the child progresses.

### Auto-fire `/zoom-out` at the Phase 1 → 2 boundary

After the PRD is written and the log line appended (and before
opening the Phase 1 PR's human-approval gate), invoke the
`zoom-out` skill against the just-written PRD slug. Surface the
brief in conversation alongside the PR URL so the human reviewer
sees both at the same moment. Per the ADR at
[`wiki/brain/adrs/zoom-out-on-current-work.md`](../../../wiki/brain/adrs/zoom-out-on-current-work.md),
this catches the makeup-mirror failure mode at exactly the
commitment-class moment when locking in the PRD's bet might miss
the bigger picture.

The skip heuristic from the zoom-out skill applies: if all of —
appetite is `small`, no `affects:` reverse edges, no adjacent
slug mentions in the last 50 log lines — then the brief is
skipped (single line + log entry; no surfaced brief). Otherwise
the brief fires. Skipped-or-fired is captured in
`log/log.md` either way.

If the brief surfaces a load-bearing concern (a tension with
adjacent work, a missed cross-cutting effect), name it in the
PR-surfacing message: *"Phase 1 PR open; CI green; **zoom-out
flagged X — please consider before merging**"*. Don't try to
patch the PRD in response — let the human decide whether to
amend, merge as-is, or hold.

Skip the auto-fire if the PM agent rejected the pitch (no PRD
written → nothing to zoom out on).

## Phase 1.5 — RFC pass — *opt-in via `--rfc`, forward mode only*

When `--rfc` is set in forward mode, run the `rfc` skill against
the just-written PRD before the Tech Lead phase begins. The pool
is inferred from the PRD's frontmatter (`team:`, `repos:`,
`affects:`, `## Affected personas`); each persona reacts in a
one-paragraph voice; reactions land in a new `## RFC` section on
the PRD.

The Tech Lead agent in Phase 2 then reads PRD *plus* RFC reactions,
and the resulting ADR's `## Alternatives` should explicitly
reference RFC concerns where relevant ("the backend persona's concern about
N+1 queries maps to Option B above").

Skip in record-existing mode — there's nothing to RFC about a
decision the code already encodes.

If the inferred pool is empty (very small / brain-meta page),
`/shape --rfc` falls back to running with PM + Tech Lead + the
page's own audience heuristic; see the `rfc` skill for the rule.

Append to `log/log.md`:

```
YYYY-MM-DD shape — rfc pass: wiki/<repo>/prds/<slug>.md (<N> personas)
```

## Phase 1 — `--epic` mode (umbrella authoring) — *epic mode only*

When the invocation is `/shape <scope> --epic <pitch>` (or the
soft-promotion suggestion was accepted), Phase 1 produces a
single `kind: epic` umbrella page at
`wiki/<scope>/epics/<slug>.md`. **There is no Phase 2 ADR pair**
for the umbrella per
[`wiki/brain/adrs/multi-prd-epic-shape.md`](../../../wiki/brain/adrs/multi-prd-epic-shape.md)
§ Decision: the umbrella has no single bet to make; decisions
live in children. Phase 1.5 (RFC) applies if `--rfc` is set;
Phase 2 + Phase 3 are skipped for this `/shape` invocation.

Load `.claude/personas/agents/pm-agent.md` and follow its
protocol, with the umbrella-specific framing:

1. Frame the umbrella in one sentence — the *initiative*, not
   a single piece of work.
2. Identify the affected personas (umbrella-level, often
   broader than any single child's).
3. Set the umbrella scope (the work the umbrella encompasses)
   and explicit no-gos.
4. Sketch the *decomposition* — the children you anticipate
   spawning under this umbrella. The list is not load-bearing
   (children don't have to all be enumerated up front); it's a
   shape signal.
5. List rabbit holes + success metrics for the umbrella as a
   whole.

Write `wiki/<scope>/epics/<slug>.md` from
`tools/templates/epic.md`. Frontmatter:

```yaml
kind: epic
status: draft
confidence: low      # PM-authored content starts low
team: <as inferred from pitch>
repos: [<scope>]
```

Required sections (validator-enforced — see
`tools/brain.py` `REQUIRED_SECTIONS_BY_KIND["epic"]`):
`Objective`, `Background`, `Affected personas`, `Scope`,
`No-gos`, `Children`, `Success metrics`. The `## Children`
section is empty at Phase 1 — populated as children spawn
via regular forward `/shape` invocations with
`parent_epic: <slug>`.

Update `wiki/<scope>/index.md` to list the epic under a
`## Epics` section (create the section if it doesn't exist;
the section's existence is a signal that this scope has
umbrella-scale work). Append to `log/log.md`:

```
YYYY-MM-DD shape — pitch → wiki/<scope>/epics/<slug>.md (PM agent, --epic)
```

The Phase 1 → 2 zoom-out auto-fire still applies (the brief
fires against the just-written epic page; the brief shape is
the epic-targeted four-section variant per
`.claude/skills/zoom-out/SKILL.md`'s target-kind branch).

After human approval of the epic's Phase 1 PR, **children may
spawn**. Each child uses regular forward `/shape <scope>
<child-pitch>`, with the pre-flight epic-detection question
surfacing this newly-created epic as a candidate parent.

If the PM agent decides the umbrella should be rejected
(too small for an umbrella, no clear coordination concern,
duplicates an existing epic), write a one-paragraph
rejection note in the log line and stop.

## Phase 2 — Tech Lead agent (→ ADR)

Load `.claude/personas/agents/tech-lead-agent.md`. The input
depends on the mode:

- **Forward mode**: input is the PRD authored in phase 1. The bet
  is *forward* — what to build.
- **Record-existing mode**: input is the description of the
  pre-existing decision (from `--record <text>`, `--from-notion
  <url>`, or `--from-source <repo-path>`). The bet has already
  been made — the ADR captures *why* it was made and what
  alternatives were rejected, post-hoc.

Steps:

1. Read the input in full (PRD, Notion source, or sibling-repo
   source).
2. Read the sibling repo's existing patterns at
   `~/projects/<repo>/`. Per `AGENTS.md` § Working inside a
   sibling repo rule 5, the Tech Lead's load-bearing job here is
   *pattern fit*: how does the codebase already solve similar
   shapes? Is there an established sibling-method family,
   class hierarchy, helper convention, service layer,
   `Maintenance::` shape, ViewComponent style, or configuration
   mechanism this work would naturally extend? **Recommend
   extension over parallel** unless adjacent code shows a real
   reason the existing pattern doesn't fit.
3. Generate at least two alternatives + "do nothing."
   - Forward mode: alternatives are options for the proposed work.
   - Record-existing mode: alternatives are the options that *were*
     considered (or could have been) when the decision got made.
   The default-extension framing from step 2 should be the
   first alternative; reasons to *not* extend (parallel-pattern
   warranted) sit as the contrasting alternatives.
4. Apply team-persona lenses (backend / platform / architect / autonomous-agent).
5. Pick (or document the existing) bet.
   **Manual default (per § Decision policy):** in forward mode,
   surface the alternatives + persona reactions + the agent's
   recommended bet to the user and **wait for the user to pick**
   before writing the ADR. The user's choice is the bet recorded
   in `## What`; the agent's recommendation becomes one of the
   `## Alternatives`. Under `--auto`, pick the recommended bet
   and record the reasoning visibly. Record-existing mode is
   unaffected — the bet is already encoded in the code, the ADR
   is just capturing it.
6. Write the ADR. If a parallel pattern was deliberately chosen,
   record *why* in `## Alternatives` so phase 3 doesn't second-
   guess the call (and so the cache-formatted-resume-text
   build-notes refinement doesn't repeat — that ADR sketched a
   parallel `Candidate`-side helper pair when the codebase
   already had a sibling formatter family; the build chose the
   sibling, the ADR was retroactively updated).

Write `wiki/<repo>/adrs/<slug>.md` from
`tools/templates/adr.md`. **Forward mode** reuses the same `<slug>`
as the PRD so the pair is easy to find at a glance. **Record-
existing mode** picks its own slug (no PRD to align with).

Frontmatter:

```yaml
kind: decision
status: living                       # record-existing → living from the start
                                     # forward → draft until built, then living
confidence: medium                   # ADR-authored, with cited evidence
team: <inherited or inferred>
repos: [<target>]
sources:
  - wiki/<repo>/prds/<slug>.md       # forward only
  - <Notion URL if --from-notion>
  - <sibling-repo paths read during analysis>
```

**Forward mode**: after writing the ADR, update the PRD:

- Bump `confidence: low` → `medium`.
- Bump `status: draft` → `living`.
- Add a `## Decision` section at the bottom pointing to the new ADR.

**Record-existing mode**: no PRD to update. The ADR stands alone.

Update `wiki/<repo>/index.md` to list the ADR under `## ADRs`.
Append to `log/log.md`:

```
# Forward mode:
YYYY-MM-DD shape — wiki/<repo>/prds/<slug>.md → wiki/<repo>/adrs/<slug>.md (Tech Lead agent)

# Record-existing mode:
YYYY-MM-DD shape --record — <description> → wiki/<repo>/adrs/<slug>.md (Tech Lead agent)
```

If the Tech Lead agent rejects the PRD (appetite is wrong, the
problem is better solved by an existing ADR / decision page), write
the rejection as the ADR's `## What` ("don't build this; here's
why") and stop before phase 3. The PRD stays as record but doesn't
move to `living`.

### Child-spawn maintenance — `parent_epic:` ADRs

If the corresponding PRD has `parent_epic: <slug>` set, the new
ADR inherits the same `parent_epic:` value (single string, same
scope). Same Starlight aside auto-prepended at ADR-write-time as
on the PRD. **Update the parent epic's `## Children` section** —
the line for this child's PRD bumps from *draft* to *living*
(the PRD's status moved this phase per the bump above), and
optionally a sibling line for the ADR is added if separate
visibility is wanted (default: one line per child slug, since
PRD + ADR share a slug). Per the multi-prd-epic-shape ADR's
status-mapping convention.

### Auto-fire `/zoom-out` at the Phase 2 → 3 boundary

After the ADR is written, the PRD's confidence + status are
bumped, and the log line is appended (and before opening the
Phase 2 PR's human-approval gate), invoke the `zoom-out` skill
against the just-written ADR slug. Surface the brief in
conversation alongside the PR URL so the human reviewer sees
both at the same moment.

This is the zoom-out moment where the *implementation shape*
chosen by the Tech Lead is checked against the bigger picture
*before* Phase 3 build starts — the most expensive moment to
miss the makeup-mirror failure mode, because Phase 3 produces
code that's harder to reverse than artefacts.

Skip heuristic and concern-surfacing rules are the same as
the Phase 1 → 2 boundary. Skip the auto-fire if the Tech Lead
rejected the PRD (no ADR written or ADR is itself a rejection
note → nothing to zoom out on for forward work; record-existing
mode is also skipped, since there's no Phase 3 to gate).

## Phase 3 — Developer agent (ADR → code) — *forward mode only*

**Record-existing mode skips this phase entirely** — the code
already encodes the decision; there's nothing for the Developer
agent to build.



Load `.claude/personas/agents/developer-agent.md`. This phase's
output is *code in the sibling repo*, not new wiki content. Per
`AGENTS.md` § Working inside a sibling repo, all five rules
apply throughout phase 3 — surfacing the load-bearing two for
phase-3 work:

1. Read the PRD + ADR pair in full.
2. Walk the sibling repo's conventions (its `AGENTS.md` /
   `README.md`, plus the brain's
   `wiki/<repo>/permanent/conventions.md`).
3. **Pattern-fit pre-work (rule 5).** Before planning the
   change, scan the file the work touches and its neighbourhood
   for prior art on the shape being introduced. Does the codebase
   already solve this category of problem with an established
   pattern (a sibling formatter method, an established job-class
   family, a component base class, a configuration mechanism,
   etc.)? If yes, extend it. If no,
   pause and surface the divergence to the user before
   proceeding — a parallel pattern is a load-bearing decision
   that needs explicit justification (recorded in the ADR's
   `## Build notes` or the PR body).
4. Plan the change as small commits within the appetite.
5. Implement.
6. **Reproduce CI gates locally before pushing (rule 4).** Run
   the per-repo gate invocation captured in
   `wiki/<repo>/permanent/conventions.md` (e.g. a scoped test +
   coverage run against the changed files).
   Branch coverage is the load-bearing signal — a fixture that
   only exercises the *present* side of every `if foo.present?`
   isn't enough; the *absent* side needs a fixture too. Tests +
   lint of course also run; lint failures + spec failures gate
   the push the same way they always did.
7. **Open a SHORT draft PR with brain backlinks in the
   description.** Three non-negotiable rules:
   - **Draft.** `gh pr create --draft` — never ready-for-review
     on initial open, even when CI is green. The human marks it
     ready themselves.
   - **Backlinks.** PR body links to the canonical
     `wiki/<repo>/prds/<slug>.md` and
     `wiki/<repo>/adrs/<slug>.md` GitHub paths, and the Notion
     source URL when applicable.
   - **Body is an executive summary, not a section-heavy
     long-form.** Under 200 words. Lead with one sentence
     naming the change; one short context paragraph linking
     the brain PRD/ADR + Notion source in prose; restricted
     mention of CI / test plan only if it isn't covered by
     CI itself. **Do NOT scaffold the body with H2 sections**
     (`## Why`, `## What`, `## Affects`, `## Sources`,
     `## Phase-3 gate`, `## Backlinks`, `## Smoke test`,
     `## Test plan`, `## Verification`). Same rule as the
     `/pr` skill's § PR body shape — applies identically to
     sibling-repo Phase-3 PRs and to brain-side PRs. The user
     flagged the section-heavy shape as breaking convention
     2026-05-07. Use a `> [!IMPORTANT]` callout for rollout
     if there is one. Long AI-generated bodies make review
     harder; trim to the context that isn't in the diff.

After the sibling-repo PR merges:

- In the brain, append `## Build notes` to the ADR with any
  deviations from the plan.
- Bump the PRD's `status` if the work is fully shipped (`living` →
  `superseded`, with a forward-link note).
- **If the PRD has `parent_epic: <slug>`**, update the parent
  epic's `## Children` section: bump this child's status from
  *living* to *superseded* (per the multi-prd-epic-shape ADR's
  status-mapping convention).
- Append to `log/log.md`:

  ```
  YYYY-MM-DD shape — built wiki/<repo>/prds/<slug>.md @ <sibling-PR-url> (Developer agent)
  ```

This phase is optional in autonomous runs. The PM + Tech Lead phases
produce the artifacts; the human (or a follow-up agent run) can
trigger phase 3.

## Cross-phase rules

- **One PR per phase, ideally.** Phase 1 (PRD), Phase 2 (ADR + PRD
  graduation), Phase 3 (sibling-repo code + brain build notes).
  Smaller PRs let CI catch issues per phase.
- **Each phase boundary is a human gate.** Per `AGENTS.md`
  § Governance > `/shape` PRs are human-gated at every phase, the
  agent **stops at the end of every phase** and waits for explicit
  human approval before either merging the phase's PR or starting
  the next phase. After phase 1: open the PRD PR, surface the URL,
  wait. **Do not author the ADR** until the human has explicitly
  approved the PRD (a GitHub review with state `APPROVED`, or an
  unambiguous go-ahead in the conversation). Phase 1's approval is
  permission to merge the PRD PR *and* permission to start phase 2;
  phase 2 needs its own approval at the end before the ADR PR is
  merged. CI green is necessary but not sufficient — the
  `commitment-class` nature of ADR/PRD output requires human
  sign-off at each step. This applies regardless of how `/shape`
  was invoked (user-initiated or chained from `wiki-ingest`).
- **Confidence floor.** Per `AGENTS.md` § Governance, agent-authored
  content cannot self-promote to `confidence: high` in the same PR.
  PM writes at `low`; Tech Lead bumps to `medium` in their PR;
  graduation to `high` waits for shipped evidence + human approval.
- **Notion is read-only.** If the pitch came from a Notion page, the
  brain reads it but never writes back. Any update to Notion (status
  changes, etc.) is the human's responsibility.
- **Stay in active scope.** `/shape` only operates on the
  active-scope repos declared in `brain.config.yml` (mirrored in
  `AGENTS.md` § Active scope). Plus the org and brain meta-scopes. If a
  pitch belongs to an archived or out-of-scope repo, surface
  that and stop.

## Done check

- [ ] `wiki/<repo>/prds/<slug>.md` exists with all six initiative
      sections + Appetite / No-gos / Rabbit holes / Affected personas
      / Decision needed.
- [ ] `wiki/<repo>/adrs/<slug>.md` exists with all five decision
      sections + Linked PRD.
- [ ] `wiki/<repo>/index.md` lists both under `## PRDs` and `## ADRs`.
- [ ] PRD's confidence is `medium` and status is `living` once Tech
      Lead phase completes.
- [ ] `log/log.md` has phase-1 and phase-2 lines (and phase-3 when
      build is done).
- [ ] `wiki/index.md` § Open initiatives updated when a PRD lands
      (Phase 1); § Recent decisions updated when an ADR lands
      (Phase 2). Per
      [`wiki/brain/adrs/home-content-shape.md`](../../../wiki/brain/adrs/home-content-shape.md):
      every wiki/ edit must be paired with a wiki/index.md edit.
- [ ] `python tools/brain.py validate` is clean.
- [ ] **Phase 1 + Phase 2 — `/zoom-out` auto-fired at the
      respective boundaries.** Brief either rendered or skip-
      heuristic-skipped; outcome logged. If load-bearing concerns
      surfaced, named explicitly alongside the PR URL.
- [ ] **Phase 3 only — pattern-fit pre-work performed.** Either
      the chosen shape extends an established pattern in the
      sibling repo, or the parallel-pattern justification is
      recorded in the ADR's `## Build notes` / the PR body. Per
      `AGENTS.md` § Working inside a sibling repo rule 5.
- [ ] **Phase 3 only — CI gates reproduced locally before push.**
      Per-repo gate invocation from
      `wiki/<repo>/permanent/conventions.md` reports clean. Per
      rule 4.
