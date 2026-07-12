---
name: wiki-ingest
description: Ingest a source into the brain wiki — search mempalace for prior context, snapshot the source to sources/ if external, decide which existing or new wiki page(s) it touches, edit the right shelf (`permanent/*` / `state.md` / cross-cutting root pages) with structured frontmatter and the right section shape, update index.md, append to log.md. Sub-skill of `/in`; the user-facing command is `/in` (or `ingest: <target>` to force this skill only). Hands off to `/shape` whenever the source contains a forward pitch or a pre-existing decision — never writes to `prds/` or `adrs/` directly. Load when the user says "ingest", "pull into the brain", "add to the wiki", "absorb this", or otherwise asks to incorporate new material.
---

# Ingest a source into the wiki

You are working in `~/projects/brain`, an LLM-maintained markdown wiki built
on Karpathy's three-layer pattern (raw sources → wiki → schema) with
mempalace as the verbatim retrieval layer. `AGENTS.md` is the schema.

**Single source of truth.** The shelf-routing table below is mirrored
in `AGENTS.md` § Routing ingested content to the right shelf, and the
ADR/PRD hand-off rule is in `AGENTS.md` § Shape — universal authoring
path. If the two ever drift, **AGENTS.md wins** — open a PR to
re-align this file.

The ingest target may arrive as: a path under `~/projects/`, a Notion URL,
a pasted block of text, a chat transcript, an external URL, or "the latest
work in <repo>".

## Anti-poisoning rule

The wiki is a *derived view*. Never re-ingest content from `wiki/` as if
it were a source. Sources live in `sources/`, sibling repos under
`~/projects/`, or external systems (Notion, URLs). If you find yourself
wanting to "ingest" a wiki page, you actually want `/lint` or `/overlap`.

## Protocol

### 0. (Sibling-repo only) Consult the sync cursor — incremental ingest

**When the target is a sibling repo** (`~/projects/<repo>/`), and
**before** reading the source end to end, narrow scope using the
sync cursor stored at `wiki/_state/sync-cursors.json`:

1. Run sibling-repo handling first — `tools/sync-siblings.sh` per
   AGENTS.md § Sibling-repo handling. If the sibling is on a feature
   branch or has uncommitted changes, **don't update the cursor at
   the end** — just note the divergence in the synthesis. Continue
   the rest of the protocol against the working tree as-is.
2. `python3 tools/brain.py sync-cursor diff <repo>` — prints paths
   changed since the last cursor SHA. If the cursor is absent
   (first-pass ingest), the command prints all tracked files plus a
   stderr note. If the cursor SHA is unreachable (sibling rebased /
   force-pushed), it falls back to a full listing with a loud
   stderr warning.
3. **Walk only those paths** in step 1 below. Skipping unchanged
   files is the whole point of the cursor — don't re-read what
   didn't move.
4. After the synthesis lands and the audit log is appended (step
   8), advance the cursor:
   ```
   python3 tools/brain.py sync-cursor set <repo> \
     --synced-by "PR #<num> or log line"
   ```
   The `set` command refuses if the sibling isn't on main with a
   clean tree (per AGENTS.md). Don't `--force`; if the rule fires,
   leave the cursor unchanged and surface that in the log line so
   the next ingest knows to re-attempt.

For non-sibling-repo targets (Notion URLs, pasted text, external
URLs, files already under `sources/`), skip this step entirely —
those have their own freshness model (immutable snapshots).

### 1. Read the source end to end

Don't skim. If it's a long doc, read it once fully before deciding what to do.

### 2. Check prior context **before** writing

Walk `wiki/index.md` and read any candidate pages that look topically
related — *prefer editing existing pages over creating new ones*.

Run `mempalace search "<phrase>"` on key concepts from the source. If the
palace looks stale (no recent mine for this corpus, or `mempalace status`
shows a thin wing), run `/mine` against the source first so the search has
fresh material to hit on.

### 3. Snapshot if the source is external

| Source type                              | Action                                                      |
|------------------------------------------|-------------------------------------------------------------|
| File inside a sibling repo (`~/projects/<repo>/...`) | Cite the path directly — sibling repos are raw sources. Do **not** copy into `sources/`. |
| Notion page                              | **Read-only** via the claude.ai Notion MCP (`notion-search`, `notion-fetch`) for live retrieval. Then snapshot to `sources/notion/<slug>--<id>.md` via `tools/notion-export.py` for immutability. Cite both paths. **Never write to Notion.** |
| Pasted text from chat / a person         | Save to `sources/notes/<slug>--YYYY-MM-DD.md` with a one-line provenance comment at the top. |
| External URL (blog, RFC, gist)           | Save the rendered text to `sources/web/<host>--<slug>.md`; include the URL and pull date in a top comment. |
| Anything binary                          | Keep it out of git. Reference an external location (S3, Drive) and note that in the wiki page. |

Anything you save to `sources/` is **immutable** going forward. Re-fetches
overwrite, but they are not edited.

### 4. Decide which wiki page(s) the source touches

For sibling-repo content, the brain has a **layered per-repo
structure** (per `AGENTS.md` § Wiki structure):

```
wiki/<repo>/
├── index.md
├── permanent/         # nested-emergent (sub-folders earn their place)
│   ├── purpose.md
│   ├── architecture.md   (or architecture/index.md + sub-aspects)
│   ├── conventions.md
│   ├── interfaces.md
│   └── domain.md
├── state.md
├── adrs/              # ONLY written via /shape — never directly here
└── prds/              # ONLY written via /shape — never directly here
```

**`/in` never writes to `adrs/` or `prds/` directly.** Those are
populated exclusively by `/shape`. When you spot a pitch, RFC, or
pre-existing decision, hand off to `/shape` rather than authoring
the PRD/ADR yourself.

**Route the ingest to the right shelf** before editing:

| Content shape                                                       | Shelf / route                                          |
|---------------------------------------------------------------------|--------------------------------------------------------|
| Code-shape facts (stack, modules, public surface)                   | `wiki/<repo>/permanent/architecture.md` (edit)         |
| External contracts (HTTP, GraphQL, jobs, events, SDK API)           | `wiki/<repo>/permanent/interfaces.md` (edit)           |
| Style + pattern observations                                        | `wiki/<repo>/permanent/conventions.md` (edit)          |
| Domain vocabulary / entities / concepts                             | `wiki/<repo>/permanent/domain.md` (edit / promote)     |
| "What's true today" observation; new capability shipped             | `wiki/<repo>/state.md` § Now (edit)                    |
| New milestone in the repo's history                                 | `wiki/<repo>/state.md` § Past (append)                 |
| New gap / risk surfaced (Now-vs-Perceived)                          | `wiki/<repo>/state.md` § Perceived (edit)              |
| Future intent / strategic shift                                     | `wiki/<repo>/state.md` § Target (edit)                 |
| Notion **pitch / RFC** targeting a repo (forward-looking)           | **Hand off to `/shape <repo> --from-notion <url>`.**   |
| Notion **decision / past ADR** targeting a repo                     | **Hand off to `/shape <repo> --record`.**              |
| Repo-detected pre-existing decision (e.g. "Bun chosen over Node")   | **Hand off to `/shape <repo> --record`.**              |
| Cross-repo process / methodology (Shape Up, onboarding)             | `wiki/` root (edit / create)                           |
| Customer-feedback insights                                          | `wiki/insights/` (cross-cutting; via `/feedback`)      |
| Brain-self meta (the brain itself)                                  | `wiki/brain/` (e.g. `roadmap.md`, `state.md`)          |

If a concept inside `permanent/` has grown 2+ specialised
sub-aspects (e.g. `architecture` covers ember-spa, avo-admin, and
liquid templates as distinct subsystems), **promote** it: rename
`permanent/<concept>.md` → `permanent/<concept>/index.md`, then add
the specialised sub-pages as siblings under the new folder. Don't
promote preemptively — flat is correct until two specialisations
push it.

**Default to editing existing pages.** New pages are mostly the
`/shape`-authored trail under `adrs/` and `prds/`. Everything else
is edit-in-place.

If a single source spans shelves (e.g. a Notion page that *both*
describes architecture *and* states a forward pitch), split: edit
`permanent/architecture.md` for the architecture facts; hand off
the pitch to `/shape`.

### 4a. Hand-off mechanics for `/shape`

When the routing rule says "Hand off to `/shape`," it is **not** a
TODO and **not** a follow-up PR. The hand-off is **same-session,
same-PR**:

1. Finish your wiki-ingest part first — edit the affected
   `permanent/*` and `state.md` pages with whatever this source
   contributes to the durable / state layers.
2. Announce the hand-off explicitly:
   > "This source also contains a forward pitch for `<repo>` —
   > handing off to `/shape <repo> --from-notion <url>`."
3. Load the `shape` skill and run its full protocol against the
   same input.
4. The PRD / ADR file(s) `/shape` produces land in the same
   working tree as your `permanent/` and `state.md` edits.
5. All artefacts go into one PR.

A single Notion page (or a single repo ingest pass) often produces
*both* permanent edits *and* a `/shape`-authored ADR/PRD. That's
the design — one source, multiple shelves, one PR.

When `/shape` rejects the input (the PM agent doesn't see a pitch
worth shaping; no clear user persona; appetite mismatch), `/shape`
logs the rejection and stops. The wiki-ingest edits to `permanent/`
and `state.md` still land.

If a sibling-repo ingest detects *multiple* pre-existing decisions
(e.g. reading the cli source surfaces "Bun chosen over Node",
"oclif over Yargs", and "GitHub Packages over npm public" all at
once), invoke `/shape <repo> --record` once per decision in the
same session. Each gets its own ADR; all go in one PR.

### 5. Pick the page kind

Set `kind:` in frontmatter. The kind drives the section structure.

| Kind         | When to use                                                      |
|--------------|------------------------------------------------------------------|
| `reference`  | The source describes how something *is* — a stack, a repo's layout, a convention, an API surface. |
| `initiative` | The source is about active product or technical work — a feature, a refactor, a migration, a roadmap item. |
| `decision`   | The source is or codifies a specific decision (RFC, ADR, design doc concluding on an option). |
| `entity`     | The source is about a person, team, division, product, or customer. |
| `insight`    | The source is user feedback / data — synthesise a pattern. Usually written via `/feedback`, not directly via `/ingest`. |
| `meta`       | About the brain itself.                                          |

If a single source spans kinds (e.g. a PRD that *both* explains an
initiative *and* records a decision), split it across pages of the right
kinds rather than mixing structures on one page.

### 6. Edit the page(s)

Every wiki page starts with YAML frontmatter:

```yaml
---
title: <human title>
kind: reference | initiative | decision | entity | meta
status: draft | living | superseded | archived
updated: YYYY-MM-DD
# Optional but recommended where applicable:
team: <primary owning team>
division: <umbrella org unit>
repos:
  - <repo name>
depends_on:
  - <other-page.md>
confidence: high | medium | low
supersedes: <older-page.md>
superseded_by: <newer-page.md>
sources:
  - sources/...
  - ~/projects/<repo>/<path>
  - https://notion.so/...
---
```

Only `title`, `kind`, `status`, `updated`, and `sources` are required.

When creating a new page, copy from `tools/templates/<kind>.md` rather
than handcrafting the structure — it carries the required sections
already and keeps shape consistent across runs.

#### Section structure by kind

**`reference`** — describe state-of-the-world. No mandatory sections.
Suggested: a short intro paragraph, then `## Stack` / `## Layout` /
`## Conventions` / `## Open threads` as the material warrants. Do *not*
force Now/Perceived/Target onto reference pages.

**`initiative`** — active work. Required sections:

```markdown
## What
The concrete change, feature, system, or piece of work.

## How
Implementation approach: architecture, refactor path, rollout plan,
dependencies, sequencing.

## Why
Motivation: user need, business goal, constraint, incident, technical
debt being paid down. Cite sources.

## Now
What is *actually* true today, grounded in citable sources (code paths,
prod state, recent commits).

## Perceived
What the org appears to *believe* is true. Diverges from Now when docs
are stale or teams have inconsistent mental models. Note the gap
explicitly when you see it.

## Target
Where we want to be: explicit intent, next milestone, desired end state.
```

**`decision`** — ADR-style. Required sections:

```markdown
## What
The decision in one or two sentences.

## Why
The forces and constraints that drove it.

## How
The shape of the implementation that follows from the decision.

## Alternatives
Options considered and why they were not chosen.

## Consequences
What this commits the org to; trade-offs accepted.
```

**`entity`** — a profile. No mandatory sections; keep short.

#### Body conventions

- Cite sources for every non-trivial claim. Use repo-relative or absolute
  paths, or full URLs.
- Mark uncertainty inline as **(unverified, YYYY-MM-DD)** or
  **(unknown — needs source)**. Don't invent.
- Voice: present tense, declarative.
- Dates: absolute (`2026-04-29`), never relative.
- Cross-link other wiki pages with relative markdown links.
- When mempalace surfaced a useful verbatim passage, link to it via a
  search key the future reader can re-run, e.g.:

  ```
  *Verbatim:* `mempalace search "<query>"` → `<wing>/<file>` (drawer match ~0.41).
  ```

#### Supersede, don't silently overwrite

When a source forces a meaningful change to an existing page's
conclusions:

- If the change is incremental (a stack version bumped, a new convention
  added), edit in place and bump `updated:`.
- If the change *replaces* a prior synthesis (an initiative cancelled, a
  decision reversed, a system rebuilt), set `status: superseded` on the
  old page, create a new page with `supersedes: <old>.md`, and link both
  ways. Auditable history matters for regenerability.

### 7. Update `wiki/index.md`

Add or revise the page's entry. One line:

```
- [Title](path.md) — one-line hook
```

Group under section headings as themes emerge. Don't pre-create headings
for hypothetical future content.

### 8. Stage the audit-log line

Append to `log/log.md` on the feature branch (one line, newest at the
bottom):

```
YYYY-MM-DD ingest — <source> → <page1>, <page2>
```

Use today's date in absolute form. The brain's "today" is whatever
the session reports. The line **lands on `main` only when the PR
merges** — per `AGENTS.md` § Governance > Audit log, branch
protection requires the audit update to ride through the same PR (or
a tiny follow-up PR). Don't try to push it to `main` directly; it
will be rejected.

If the working-tree-only path is what the user explicitly asked for
("just stage, don't ship"), the log line stays unwritten — the log
records merges, not stages.

### 9. Land via `/pr` — mandatory

**Ingesting ends at a merged PR, not at edits in the working tree.**
Until the change is on `origin/main`, the brain has not been
updated; other agents, sessions, and the deployed UI cannot see the
work; and the audit line stays absent from `log/log.md`. A user
asking "did you ingest X?" expects X to be discoverable on GitHub.

After the working-tree edits are clean and `brain.py validate` +
`brain.py check --no-net` pass locally:

1. **`/pr`** — feature branch, commit (including the audit line from
   step 8), push, open the PR. The `/pr` skill itself owns the
   post-open contract: watch CI to completion and chain to
   `/review` on green.
2. **`/review <PR#>`** fires automatically when CI is green; for
   non-`/shape` ingests the agent self-merges, and the audit line
   lands on `main` as part of the merge.

The only legitimate stops short of a merged PR:

- Explicit user override ("snapshot only, don't ship yet").
- `/pr` rejected the diff (validate / check failure that requires
  user input).
- The PR is `/shape`-shaped and `/review` deferred to a human
  `APPROVED` review (`/shape` Phase boundaries do this by design).

In any of those cases, surface the state to the user with the next
action they would take — don't silently leave the work in the tree.

## Done check

Before declaring the ingest done:

- [ ] Source is readable from a stable path (sibling repo, `sources/...`,
      or pinned URL).
- [ ] Page(s) live under `wiki/` and have valid frontmatter with `kind`,
      `status`, and `updated` set to today.
- [ ] If `kind` is `initiative`, all six sections (What/How/Why/Now/
      Perceived/Target) are present, even if some are explicitly
      `(unknown — needs source)`.
- [ ] If `kind` is `decision`, all five sections (What/Why/How/
      Alternatives/Consequences) are present.
- [ ] Every non-trivial claim cites a source or is marked unverified.
- [ ] `wiki/index.md` § Where to find things lists any new page (the
      wayfinding catalog).
- [ ] `wiki/index.md` § What changed has a one-line entry for this
      ingest. If the source is high-signal, § Curated picks is also
      updated. Per
      [`wiki/brain/adrs/home-content-shape.md`](../../../wiki/brain/adrs/home-content-shape.md):
      every wiki/ edit must be paired with a wiki/index.md edit.
- [ ] `log/log.md` has the audit line staged on the feature branch
      (it lands on `main` via the merge).
- [ ] No orphan pages introduced (page exists but isn't in `wiki/index.md`).
- [ ] No content in `wiki/` was treated as a source.
- [ ] **PR landed** — `gh pr view <PR#> --json mergedAt --jq .mergedAt`
      is non-null **OR** the PR is `/shape`-shaped and the user was
      asked to take over **OR** the user explicitly halted the chain
      and the override was *surfaced in chat*, not silently applied.
