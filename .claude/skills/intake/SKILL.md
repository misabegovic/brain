---
name: intake
description: Single entry point for everything that *adds* to the brain. Auto-routes the input to the right underlying skill (wiki-ingest, palace-mine, feedback-ingest, or shape) based on what the user passed. Load when the user says "in", "ingest", "intake", "add this", "pull in", "absorb", "mine", "feedback", "pitch", "record this decision", or invokes `/in`.
---

# Intake — single entry for adding to the brain

**Single source of truth.** The natural-language → slash-command
mapping lives in `AGENTS.md` § Intent → command mapping. This skill
operates one level lower: once `/in` is the chosen command, this
skill picks the right *sub-skill* (wiki-ingest / palace-mine /
feedback-ingest / shape) and runs it. If the routing rules below
ever drift from AGENTS.md, **AGENTS.md wins** — open a PR to
re-align this file.

You are working in `~/projects/brain`. Four operations sit beneath
this skill:

- **`wiki-ingest`** — edits the permanent + state layers of the
  affected repo's wiki, plus cross-cutting wiki-root pages.
- **`palace-mine`** — pushes raw text into mempalace's verbatim
  retrieval surface.
- **`feedback-ingest`** — processes AI-summarised user feedback into
  `kind: insight` pages.
- **`shape`** — *the only path* to ADRs and PRDs. When the input is
  a forward-looking pitch or a decision the code already encodes,
  intake hands off here.

Users (and you) shouldn't have to remember which to run; this skill
picks the right one (or chains them) based on the input.

## Routing

| Input shape                                                              | Action                                                                                                                                              |
|--------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| Sibling repo path under `~/projects/<repo>/` (or `<repo>` of one)        | `palace-mine` first (`projects` mode, wing=`<repo>`), then `wiki-ingest`. If `wiki-ingest` flags pre-existing decisions during the read, hand each off to `shape --record`. |
| `sources/ai_user_feedback/<date>/`                                       | `feedback-ingest` against the batch.                                                                                                                |
| `sources/ai_user_feedback/` (no date)                                    | Pick the most recent unprocessed batch (consult `log/log.md`), then `feedback-ingest`.                                                              |
| Notion URL whose content is a **forward pitch / RFC / planning doc**     | `shape <repo> --from-notion <url>`. The PRD is brain-authored; the URL is cited as input.                                                           |
| Notion URL whose content is a **past decision / ADR record**             | `shape <repo> --record --from-notion <url>`. ADR-only flow, post-hoc capture.                                                                       |
| Notion URL whose content is **descriptive / reference-shaped**           | `wiki-ingest`: live-read via MCP, snapshot to `sources/notion/<slug>--<id>.md`, edit the relevant `wiki/<repo>/permanent/*.md` or root page.        |
| Inline pitch (`<repo>: <pitch text>` or just `<repo> <pitch>`)           | `shape <repo> <pitch>`.                                                                                                                              |
| `record: <repo> <description>`                                           | `shape <repo> --record <description>`.                                                                                                              |
| URL whose content is **competitor-shaped** (press release naming a competitor company; product page on a competitor's domain; trade-press article naming a competitor in the organisation's market context) | `wiki-ingest` competitor-route: snapshot to `sources/web/competitors/<competitor>/<slug>--<shortid>.md`, edit/create `wiki/org/competitors/<competitor>/index.md`. See [`wiki/brain/adrs/competitor-intel-ingestion.md`](../../../wiki/brain/adrs/competitor-intel-ingestion.md). |
| Other URL (`http://`, `https://`)                                        | `wiki-ingest` (which snapshots to `sources/web/<host>--<slug>.md` first).                                                                           |
| Path under `sources/` already                                            | `wiki-ingest` directly.                                                                                                                              |
| Pasted text / chat transcript / unclassified file                        | `wiki-ingest` (saves to `sources/notes/<slug>--YYYY-MM-DD.md`).                                                                                     |

If the input is ambiguous (e.g. a Notion URL that *could* be either
forward or past), **ask one clarifying question before routing.**
Don't run any sub-skill speculatively.

## Notion: telling forward from record-existing

Use the `notion-fetch` response to classify before routing:

- **Forward signals**: title contains "Pitch", "Proposal", "RFC",
  "Idea". Body uses future tense, mentions appetite / sizing,
  asks "should we" or "let's." Pages under a "Pitches" or
  "Roadmap" parent.
- **Record signals**: title contains "Decision", "ADR", "Rationale",
  "Why we chose". Body uses past tense, names alternatives that
  were rejected.
- **Reference signals**: descriptions of how a system works today,
  domain glossaries, architecture diagrams. No decision being
  made; no pitch being shaped. → `wiki-ingest`.

## Overrides

The user can force a route with a leading marker:

- `mine: <target>` — force `palace-mine` only, skip ingest.
- `feedback: <date or path>` — force `feedback-ingest`.
- `ingest: <target>` — force `wiki-ingest` only.
- `shape: <repo> <pitch>` — force forward `shape`.
- `record: <repo> <description>` — force record-existing `shape`.
- `competitor: <name>` — force the competitor-content route on a URL the auto-classifier missed (or got wrong). Snapshot lands at `sources/web/competitors/<name>/<slug>--<shortid>.md`; synthesis lands at / edits `wiki/org/competitors/<name>/index.md`. Used as a leading marker (`competitor: ashby https://...`) or trailing marker (`/in https://... competitor: ashby`); both forms accepted.

## Helper fan-out (parallel-first)

When the input has parallel shape — a multi-source batch under
`sources/ai_user_feedback/<date>/`, a sibling-repo path that
spawns both `palace-mine` and `wiki-ingest` runs, multiple Notion
URLs in one invocation, an `ingest:` override pointed at a
directory of files — default to fanning out helper subagents in
a single message rather than serial tool calls. Each helper
processes one source / file / sub-batch and reports back; the
intake skill synthesises the routing decisions and surfaces a
single consolidated handoff. Per
[`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md).

## Hand-off mechanics (important)

When routing leads to `/shape`, the hand-off is **not** a TODO and
**not** a follow-up PR. It's a **same-session, same-PR** invocation:

1. The intake announcement names `/shape` as the next step.
2. The agent loads the `shape` skill and runs its protocol fully.
3. The resulting `wiki/<repo>/{prds,adrs}/<slug>.md` files (slug-only
   per AGENTS.md § ADR / PRD filenames are slug-only) are added to
   the same working tree.
4. Permanent / state edits made by `wiki-ingest` (if it ran first
   on the same input) and the new PRD/ADR files all land in the
   same PR.

This is what "automated `/shape`" means: ingest detects → ingest
finishes its part → ingest invokes `/shape` → all artefacts go in
one PR. No manual hop.

## Announce before acting

Before running, state in one sentence which underlying skill(s)
will run and why. Examples:

> "Treating `~/projects/cli` as a sibling-repo intake — running
> palace-mine (wing: cli) then wiki-ingest. If wiki-ingest spots
> pre-existing decisions, those will hand off to /shape --record
> in the same session."

> "This Notion URL is a pitch (title: 'Pitch: candidate scoring
> v2'). Routing to /shape <repo> --from-notion."

> "This Notion URL describes how the application form works today —
> reference-shaped, no decision being made. Routing to wiki-ingest
> for permanent + state edits."

## Land it — `/pr` is mandatory, not optional

**Ingesting into the brain ends at a merged PR, not at edits in the
working tree.** Snapshots in `sources/`, edits in `wiki/`, and a clean
local validate are necessary but not sufficient — until the change is
on `origin/main`, the brain has not actually been updated and other
agents / sessions / the deployed UI cannot see the work. A user
asking "did you ingest X?" expects to find X on GitHub.

The landing chain after the sub-skills finish editing the working
tree:

1. **`/pr`** — feature branch, commit, push, open the PR. The `/pr`
   skill itself owns the post-open contract: watch CI to completion,
   chain to `/review` on green.
2. **`/review <PR#>`** — same session, fires automatically on CI
   green. For non-`/shape` ingests the agent self-merges; for
   `/shape`-shaped PRs, `/review` defers to a human `APPROVED`
   review and the agent surfaces the URL and stops.
3. **`log/log.md`** — the audit line lands on the merging branch as
   part of the merge (per `AGENTS.md` § Governance > Audit log). It
   does **not** exist on a working-tree-only run; if you stop before
   merge, no log line.

The only legitimate reasons to stop short of a merged PR:

- The user explicitly says *"snapshot only, don't open a PR yet"* /
  *"just stage these locally"*. Honour that, but confirm — the
  default is the full chain.
- `/shape` is in the chain and Phase 1 / Phase 2 hits its
  human-approval gate (Phase boundary stop is built into `/shape`).
- Local validate / check fails and cannot be fixed from inside the
  same skill run; surface the failure and ask.

## Done check — terminate on observable state, not declared intent

Each item must be verifiable from current repo / wire state.

- [ ] Routing decision was announced in plain English (in chat).
- [ ] Each underlying skill ran its full protocol (don't shortcut
      their done-checks).
- [ ] If routing produced a hand-off chain (e.g. wiki-ingest → shape
      --record), the chain ran in one session and all artefacts are
      in one PR.
- [ ] **`/pr` invoked** — a PR exists for the work.
- [ ] **PR landed** — `gh pr view <PR#> --json mergedAt --jq .mergedAt`
      is non-null **OR** the PR is `/shape`-shaped and the user was
      asked to take over **OR** the user explicitly halted the chain
      ("snapshot only, don't ship yet") and the override was *surfaced
      in chat*, not silently applied.
- [ ] If merged: the audit line is on `main` (per `/pr`'s Done check).
- [ ] If the user said "snapshot only", that override is honoured and
      surfaced; otherwise the full chain ran.
