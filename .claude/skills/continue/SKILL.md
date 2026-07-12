---
name: continue
description: Resume in-flight /shape work. Detect current phase by inspecting PRD/ADR state + open PRs; route to the right next action. Ingest fresh PR comments / new sources arrived since last run. Pre-push verifies pattern fit (AGENTS.md rule 5) and CI gates (rule 4) before code changes leave local. Always stops at /shape phase boundaries for human approval; flags pattern mismatches, unfamiliar feedback, or scope-creeping new sources before acting. Load when the user says "continue", "keep going on X", "what's next on X", "address PR comments on X", "ingest new feedback on X", or invokes `/continue <slug-or-PR#>`. Pairs with `/shape` (which starts new work) and `/in` (which ingests fresh sources unrelated to in-flight work).
---

# Continue — resume in-flight /shape work

You are working in `~/projects/brain`. This skill picks up
`/shape` work that's already underway — somewhere along the
Phase 1 → 1.5 → 2 → 3 → Build-notes path — and either advances
it to the next phase or ingests new context that arrived since
the last run.

## Local-first mode

If `.env` declares `LOCAL_FIRST=true`, phase detection reads from
**local commit history + working-tree state**, not `gh pr list` /
`gh pr view`. Commit messages on the current branch are the trail
— a commit titled "Phase 1 PRD: <slug>" means Phase 1 landed; the
next action is Phase 2.

The "ingest fresh PR comments / new sources" sub-step is a no-op
under local-first — there are no PR comments to ingest. New
sources still apply (the operator can drop a file under
`sources/` mid-flight); detect those via `git status` + `ls
sources/`.

Phase advancement still pauses for inline operator approval at
each boundary, per `/shape` skill's local-first preamble. No
remote push, no `gh pr` calls.

```bash
[ -f .env ] && grep -q '^LOCAL_FIRST=true$' .env && LOCAL_FIRST=1
```

The skill is a **router**, not a re-implementation of /shape's
phase protocols. It locates the in-flight work, decides what
the next action is, and either:

- **Hands off to `/shape`** (for "start the next phase" cases —
  e.g. PRD merged → start Phase 2 ADR authoring), or
- **Does its own work** (for "ingest feedback into in-flight
  Phase 3" cases — PR comments, new sources mid-build, Build
  notes after merge).

## Inputs

| Form                       | Meaning                                                                                                                |
|----------------------------|------------------------------------------------------------------------------------------------------------------------|
| `/continue <slug>`         | Continue work on the named `wiki/<repo>/{prds,adrs}/<slug>.md`. Locates artifacts by slug.                              |
| `/continue <PR#>`          | Continue work tied to a specific PR (brain or sibling-repo). The skill maps the PR back to a slug.                      |
| `/continue` (no args)      | List in-flight `/shape` work (any PRD with `status: draft` or `living` not yet `superseded`, plus their PR state) and ask which to continue. |

## Pre-flight

1. **Locate artifacts.** For the chosen slug:
   - PRD file at `wiki/<repo>/prds/<slug>.md` (if exists)
   - ADR file at `wiki/<repo>/adrs/<slug>.md` (if exists)
   - **Epic page at `wiki/<repo>/epics/<slug>.md`** (if exists — for `/shape --epic` work; the slug is the epic itself)
   - Most recent brain PR(s) for this slug — `gh pr list --search "<slug>" --state all`
   - Sibling-repo PR for this slug — search the brain log for the PR URL, or `gh pr list` in the sibling repo
   - Any Notion source linked from the PRD/ADR/epic `sources:` list (for change-detection)
   - **If the resolved PRD/ADR has `parent_epic: <slug>` set**, also locate the parent epic page and surface it as part of the state context (the epic provides umbrella narrative the user may want to revisit while continuing the child).

2. **Inspect state.** Determine which case applies (only one fires per invocation):

| State                                                              | Action                                                                                                |
|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Phase 1 PRD draft, brain PR not merged                             | **Stop and ask.** Phase 1 needs human approval before Phase 2 starts. Surface PR URL + CI status.    |
| Phase 1 PRD merged, no ADR file                                    | **Start Phase 2.** Hand off to `/shape`'s Phase 2 protocol with the PRD as input.                    |
| Phase 2 ADR draft, brain PR not merged                             | **Stop and ask.** Phase 2 needs human approval before Phase 3 starts.                                 |
| Phase 2 ADR merged, no Phase 3 sibling-repo PR yet                 | **Start Phase 3.** Hand off to `/shape`'s Phase 3 protocol.                                          |
| Phase 3 PR open, with new external context arrived                 | **Ingest the context** (PR comments / new source URL / new conversation snapshot); update code or ADR/PRD as needed; push update. *See § Ingesting feedback below.* |
| Phase 3 PR open, no new external context                           | **Re-run pattern-fit + local CI verify**; report state; ask user what to do next.                    |
| Phase 3 PR merged, ADR's `## Build notes` empty or missing          | **Author Build notes** per `/shape`'s Phase 3 finish protocol; open follow-up brain PR.              |
| **Target is an epic page** (`kind: epic`)                           | **Report epic state + child progress** (deterministic walk of `child_prds:` and `child_adrs:` reverse-edges with status-mapping). Ask which child to continue or whether to spawn a new child via regular `/shape`. If all children are `superseded`, suggest manual epic close (`status: superseded`) per the multi-prd-epic-shape ADR's manual-closing convention. |
| **Child slug with `parent_epic:` set, child progressed this phase** | After advancing the child (Phase 2 ADR merged → Phase 3 start; Phase 3 PR merged → Build notes), **update the parent epic's `## Children` section** to reflect the child's new status (status-mapping per zoom-out skill: `draft → in flight (PRD draft)`, `living → in flight (ADR shipped)`, `superseded → shipped`). One line edit; no new file. |

3. **Pre-work checks** per `AGENTS.md` § Working inside a sibling repo:
   - **Helper fan-out (parallel-first).** When pre-work has parallel shape — multiple state-source reads (PRD, ADR, sibling-repo PR comments, Notion source change-detection), multiple sibling-repo files to inspect for pattern-fit, multiple in-flight slugs to triage when no slug is given — default to fanning out helper subagents in a single message rather than serial tool calls. Per [`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md).
   - **Pattern fit (rule 5).** Whatever code change is about to happen, scan adjacent code for prior art on the shape being introduced. If the change appears to introduce a *parallel* pattern instead of *extending* an established one, **stop and ask** before proceeding. The cache-formatted-resume-text Build notes refinement is the worked example.
   - **Local CI verify (rule 4).** If the action involves pushing code, reproduce the relevant CI gate locally (per the sibling repo's `permanent/conventions.md` invocation) before pushing.
   - **Deepdive gap (when resuming a Phase-1 PRD or starting Phase 2).** If the resumed work is at the Phase-1 PRD or about to enter Phase 2, scan the PRD's `## Background` and `## Now / Perceived / Target` sections against the deepdive rule at [`wiki/brain/adrs/shape-deepdive-pre-flight.md`](../../../wiki/brain/adrs/shape-deepdive-pre-flight.md) (protocol at `.claude/skills/shape/SKILL.md` § Pre-flight step 4). If the PRD reads as a restated pitch — no cited sibling-repo paths, no prior ADRs, no constraints surfaced from code — **stop and ask** whether to fire the deepdive now (fetch the load-bearing context, append findings to `## Background`) before advancing. Same proportionality as in `/shape`: a small pitch warrants a small deepdive. The pace half of the discipline lives at [`wiki/brain/authoring-adrs-and-prds.md`](../../../wiki/brain/authoring-adrs-and-prds.md) § Pace and depth.
   - **Zoom-out (manual).** If the user asks to *"step back"*, *"zoom out"*, *"check the bigger picture"*, *"verify fit"*, or otherwise signals the makeup-mirror moment, invoke the `zoom-out` skill explicitly against the in-flight slug. `/continue`'s pre-push doesn't *auto-fire* zoom-out — manual invocation covers the pre-push case. If the brief surfaces a load-bearing concern, **stop and ask** rather than proceed.

## Stop-and-ask triggers

`/continue` is **aggressive about pausing** for human direction. Stop and ask whenever any of these fire:

- **New PR comment with substantive feedback** the agent isn't certain how to address. Surface the comment + a short proposed plan; wait for confirmation. Don't act.
- **New source URL or context drop** is offered (in conversation, in a PR comment, in a Notion page link), but the agent isn't sure if it's in scope. Surface the source + ask whether to ingest or set aside.
- **Pattern-fit scan shows a parallel pattern** would be introduced when an established one exists. Surface both shapes and ask which to take. Default lean: extend the established pattern (rule 5's "most of the time the answer is yes").
- **Local CI gate fails** after a code change. Don't push; surface the failure + a proposed fix; wait for confirmation.
- **Phase boundary reached** (Phase 1 → 2, Phase 2 → 3). Per `/shape`'s human-gate rule, the agent stops; the user approves; the next phase starts. CI green is necessary but not sufficient.
- **The in-flight work appears to need a fundamental re-pitch** (the PRD's framing is wrong, or the ADR's chosen bet has been invalidated by new evidence). Don't try to patch — surface the issue and ask whether to re-shape.

## Ingesting feedback into in-flight Phase 3

This is `/continue`'s most distinctive capability — none of the existing skills do this directly. The shape:

1. **Pull the new context.**
   - PR comments: `gh pr view <PR#> --comments` plus `gh api repos/<org>/<repo>/pulls/<PR#>/comments` for review-line comments.
   - Notion sources: the Notion MCP fetch (per `feedback_notion_mcp_canonical.md` memory).
   - Conversation/design-discussion drops the user pastes in: the user's message itself is the source.
   - Sibling-repo file references (a reviewer points at `app/foo.rb:42`): `Read` the cited region.

2. **Snapshot any new external source** to `sources/<repo>/...` (or `sources/notion/...`) per the additive-only rule. PR comment threads themselves don't get snapshotted — they live in GitHub. But any *new artifact* a comment references (a Notion page not previously cited, a JSON sample, a customer-facing screenshot) does.

3. **Decide the action together with the user.** Surface:
   - The feedback / new source.
   - The agent's proposed action.
   - The agent's uncertainty about whether the proposal is right.

   Example surface: *"A reviewer asked why we picked the formatter-side shape over the helper-method sketch. I propose to (a) add a one-paragraph clarification to the PR description pointing at the ADR's § Build notes entry, and (b) leave a single inline reply pointing at the same. Do you want that, or would you rather respond differently?"*

4. **Do the work.** Edit code (if the feedback warrants), edit ADR (if a clarifying Build-notes append is warranted), push, mark the PR comment thread resolved.

5. **Permanent record decisions.** When a PR-comment discussion surfaces a *deviation* from the ADR's plan, **append to the ADR's `## Build notes`** rather than burying it in PR comments. The PR thread is volatile (squash-merge often hides it; archived later); the Build notes are permanent and the next agent inheriting the area reads them.

## Done check

- [ ] The chosen action is the right one for the inspected state — not guessed; the routing table above produced exactly one match.
- [ ] Pattern-fit scan performed before any code change. Outcome recorded in PR body / Build notes if non-trivial.
- [ ] Local CI gate reproduced before any push. Output cited (e.g. `undercover ✅ No coverage is missing in latest changes`).
- [ ] User asked at every stop-and-ask trigger; nothing autonomous on commitment-class decisions.
- [ ] Brain artefacts updated where the discussion warrants permanent record (Build notes, PRD/ADR clarifications, new source snapshots).
- [ ] `log/log.md` line appended for the action taken:

  ```
  YYYY-MM-DD continue — <description> (<slug>)
  ```

  Examples:
  - `2026-05-06 continue — addressed PR comment on cache-formatted-resume-text Phase 3 (cache-formatted-resume-text)`
  - `2026-05-06 continue — ingested new Notion source mid-build (foo-feature)`
  - `2026-05-06 continue — handed off to /shape Phase 3 after PRD/ADR approval (bar-pattern)`

## What `/continue` is NOT

- **Not a re-shape.** `/continue` doesn't re-author the PRD or ADR. If the in-flight work needs a fundamental re-pitch, surface that and stop; the user invokes `/shape` (or accepts a `/shape --record` retroactive ADR).
- **Not `/in` for fresh sources.** `/in` is the front door for sources *unrelated* to in-flight work. `/continue` ingests sources only *in service of* advancing existing `/shape` work — the source must connect to a known slug.
- **Not `/review`.** `/continue` does not merge PRs. If the user wants a merge, that's `/review` (or direct `gh pr merge`).
- **Not autonomous past phase boundaries.** Per the existing `/shape` human-gate rule, `/continue` stops at every Phase 1→2 and Phase 2→3 boundary and waits for explicit user approval. Same rule, same gate.
