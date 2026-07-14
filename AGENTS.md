# AGENTS.md — schema for the brain

You are the agent maintaining this repository. This file tells you how.
The methodology is the LLM-wiki pattern from
<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>,
with [mempalace](https://github.com/mempalace/mempalace) as the verbatim /
semantic-recall layer.

This is the **kernel schema** — organisation-agnostic. Per-organisation
facts (org name, active repos) live in `brain.config.yml`; this file
describes the mechanism. Edit it as the mechanism evolves, not to hold
content.

## Mission

Maintain a synthesis of the organisation this brain serves — products,
repositories, decisions, people, roadmap — accurate enough that:

1. **Codebases could be regenerated** from the specs stored here. The brain
   is the *source of understanding*; the sibling repos under
   `$BRAIN_PROJECTS_ROOT` (default `~/projects/`) are the *source of code*.
   The two stay aligned.
2. **Cross-team overlaps surface, not hide.** When two teams (or two parts
   of one team) work on adjacent problems — product *or* technical, across
   repositories *or* within a single repo — the brain makes that overlap
   visible. Decision-making and alignment are first-class outputs.
3. **Autonomous agents can use this as their primary context.** The brain
   is built so that agent operations can plan, decide, and implement
   against it as their main working memory rather than against raw
   codebases alone.

## Governance — multi-agent collaboration

The brain is a shared working space for humans *and* autonomous
agents. Branch protection on `main` is enforced; every change lands
via PR. Agents can author *and* merge their own PRs as long as CI is
green — the remaining guards (CI checks, confidence floor,
sources/-additive, audit log) are sufficient at this scale.

### Local-first mode (the LOCAL_FIRST escape hatch)

When the repo's machine-local `.env` declares `LOCAL_FIRST=true`,
**the PR/CI ritual is suspended** for that operator's session. The
brain is being used as a single-operator working space; remote
gates would only add latency. Read the toggle on every session
start:

```bash
[ -f .env ] && grep -q '^LOCAL_FIRST=true$' .env && echo "local-first"
```

The contract when `LOCAL_FIRST=true`:

- **Work normally on the current branch** (whatever it is, including
  `main`). No auto-branching. No `git push`. No `gh pr create`.
- **Don't pause for instruction.** Agents and skills proceed
  through their normal multi-step work — Phase 1 / Phase 2 / Phase 3
  of `/shape`, ingest sweeps, lint passes, view regen — landing each
  step as a **local commit** on the current branch instead of a PR
  boundary. Commit messages are unchanged; the diff still tells the
  story.
- **All validations still run locally**, exactly as the PR pre-flight
  would: `brain.py validate`, `brain.py check --no-net`,
  `brain.py views` + `git diff --exit-code wiki/_views/`. A failure
  is still a hard stop — fix and recommit. The CI workflow at
  `.github/workflows/validate.yml` is not consulted.
- **Audit log is still appended** (`log/log.md`) on each commit.
  The audit trail predates the PR convention and remains useful
  even without one. `restricted-paths:` flag is still computed and
  noted in the commit body when applicable.
- **Confidence floor still applies.** Agent-authored content starts
  at `confidence: low` (or `medium` with cited evidence). The same
  pattern as PR mode; unchanged.
- **`sources/**` is still additive only.** The immutability
  guarantee is operator-independent.
- **`/pr` only fires on explicit user request.** When the operator
  says "open a PR" / "ship this" / `/pr`, the skill flips into
  remote mode for that single invocation: branch (if on `main`),
  push, `gh pr create`, hand off to `/review`. The next operation
  returns to local-first.
- **`/review` is dormant.** No remote PR exists to review.
- **`/shape` collapses phase boundaries.** Phase 1 (PRD), Phase 2
  (ADR), Phase 3 (build) each land as one or more local commits on
  the current branch. The human gate that normally lives at PR
  approval moves into the conversation — the operator approves
  inline before the next phase starts. The artefact-shape rules
  (paths under `<scope>/{adrs,prds}/` vs. `<scope>/ai-suggestions/`,
  banner + frontmatter for AI-suggestions, no-code-blocks, etc.)
  are unchanged — they're properties of the artefact, not the
  ritual.
- **`/continue` works on the current branch.** Phase detection
  reads local commit history + working tree state, not `gh pr
  list`. No "address PR comments" sub-step (no PR exists).
- **`/spawn` still creates worktrees + branches**, but child efforts
  do not auto-open PRs at completion — they land their work locally
  in the worktree. The operator decides when (and which) to push.

The three rules below apply when `LOCAL_FIRST` is unset or `false`.
Switching modes is a `.env` edit; no reset, no migration.

### The three rules

1. **PR-required.** Agents work on feature branches; never push to
   `main`. PRs gate every change with an auditable diff. Use `/pr` to
   open; `/review` to land.
2. **CI must pass.** `.github/workflows/validate.yml` is the gate —
   `brain.py validate` + `brain.py check --no-net` + verifying the
   auto-generated `wiki/_views/` is current. No exceptions.
3. **Confidence floor.** Agent-authored content starts at
   `confidence: low` (or `medium` with cited evidence). Cannot
   self-promote to `high` in the same PR.

For most PRs (ingests, lint sweeps, view regenerations,
synthesis edits, brain-meta governance changes outside `/shape`)
**the agent self-merges as soon as CI is green** — the three
rules above are sufficient. The next subsection carves out the
single exception: PRs produced by `/shape`.

### `/shape` is manual by default; `--auto` opts in to autonomous

`/shape` is **manual by default**: the agent surfaces options +
trade-offs at every load-bearing in-phase decision (slug,
appetite, affected persona, no-gos / rabbit holes, Phase 2
alternatives + bet, pattern-fit divergence) and **waits for the
user to pick** before authoring the artefact. The agent's job is
to surface tradeoffs, not to decide for the user.

The `--auto` flag (combinable with any mode — `--epic`,
`--record`, `--from-notion`, `--rfc`) flips the in-phase
decision policy to autonomous: the agent picks the option it
would recommend and records the choice + reasoning visibly so
the user can course-correct. **Phase-end approval gates always
apply** regardless of `--auto` — see the next subsection.

When in doubt about whether a decision is load-bearing enough
to pause for, **pause**. The cost of an extra one-line
confirmation is far smaller than the cost of an ADR/PRD that
locks in the wrong bet because the agent guessed silently.

### `/shape` PRs are human-gated at every phase

`/shape` (forward, `--record`, and `--rfc` modes) authors
ADRs (`kind: decision`) and PRDs (`kind: initiative`) into the
human-approved shelves at `wiki/<scope>/{adrs,prds}/`. These are
**commitment-class artefacts**: they record either "the team is
committing to do Y" (PRD) or "the team has decided X" (ADR). Routine
ingests are observation; `/shape` outputs are commitment.
Commitment-class work needs explicit human sign-off — CI alone
is not the gate.

The rules:

1. **Phase 1 (PRD authoring) lands as its own PR** and **stops
   for human approval before phase 2 starts.** The agent opens
   the PR, waits for CI green, posts the PR URL, and **does not
   author the ADR until the human has explicitly approved the
   PRD** (a GitHub PR review with state `APPROVED`, or an
   explicit go-ahead in the conversation). Approval of phase 1
   is *both* permission to merge the PRD PR *and* permission to
   start phase 2.
2. **Phase 2 (ADR authoring) lands as its own PR** and **stops
   for human approval before merge.** Same gate at the end:
   PR opens, CI runs, the agent surfaces the URL, and waits.
   The phase-1 approval does **not** carry over — phase 2 gets
   its own gate.
3. **Both PRs need a human `APPROVED` review before merge.**
   `/review` will refuse to auto-merge any PR that touches
   `wiki/<scope>/{adrs,prds}/<slug>.md` outside any
   `ai-suggestions/` subfolder unless a non-author human review
   in `APPROVED` state is present.

This applies regardless of whether `/shape` is invoked
explicitly by the user (`/shape <repo> <pitch>`) or chained from
`wiki-ingest` after spotting forward-pitch / pre-existing-decision
content in a source.

The relationship to the next subsection:

- The `ai_suggestion: true` shape (and the `ai-suggestions/`
  shelf) is for **unsupervised** agent runs — the agent acts on
  its own initiative, lands the artefact in the suggestion shelf,
  and graduation to the human-approved shelf is its own PR with
  human review.
- The `/shape`-PR-human-gate above is for **supervised** agent
  runs — the human asked the agent to shape something into the
  live shelves directly. Even then, each phase boundary needs
  its own human approval; the human is in the loop turn-by-turn.

The two patterns coexist. Both end in human-approved artefacts;
they differ in *where the agent's draft lives between author and
approval* (`ai-suggestions/<adrs|prds>/` vs. a feature-branch PR
diff against `<adrs|prds>/`).

### `ai_suggestion` — agent-authored ADRs/PRDs are suggestions, not decisions

ADRs (`kind: decision`) and PRDs (`kind: initiative`) authored by
an agent on its own initiative — without a human reviewing,
iterating, and explicitly approving — are **suggestions**, not
records of decisions. They are *ideas to explore*, **not**:

- A decision the team has made.
- The current state of the product.
- An upcoming product change.

The legitimate path to a real ADR/PRD is **human-supervised**:
a human reviews the PRD → iterates → approves; a human reviews
the ADR(s) for that PRD → iterates → approves. Only the
approved artifact is authoritative for downstream agents.

#### Folder separation — never co-mingle suggestions with approved decisions

Suggestions live separately from human-approved decisions at
**three scopes** that match the brain's three-level model
(brain / org / repo) plus the ADR/PRD distinction:

| Scope             | Path (human-approved)          | Path (AI-suggestion drafts)                  | When to use                                                              |
|-------------------|--------------------------------|-----------------------------------------------|---------------------------------------------------------------------------|
| **Per-repo**      | `wiki/<repo>/adrs/<slug>.md`   | `wiki/<repo>/ai-suggestions/adrs/<slug>.md`   | Decisions specific to one repo.                                            |
| **Per-repo**      | `wiki/<repo>/prds/<slug>.md`   | `wiki/<repo>/ai-suggestions/prds/<slug>.md`   | Initiatives specific to one repo.                                          |
| **Org**           | `wiki/org/adrs/<slug>.md`      | `wiki/org/ai-suggestions/adrs/<slug>.md`      | Cross-org decisions that touch ≥ 2 repos or define org-wide policy.        |
| **Org**           | `wiki/org/prds/<slug>.md`      | `wiki/org/ai-suggestions/prds/<slug>.md`      | Org-level initiatives (cross-cutting product / process / methodology).     |
| **Brain (meta)**  | `wiki/brain/adrs/<slug>.md`    | `wiki/brain/ai-suggestions/adrs/<slug>.md`    | Decisions about the brain itself (schema / skills / tooling / governance). |
| **Brain (meta)**  | `wiki/brain/prds/<slug>.md`    | `wiki/brain/ai-suggestions/prds/<slug>.md`    | Brain-self initiatives.                                                    |

The folder separation is the **load-bearing convention** at every
scope. The `ai_suggestion: true` frontmatter flag is the layered
safety check; the path is the primary signal. **Never write a
suggestion-shaped artifact into the human-approved paths
directly** — it corrupts the trail at whatever scope it lands.

`ai-suggestions/` is a reserved name analogous to `wiki/_archive/`
and `wiki/_views/`. Each scope's `ai-suggestions/` folder
contains exactly two subfolders (`adrs/` + `prds/`); empty
folders are not created preemptively.

#### Picking the right scope

When the agent decides where a new suggestion lives, the rule of
thumb is **"narrowest scope that captures the decision"**:

- If the decision is **specific to one repo's code, conventions,
  or trail** — per-repo (`wiki/<repo>/ai-suggestions/`).
- If the decision **affects ≥ 2 repos** or **defines org-wide
  policy** (process, methodology, cross-product convention,
  shared tooling adoption) — org (`wiki/org/ai-suggestions/`).
- If the decision is **about the brain itself** — its schema,
  skills, governance, validator, templates, audit rules,
  tooling — brain (`wiki/brain/ai-suggestions/`).

When in doubt, prefer the narrower scope; suggestions can be
re-scoped during graduation if the human reviewer disagrees.

#### Marking convention

Agent-authored ADRs/PRDs (under `ai-suggestions/`) **must**
carry both:

1. `ai_suggestion: true` in the YAML frontmatter.
2. A prominent banner at the top of the page reading (verbatim
   shape, paraphrasable in detail):

   > **AI-suggested {ADR|PRD}.** Does not reflect a
   > human-approved decision and does not record current
   > product state or upcoming product changes. Agent-authored
   > synthesis from observed patterns; for a human to review,
   > iterate on, and decide whether to graduate.

#### Templates

Each artifact has two templates:

| Template                                | Use for                                          |
|-----------------------------------------|--------------------------------------------------|
| `tools/templates/adr.md`                | Human-approved ADRs.                             |
| `tools/templates/adr-ai-suggestion.md`  | Agent-authored ADR suggestions.                  |
| `tools/templates/prd.md`                | Human-approved PRDs.                             |
| `tools/templates/prd-ai-suggestion.md`  | Agent-authored PRD suggestions.                  |

The AI-suggestion templates frame language in
inference-with-uncertainty mode (*"the prep notes suggest…"*,
*"the repo state is consistent with…"*), include an "Open
questions for the human reviewer" section, and explicitly
distinguish *observation* from *hypothesis*.

#### Graduation

When a human reviews + iterates + approves an agent-authored
suggestion, the graduation PR:

1. Drops `ai_suggestion: true` from frontmatter.
2. Removes the banner.
3. Bumps `confidence:` as appropriate (typically `low` →
   `medium`).
4. Changes `status:` from `suggested` to `accepted` (ADR) or
   `living` (PRD).
5. **Moves the file** from `<scope>/ai-suggestions/{adrs,prds}/`
   to `<scope>/{adrs,prds}/`, where `<scope>` is `wiki/<repo>`,
   `wiki/org`, or `wiki/brain` per the suggestion's scope.
6. Reshapes language from inference-mode ("the team appears to
   have…") to direct-mode ("we adopted…"), correcting any
   factual errors the human catches.

The artifact is otherwise unchanged in shape.

#### The shape rule for agents

When the user prompts you to author an ADR or PRD without a
review-iterate-approve loop in the same session, produce it as
an `ai_suggestion`. The user's "go author this" is a request
for a *suggestion*, not pre-approval of a decision. The user
must come back, review, and explicitly graduate it.

#### What does NOT belong in any ADR or PRD (agent or human)

These are **hard rules**, not stylistic preferences:

- **No code blocks** of any kind in ADRs or PRDs — no code in any
  language, no shell. Names and identifiers can be quoted in
  prose; configuration belongs in repo READMEs or
  `permanent/interfaces.md`. Per Nygard + AWS prescriptive
  guidance: ADRs focus on *why*, not *how*. Per ProductPlan: a
  PRD "may hint at a potential implementation to illustrate a
  use case but may not dictate a specific implementation."
- **No interface schemas** (HTTP endpoints, JSON payloads, class
  definitions, database tables). Those belong in
  `permanent/interfaces.md` or a dedicated reference page;
  the ADR/PRD cites them.
- **No how-to instructions / runbooks / migration steps** in
  the ADR or PRD body. Those belong in repo READMEs or
  operational docs.
- **Narrative in complete sentences** (per Nygard). Bullet
  lists for enumerations only (alternatives, consequences,
  affected personas).

#### Cross-cutting analogue (synthesis pages, `kind: reference`)

Agent-authored synthesis pages under `wiki/org/`,
`wiki/<repo>/permanent/`, or similar do **not** carry
`ai_suggestion: true` and do **not** move to a separate
folder — they are *describing existing state*, not making
decisions. They warrant a lighter "Agent-authored synthesis"
note at the top to clarify the descriptive-vs-prescriptive
distinction. Decision-matrix-style tables in those pages are
*observations of established practice*, not policy.

### Path conventions

- `sources/**` is **additive only** — agents may add new files but
  not modify or delete existing ones (the immutability guarantee).
- `wiki/**`, `wiki/_overlaps/**`, `wiki/_views/**`, `wiki/_archive/**`,
  `wiki/_state/**`, and `log/log.md` are the freely-editable agent
  surface.
- "Restricted paths" still exist as a *signal*, not a gate — these
  files affect how agents/humans operate, how the brain is built, or
  how it deploys, and the `/pr` skill flags them in the PR body so
  reviewers can pay closer attention. They are not auto-escalated.
  - `AGENTS.md` (this schema).
  - `brain.config.yml`.
  - `.claude/**` — skills, commands, settings, personas.
  - `tools/**`.
  - Any `Dockerfile`, `.dockerignore`.
  - `.github/**` — CI workflows.
  - `ui/Dockerfile`, `ui/serve.mjs`, `ui/astro.config.mjs`,
    `ui/src/content.config.ts`, `ui/package.json`,
    `ui/package-lock.json`.

### Public artifacts carry no personal data

PR descriptions, commit messages, and release notes are shared —
and on a public repo, world-readable. They **must not** contain
session URLs, private chat links, tokens, emails, or other
account-tied identifiers. Model attribution (`Co-Authored-By:
Claude …`) is fine; a session URL is not.

Enforced deterministically: the `commit-msg` git hook runs
`brain.py check-no-personal-data` (session-URL / account-link
patterns; extend per-org via a git-ignored `.personal-data-patterns`
file), and the `/pr` skill runs the same check on the PR body. If
a harness appends a session URL by default, strip it — the guard
does not depend on the harness behaving.

### Audit log

Every merge appends one line to `log/log.md`:

```
YYYY-MM-DD merge — PR #<num>: <title>
   diff: <files> files, +<insertions>/-<deletions>
   restricted-paths: <true|false>
```

Under `LOCAL_FIRST=true` there's no PR number, so each commit
appends a parallel-shape line keyed on the short SHA:

```
YYYY-MM-DD commit — <short-sha>: <title>
   diff: <files> files, +<insertions>/-<deletions>
   restricted-paths: <true|false>
   by: <author — operator | agent name>
```

The `by:` line attributes the change to the operator or the named
agent (history should distinguish human from named-agent
authorship). Optional on lines predating
2026-07-10; expected on new lines.

The `merge` and `commit` keywords share the date prefix and the
indented `diff:` / `restricted-paths:` shape, so `sync-siblings.sh`
and any future log-walkers continue to parse with the existing
`^[0-9]{4}-[0-9]{2}-[0-9]{2} (mine|ingest|merge|commit)` regex.

The audit line is appended in a follow-up commit on the merging branch
(or a trivial follow-up PR; either is fine — the guard is the diff
visibility, not the merge cadence). `log/log.md` is rotated by `/sync`
when it crosses 2,000 lines or ~200 KB; the rotation procedure lives
in the `sync` skill.

## Knowledge half-life

Permanent knowledge bases rot. `/sync` catches structural rot;
`/groom` catches epistemic rot. Half-life thresholds (per page kind)
and the actions they trigger live in the `groom` skill.

## What the brain tracks for every active piece of work

For initiatives (active product or technical work) and decisions, capture
three dimensions and three states:

**Three dimensions — WHAT, HOW, WHY**

- **WHAT** — the concrete change, feature, system, or decision.
- **HOW** — the implementation approach: architecture, refactor path,
  rollout plan, dependencies.
- **WHY** — the motivation: user need, business goal, constraint, incident,
  technical debt being paid down.

**Three states — Now, Perceived, Target**

- **Now** — what is *actually* in production / in the codebase / true
  today, grounded in citable sources.
- **Perceived** — what the org *believes* is true. Often what the wiki
  itself records. Diverges from Now when documentation is stale, when
  teams have inconsistent mental models, or when assumptions haven't been
  re-checked.
- **Target** — where we want to be: the explicit intent, the next
  milestone, the desired end state.

The gap between Now and Target is the work; the gap between Now and
Perceived is the *risk*. Both belong on the page.

## The three layers

1. **Raw sources** (`sources/`, sibling repos under
   `$BRAIN_PROJECTS_ROOT`, external planning tools) — immutable. Never
   rewrite them. When you ingest something external, snapshot a copy
   into `sources/` so the synthesis above it has a stable reference.
2. **The wiki** (`wiki/`) — markdown pages you own, plus `wiki/index.md` as
   the catalog. Cross-linked. Every non-trivial claim cites a source.
3. **The schema** — this file. The rules.

**The wiki is a derived view; never re-ingest it as a source.** Synthesis
written into `wiki/` does not get fed back through `/in` as if it were
raw material. This rule prevents the closed-loop poisoning failure mode
where LLM-authored summaries gradually replace originals in retrieval.
Citations always resolve back through `wiki/` to `sources/` or sibling
repos, not to other `wiki/` pages.

## Repository layout

```
brain/
├── README.md           # human intro
├── AGENTS.md           # this file (CLAUDE.md → AGENTS.md)
├── brain.config.yml    # per-organisation config (org name, repo registry)
├── .claude/            # slash commands, skills, settings, personas
├── sources/            # raw immutable inputs
├── wiki/               # synthesis layer
├── log/                # operations log
├── tools/              # brain.py CLI, sync, hooks, templates
└── ui/                 # purpose-built Astro app: briefing + corpus + Pagefind (src/content/docs symlinked to ../wiki)
```

## The three levels — brain, org, repo

| Level    | Lives in       | Examples                                              |
|----------|----------------|-------------------------------------------------------|
| `brain`  | `wiki/brain/`  | Brain self-tracking: roadmap, schema decisions, UI.   |
| `org`    | `wiki/org/`    | Way of working, onboarding, cross-team decisions.     |
| `<repo>` | `wiki/<repo>/` | One shelf per active repo in `brain.config.yml`.      |

Org-level pages are the bridge: an organisation-level decision (like
adopting Shape Up cycles) belongs in `wiki/org/`, not buried in one
repo. The `affects:` frontmatter field makes the propagation visible
from the repo side.

## Wiki structure — per-repo, layered

Each *active* repo has its own directory under `wiki/`, structured in
three layers: **permanent** (slow-changing knowledge), **state**
(where we were / are / want to be), and **trail** (volatile ADRs and
PRDs that accumulate over time).

```
wiki/<repo>/
├── index.md            # navigation hub
├── permanent/          # durable understanding
│   ├── purpose.md            # what this repo exists for
│   ├── architecture.md       # structural shape, components, principles
│   ├── conventions.md        # how code is written here
│   ├── interfaces.md         # external contracts (HTTP / events / SDK)
│   ├── constraints.md        # what cannot be deleted or violated, and why
│   ├── implementation-memory.md  # lessons encoded in the runtime (timeouts, retries, workarounds)
│   └── domain.md             # vocabulary, entities, concepts
├── state.md            # past / now / perceived / target
├── topics/             # running discussion threads — kind: topic (graduate → adrs/prds when commitment-class)
├── pitches/            # pre-bet Shape Up pitches — kind: pitch (graduate → epics/prds on a bet)
├── adrs/               # human-approved decision records — kind: decision
├── prds/               # human-approved (post-bet) initiatives — kind: initiative
└── ai-suggestions/     # agent-authored suggestions — never co-mingled with the above
    ├── adrs/           # `ai_suggestion: true` ADR drafts for human review
    └── prds/           # `ai_suggestion: true` PRD drafts for human review
```

Reading the permanent layer tells you *what the repo is*; `state.md`
tells you *where it's going*; walking adrs/ and prds/ tells you *how
it got here*. The `ai-suggestions/` shelf is a *parking lot* for
agent-authored proposals that haven't passed human review — see
§ Governance > `ai_suggestion`.

### state.md sections

`kind: reference`, with five fixed sections (in order):

- `## Cross-level context` — org-level pages whose `affects:` includes
  this repo. The reverse field is auto-computed in `pages.json`.
- `## Past` — curated narrative; PRD summaries graduate here when they
  ship.
- `## Now` — what is *actually* true, with citable sources.
- `## Perceived` — what the org appears to *believe* (gap = risk).
- `## Target` — next-90-days view + longer horizon.

### Permanent layer is structure-emergent

Start with `purpose.md` + `architecture.md`. Add the others
(`conventions.md`, `interfaces.md`, `constraints.md`,
`implementation-memory.md`, `domain.md`) when content earns them.
The two regenerative pages (per the Phoenix-Architecture ingest,
`wiki/org/methodology/regenerative-software.md`): **constraints.md**
is the architectural-primitives registry — the invariants, contracts,
and evaluations that must survive any regeneration ("what you can't
delete, and why"); **implementation-memory.md** catalogues the
lessons the running system encodes that were never written down —
each timeout, retry policy, validation, and workaround with the
incident or constraint that put it there. Both make a codebase
regenerable: an agent rebuilding a component reads them first. **Promote `permanent/<topic>.md` → `permanent/<topic>/index.md`
+ specialised sub-aspect pages** once 2+ specialisations exist. Don't
promote preemptively.

### ADR / PRD filenames

`<slug>.md` — kebab-case, ≤ 6 words, no numeric prefix. Ordering
comes from `updated:` and the chronological `## ADRs` / `## PRDs`
lists in the repo's `index.md`, never from the filename.

### Routing ingested content to the right shelf

When `/in <source>` lands content, `wiki-ingest` picks the shelf based
on what the content *is*. **`/in` never writes to `prds/` or `adrs/`
directly** — those are populated exclusively by `/shape`.

| Content shape                                                       | Shelf / route                                          |
|---------------------------------------------------------------------|--------------------------------------------------------|
| Code-shape facts (stack, modules, public surface)                   | `wiki/<repo>/permanent/architecture.md` (edit)         |
| External contracts (HTTP / events / jobs / SDK surfaces)            | `wiki/<repo>/permanent/interfaces.md` (edit)           |
| Style + pattern observations                                        | `wiki/<repo>/permanent/conventions.md` (edit)          |
| Domain vocabulary / entities / concepts                             | `wiki/<repo>/permanent/domain.md` (edit / promote)     |
| "What's true today" observation; new shipped capability             | `wiki/<repo>/state.md` § Now (edit)                    |
| Open question / ongoing discussion / positions being traded         | `wiki/<scope>/topics/<slug>.md` (create or append a dated entry) |
| Runtime lesson spotted in code (timeout, retry, workaround + why)   | `wiki/<repo>/permanent/implementation-memory.md` (edit)|
| Invariant / non-negotiable contract / evaluation-class asset        | `wiki/<repo>/permanent/constraints.md` (edit)          |
| New gap / risk surfaced (Now-vs-Perceived divergence)               | `wiki/<repo>/state.md` § Perceived (edit)              |
| Future intent / strategic shift                                     | `wiki/<repo>/state.md` § Target (edit)                 |
| Planning-tool **pitch / RFC** targeting a repo (forward-looking)    | Hand off to `/shape <repo>` (forward mode)             |
| Planning-tool **decision / past ADR** targeting a repo              | Hand off to `/shape <repo> --record` (ADR-only)        |
| Repo-detected pre-existing decision (e.g. "X chosen over Y")        | Hand off to `/shape <repo> --record`                   |
| Cross-repo process / methodology (Shape Up, onboarding)             | `wiki/org/`                                            |
| Customer-feedback insights                                          | `wiki/insights/` (cross-cutting; via `/feedback`)      |
| Playthrough finding (synthetic-user friction, via `/playthrough`)  | `wiki/insights/` at `confidence: low` — capped until a human confirms; transcript at `sources/playthroughs/` |
| Brain-self meta                                                     | `wiki/brain/`                                          |

**Default to editing existing pages.** New pages are an exception,
mostly reserved for the `/shape`-authored trail under `adrs/` and
`prds/`. Everything else is edit-in-place.

### Shape — universal authoring path for pitches, ADRs and PRDs

`/shape` is the *only* skill that writes pitch/ADR/PRD files. The
**`--pitch` mode** produces a pre-bet `wiki/<scope>/pitches/<slug>.md`;
the forward and record-existing modes below produce post-bet
PRD/ADR pairs. **Output path is determined by two orthogonal axes —
review status and scope**:

- **Review status** (suggestion vs. human-approved): a human
  reviewing → iterating → approving lands the artifact in the
  `{adrs,prds}/` shelf; an agent-authored run without human
  review lands in `ai-suggestions/{adrs,prds}/` with
  `ai_suggestion: true` + banner.
- **Scope** (per-repo / org / brain): determines the parent
  directory — `wiki/<repo>/`, `wiki/org/`, or `wiki/brain/`.
  See § Governance > `ai_suggestion` > Picking the right scope.

`/shape` has two **modes**, orthogonal to both path axes:

| Mode                | Trigger                                                                    | Output (human-supervised)                           | Output (agent-authored AI-suggestion)                                             |
|---------------------|----------------------------------------------------------------------------|------------------------------------------------------|------------------------------------------------------------------------------------|
| **Forward** (default)  | `/shape <scope> <pitch>` or `/shape <scope> --from-notion <url>` (where `<scope>` is `<repo>` / `org` / `brain`) | `<scope>/prds/<slug>.md` + `<scope>/adrs/<slug>.md` | `<scope>/ai-suggestions/prds/<slug>.md` + `<scope>/ai-suggestions/adrs/<slug>.md` |
| **Record-existing** | `/shape <scope> --record <description>` (or invoked by `wiki-ingest` when it spots a pre-existing decision) | `<scope>/adrs/<slug>.md` only                        | `<scope>/ai-suggestions/adrs/<slug>.md` only                                       |

Forward mode is *future*; record-existing mode is *past*. Either
mode can produce either authority level at any scope; the path
tells you which.

**Pitches are pre-bet; PRDs/epics/ADRs are post-bet.** A `pitch` is
the shaped proposal *before* a betting decision: it frames a
problem, sets an appetite, and may sketch the solution — including
engineering/architecture shape — at deliberately rough fat-marker
fidelity (the one kind allowed to do so; epics forbid engineering
bets, PRDs avoid dictating *how*). The lifecycle is **pitch → bet →
committed work**: a pitch the team bets on graduates into an
**epic + children** (umbrella scale) or a **PRD + ADR(s)** (single
scale); mark the graduated pitch `status: superseded` with
`superseded_by:` pointing at what it became. Un-bet pitches sit at
`status: draft` (and are swept by `/groom` like other stale drafts).

**Graduation** (suggestion → human-approved) is a separate PR
that moves the file out of `ai-suggestions/`, drops the
`ai_suggestion: true` flag, and reshapes language from
inference-mode to direct-mode. See § Governance >
`ai_suggestion` > Graduation. Re-scoping is allowed during
graduation if the human decides the suggestion belongs at a
different scope.

### Reserved subfolders

Tooling-output folders at the wiki root, prefixed with `_` so
lint and orphan checks skip them:

- `wiki/_overlaps/` — output of `/overlap`.
- `wiki/_archive/` — superseded pages, kept for history.
- `wiki/_views/` — auto-generated indices (`brain.py views`).
- `wiki/_state/` — operational state for tooling (e.g.
  `sync-cursors.json`); managed by `brain.py`, not authored by
  hand.

Reserved sub-folder for agent-authored draft-tier artifacts,
one per scope:

- `wiki/<repo>/ai-suggestions/{adrs,prds}/` — per-repo
  agent-authored ADR/PRD suggestions awaiting human review.
- `wiki/org/ai-suggestions/{adrs,prds}/` — org-level
  agent-authored ADR/PRD suggestions.
- `wiki/brain/ai-suggestions/{adrs,prds}/` — brain-meta
  agent-authored ADR/PRD suggestions.

See § Governance > `ai_suggestion` for the full convention.
Empty folders are not created preemptively at any scope.

The aggregated catalogue across all scopes lives in the
auto-generated `wiki/_views/ai-suggestions.md` view (emitted by
`brain.py views`).

### Active scope

The repo registry lives in **`brain.config.yml`** (`active_repos:` +
`archived_repos:`). The validator, the MCP server, `/shape`'s scope
check, and `tools/sync-siblings.sh` all read it. When a repo joins
active scope: add it to `brain.config.yml`, create `wiki/<repo>/`
with `index.md` (+ `permanent/` + `state.md` as content earns them),
and note the promotion in the audit log. Archived repos move their
shelf to `wiki/_archive/<repo>.md` and their registry entry to
`archived_repos:`.

ADRs and PRDs are not imported; the agent (PM / Tech Lead / Developer
roles in `.claude/personas/agents/`) authors and maintains them via
`/shape`. Each ADR / PRD lists in its repo's `index.md` (one line).

## Page kinds

Set `kind:` in frontmatter. The kind determines the expected structure.

| Kind         | Purpose                                              | Required sections                                  |
|--------------|------------------------------------------------------|----------------------------------------------------|
| `reference`  | How a thing *is* — repo, system, stack, convention.  | None beyond a short summary.                       |
| `pitch`      | A Shape Up pitch — a shaped, **pre-bet** proposal that may sketch the solution (incl. architecture) at fat-marker fidelity. Lives at `wiki/<scope>/pitches/`. | `## Problem`, `## Appetite`, `## Solution`, `## Rabbit holes`, `## No-gos`. |
| `initiative` | Active piece of **post-bet** (committed) work, product or technical. | `## What`, `## How`, `## Why`, `## Now`, `## Perceived`, `## Target`. |
| `decision`   | A specific decision (ADR-style).                     | `## What`, `## Why`, `## How`, `## Alternatives`, `## Consequences` — or Nygard's `## Context`, `## Alternatives`, `## Consequences`. |
| `entity`     | A person, team, division, product, customer.         | None beyond a short profile.                       |
| `meta`       | About the brain itself.                              | Free-form.                                         |
| `overlap`    | An overlap report (lives under `wiki/_overlaps/`).   | `## Items`, `## Overlap`, `## Recommendation`.     |
| `insight`    | A pattern derived from user feedback / data.         | `## Pattern`, `## Evidence`, `## Affected personas`, `## Implications`, `## Status`. |
| `epic`       | Umbrella over multi-PRD/ADR work.                    | `## Objective`, `## Background`, `## Affected personas`, `## Scope`, `## No-gos`, `## Children`, `## Success metrics`. |
| `idea`       | Raw scratchpad / "potentially useful" content.       | `## What`, `## Why interesting`, `## Maturity`.    |
| `topic`      | A running discussion thread on one question — decisions-in-the-making, below the ADR ceremony threshold. Lives at `wiki/<scope>/topics/`. Provenance over diffs: the dated discussion trail is the record; the Outcome links what it graduated into. | `## Question`, `## Discussion`, `## Outcome`. |

Reference pages don't need Now/Perceived/Target. Initiative and
decision pages do. Insights graduate into initiatives once a team
commits to acting — set the insight's `status: superseded` and
`superseded_by: <initiative>.md`.

## Core operations

Slash commands. Each command's protocol lives in the matching skill
file under `.claude/skills/<skill>/SKILL.md` — those are the
authoritative copy.

| Command              | Purpose                                                                                 | Routes to                                                |
|----------------------|-----------------------------------------------------------------------------------------|----------------------------------------------------------|
| `/in <source>`       | Add something to the brain *from a known source* (path / URL).                          | `wiki-ingest`, `palace-mine`, or `feedback-ingest` (auto-routed). |
| `/capture <scope>`   | Capture in-flight signal (conversation, design discussion) — no source URL needed.      | `capture` skill. Snapshots to `sources/conversations/`. |
| `/ask <question>`    | Query the brain.                                                                        | `wiki-query` (default), `wiki-plan`, `wiki-overlap`, `wiki-coverage`. |
| `/sync`              | One-shot **mechanical** health sweep.                                                   | `sync` skill (siblings + lint + check + validate + views + log rotation). |
| `/tend [<budget>]`   | Digest the inbox — the queue of pending synthesis work accumulated at `wiki/_state/inbox/` by the deterministic producers (cursor diffs, half-life crossings, link health, connector batches, operator-defined producers). Budget bounds the sweep: item count, time-box, kind, or a single id. The in-session half of queue-and-tend; never runs on a schedule. | `tend` skill. |
| `/groom`             | Periodic **judgement** sweep — knowledge GC.                                            | `groom` skill (confidence demotion, insight decay, supersede→archive). |
| `/playthrough [<persona> [<scenario>]]` | Walk the product as a user persona — **real execution, never simulation**. Transcript snapshots to `sources/playthroughs/`; decision-worthy findings become `wiki/insights/` pages at `confidence: low` (capped until a human confirms). Queued per version bump by the playthrough cursor; digested via `/tend`. | `playthrough` skill. |
| `/shape <scope> <pitch>` | Shape Up workflow: pitch → PRD → ADR → build. **Manual by default** — pauses at every load-bearing in-phase decision and lets the user pick. `--auto` to run autonomously (phase-end gates still apply). `--pitch` for a pre-bet pitch page. `--rfc` for an RFC pass between PRD and ADR. `--epic` for an umbrella `kind: epic` page (children spawn via regular forward `/shape` with `parent_epic:` linkage). | `shape` skill (chains `rfc` if `--rfc`). |
| `/continue <slug-or-PR#>` | Resume in-flight `/shape` work. Detect phase, ingest new context (PR comments / new sources), pre-push verify per § Working inside a sibling repo rules 4+5. | `continue` skill. |
| `/zoom-out <target>` | Per-work-item zoom-out brief — surface big-picture fit during deep focus. Auto-fired at `/shape` Phase 1→2 + Phase 2→3 boundaries; manual elsewhere. | `zoom-out` skill. |
| `/rfc <page>`        | Standalone RFC pass — append a multi-perspective `## RFC` section to a wiki page.       | `rfc` skill. |
| `/promote <insight>` | Graduate `kind: insight` → `kind: initiative`.                                          | `wiki-promote` (calls `brain.py promote`). |
| `/pr <summary>`      | Open a PR for current changes (agents never push to `main` directly).                   | `pr` skill. |
| `/review <PR#>`      | Review and auto-merge a PR after every guardrail passes.                                | `review` skill. |
| `/spawn <slug> [--target <repo[,repo…]>]` | **Opt-in** parallel-effort spawn. Creates a brain worktree at `.claude/worktrees/<slug>/` on a fresh branch off `main`, plus parallel worktrees in named sibling repos, plus a registry record at `wiki/_state/efforts/<slug>.json`. Default brain workflow stays single-effort, single-checkout — `/spawn` is the *only* entry path to parallel efforts. | `spawn` skill. |
| `/list-efforts [<status>]` | Read-only surface for in-flight (and recent) parallel efforts.                     | `list-efforts` skill. |
| `/rebase`            | Cheap-rebase the active branch onto `origin/main`, auto-resolving `wiki/_views/` conflicts via deterministic regen. Pauses on non-views conflicts for hand resolution. Force-push is **never** chained — operator verifies the rebased commit, then pushes separately. | `rebase` skill. |

The router skills (`intake`, `ask`) announce which underlying skill
they're picking before running. Users can override routing with a
leading marker (`mine: <repo>`, `feedback: <date>`, `plan: <task>`,
etc.).

### Intent → command mapping

The end user shouldn't need to know the slash-command surface. They
talk; the agent dispatches. This table is the deterministic mapping
the agent applies on every turn:

| User signal (paraphrased)                                              | Agent invokes                                              |
|------------------------------------------------------------------------|------------------------------------------------------------|
| "let's explore X" / "pitch X" / "rough out how we'd build X" / pre-bet shaping that wants to show solution shape | `/shape <scope> --pitch <pitch>` → `wiki/<scope>/pitches/<slug>.md` (pre-bet; graduates to epic/PRD on a bet) |
| "we should add X" / "let's build X" / "I want to do X" (already bet on) | `/shape <repo> <pitch>` (forward, with RFC if `--rfc`; manual-default — agent pauses at each in-phase decision) |
| "shape this autonomously" / "decide for me" / "run it in parallel"     | `/shape <repo> <pitch> --auto` (autonomous in-phase decisions; phase-end gates still apply) |
| "this is umbrella-scale work" / "this won't fit one PRD"               | `/shape <scope> --epic <pitch>`                            |
| "let's bet on this pitch" / "graduate the pitch"                       | `/shape <scope> [--epic] <pitch-slug>` then mark the pitch `superseded` / `superseded_by:` |
| "continue X" / "keep going on X" / "address the PR comments on X"      | `/continue <slug-or-PR#>`                                  |
| "zoom out on X" / "big picture for X" / "how does X fit"               | `/zoom-out <target>`                                       |
| "what would <persona> say?" / "circulate" / "review this PRD/ADR"      | `/rfc <page>` (standalone) or `/shape --rfc` (in workflow) |
| "we already chose X" / "we picked X over Y" / "this is how it works"   | `/shape <repo> --record <description>`                     |
| "what do we know about X?" / "where do we...?" / "have we discussed?"  | `/ask <question>`                                          |
| "outline / plan the work for X"                                        | `/ask plan: <task>`                                         |
| "any overlap on X?" / "anyone else doing X?"                           | `/ask overlap: <topic>`                                     |
| "how much do we know about repo X?"                                    | `/ask coverage: <repo>`                                     |
| Sharing context, design discussion, customer interaction               | `/capture <scope>` (scope: `brain` / `org` / `<repo>`)      |
| "let's discuss X" / "what do we think about X" / "add to the X discussion" / an unresolved question worth a trail | `/capture` → `wiki/<scope>/topics/<slug>.md` (new or dated append) |
| "this looks stale / outdated"                                          | `/groom`                                                    |
| "walk the product as a user" / "test as a persona" / "playthrough"     | `/playthrough <persona> [<scenario>]`                       |
| "is the brain healthy?" / "sweep please"                               | `/sync`                                                     |
| "tend the brain" / "do the inbox" / "digest the queue" / "catch the brain up" | `/tend [<budget>]`                                    |
| "this insight should become a project"                                 | `/promote <insight>`                                        |
| "ingest this URL / repo / file"                                        | `/in <source>`                                              |
| "review / merge this PR"                                               | `/review <PR#>`                                             |
| "in parallel" / "parallel effort" / "spawn" / "fresh worktree"         | `/spawn <slug> [--target <repo[,repo…]>]`                  |
| "what's in flight" / "list parallel work" / "show spawned efforts"     | `/list-efforts`                                             |
| "rebase me" / "another effort merged first" / "auto-resolve views"     | `/rebase`                                                   |

If two intents seem to match, the agent **asks one short
clarifying question** rather than guessing. If no slash command
seems to fit, the agent treats it as a `/capture` and routes the
content into the right brain shelves.

## Agent teams — fan-out and parallelism

The brain runs three levels of agent. The **parent session**
coordinates: it talks to the user, dispatches efforts, watches
their progress, and is itself parallel-first in tool-call
discipline — multiple Bash calls in one message when the calls
are independent, multiple Read calls in one message when reading
several known files, multiple Agent dispatches in one message
when the dispatched runs are independent. **Effort owners** run
spawned efforts end-to-end in the background — every `/spawn`
ships with a mandatory owner subagent (opt-out via `--no-owner`)
that drives the effort from deepdive through merged PR using the
template at `tools/templates/owner-subagent-prompt.md`.
**Helpers** fan out *within* an effort for parallel-shape
subtasks — multiple files to read, multiple subtasks to
evaluate, multiple targets to inspect.

The fan-out **mechanism differs by level**. The parent session
can dispatch background owner subagents (multiple Agent calls in
one message when independent). Owner subagents **cannot
recursively dispatch helper subagents** — the Agent-dispatch tool
is parent-session-only in this environment. What owners *can*
do — and must, when work has parallel shape — is fan out via
**parallel tool calls in a single message**: multiple `Read`
calls in one message when reading several known files, multiple
`Bash` calls in one message when the calls are independent,
multiple `WebFetch` calls in one message when hitting independent
URLs. The rule's *intent* (parallel-first work at every level)
survives unchanged; only the *mechanism* shifts from "dispatch
helpers" to "concurrent tool calls" once you're inside an owner
subagent.

Parallel-first is the default tilt at every level. Series is
the exception — taken when a later call genuinely depends on an
earlier call's output, or when the work is small enough that
fan-out overhead exceeds the parallelism gain. Serial work
warrants explicit justification in the moment (a one-line
*"reading X first to know which Y to fetch"* note in the agent's
narration), so future agents inheriting the area can tell
*deliberate serial* from *missed fan-out*. The opt-out flag on
`/spawn` (`--no-owner`) is the only documented way to suppress
the dispatch layer; helper fan-out has no flag — it's an
in-session judgement call about whether the subtasks are
genuinely independent.

## Conventions

- **Filenames:** kebab-case, `.md`.
- **Frontmatter:** every wiki page starts with YAML:
  ```yaml
  ---
  title: <human title>
  kind: reference | initiative | decision | entity | meta | overlap | insight | epic | idea | pitch
  status: draft | living | superseded | archived
  updated: YYYY-MM-DD
  # Optional but recommended:
  team: <team name>
  division: <division name>
  repos:                       # repos this page is *about*
    - <repo>
  affects:                     # repos whose work this page changes
    - <repo>
  depends_on:                  # other wiki pages this one builds on
    - <other-page.md>
  confidence: high | medium | low
  supersedes: <other-page.md>
  superseded_by: <newer-page.md>
  sources:
    - sources/...
    - ~/projects/<repo>/<path>
    - https://...
  ---
  ```
  Only `title`, `kind`, `status`, `updated`, and `sources` are required.
- **`summary:`** — optional executive summary (one to three
  sentences, ≤600 chars), maintained by the agent whenever content
  changes. The briefing and card components render it; humans read
  summaries, agents read bodies. The validator warns when a
  card-rendered kind (pitch / initiative / decision / epic / topic /
  insight / idea) at `living`/`accepted` lacks one; `/groom` checks
  drift.
- **Cross-links:** relative markdown links between wiki pages.
- **Dates:** absolute (`2026-04-29`), never relative.
- **Voice:** present tense, declarative. Mark uncertainty explicitly with
  *"(unverified, YYYY-MM-DD)"* rather than hedging prose.
- **Don't invent.** If a fact is not in a source you can cite, either go
  find one or write *"(unknown — needs source)"*.
- **Supersede, don't silently overwrite.** When a synthesis is replaced,
  set `status: superseded` on the old page and `supersedes:` on the new
  one.
- **Shipped PRDs use `superseded` + `superseded_by:` pointing at
  `state.md § Past`.** When a PRD's implementation work ships, mark
  the PRD `status: superseded` and set `superseded_by:` to point at
  the repo's `state.md` (the graduation entry within § Past is the
  actual record). The sibling ADR is referenced from the graduation
  entry, **not** as the supersedes target.
- **ADR amendments — amend in place when direction is unchanged;
  supersede when direction changes.** When an ADR's underlying
  decision evolves, distinguish *amendment* (the direction is
  unchanged; specifics like thresholds, scopes, rollout shape evolve
  — append a `## Amendments` section to the existing ADR, bump
  `updated:`) from *replacement* (the direction itself changes —
  author a new ADR with a fresh slug, set `supersedes:` on the new
  one, flip the old to `status: superseded` with `superseded_by:`).
- **Dependencies are one-way; reverse edges are computed.** Set
  `depends_on:` on the consumer; `consumed_by:` is auto-populated by
  `brain.py views` in `pages.json` — don't author it by hand.
- **`affects:` vs `repos:`.** `repos:` says *this page describes that
  repo*. `affects:` says *this page's content has consequences for
  that repo*. The reverse field `affected_by:` is auto-populated by
  `brain.py views`.

## Scale conventions

- **Page size discipline.** Aim for pages under ~500 lines. Past that,
  split: extract a sub-topic to its own page and link from the parent.
- **Folder emergence trigger.** Promote `wiki/<page>.md` →
  `wiki/<topic>/<index-of-topic>.md` once a topic has *three or more*
  pages or a clear sub-tree.
- **Confidence policy.**
  - `confidence: high` — every load-bearing claim cites a primary
    source you've read in the last ~30 days.
  - `confidence: medium` — citations exist, but some are stale, or the
    synthesis required interpretation.
  - `confidence: low` — partly inferred, not yet validated against
    sources, or the source itself is hearsay. **Default for new pages.**
- **Stale-date handling.** A page's `updated:` date is bumped only
  when *content* changed, not when only frontmatter changed.
- **Templates.** Start new pages from `tools/templates/<kind>.md`.
- **Validator.** `python tools/brain.py validate | stats | views`
  before commits at scale.

## Working with mempalace

mempalace stores verbatim conversation/source text and retrieves it
with semantic search. The palace lives at `~/.mempalace/palace/`
(machine-global). Use it when you need an exact passage, are
grounding a synthesis in original wording, are running `/overlap` and
need candidate pairs, or are searching across past conversations.

The wiki is the *output*; mempalace is part of the *retrieval*. Cite
both: the wiki page proves a claim, mempalace gives you the verbatim
passage.

## Pulling from external planning sources (e.g. Notion)

When the organisation keeps its product / planning / decision
canon in an external tool (Notion, Confluence, a Google Drive),
that tool is the brain's primary external read surface. Two hard
rules apply regardless of vendor:

### External planning sources are read-only

**Never write to the external tool from the brain.** Reads are
encouraged; creates / updates / comments / moves are forbidden. A
write could clobber human edits, mis-attribute provenance, or
trigger notifications.

Enforcement is layered: every known Notion write tool is on the
deny list in `.claude/settings.json`. Calls fail at the
permission layer before agent intent matters. If your org uses a
different planning tool over MCP, extend the deny list with that
vendor's write tools before the first ingest.

If you scope the ingest surface (e.g. only one namespace of the
planning tool is in bounds), record the scope here and verify a
page is in scope before snapshotting it.

### Snapshot before ingest

Live retrieval gives you the *current* page; the brain's source layer
must be *immutable*. Before `wiki-ingest` writes a wiki page from an
external planning source, snapshot it — for Notion,
`tools/notion-export.py <url-or-id>` writes
`sources/notion/<slug>--<shortid>.md` with frontmatter. Cite the
snapshot path in the wiki page's `sources:`. The live URL can also be
cited; both are useful.

## Sibling repos on this machine

Treat as raw sources; do not modify them from this repo (except
under § Working inside a sibling repo, below).

The sibling-repo root is configurable via the
`BRAIN_PROJECTS_ROOT` environment variable; the default is
`~/projects/`. The registry of which repos are active lives in
`brain.config.yml` — see § Active scope.

Active repos get `wiki/<repo>/` with `index.md` + `permanent/` +
`state.md` + `adrs/` + `prds/`. Archived repos live under
`wiki/_archive/<repo>.md` and are excluded from the active corpus.

### Sibling-repo handling — main first, latest, then read

Before processing any sibling repo: land on the canonical state.

1. `git fetch --all` to pull remote refs.
2. Then:
   - On `main`/`master` with clean tree → `git pull --ff-only`.
   - On a non-main branch → **leave it alone**; report; don't switch.
   - With uncommitted changes → **leave it alone**; report; don't pull.

`tools/sync-siblings.sh` enforces this. Skill protocols that read a
sibling repo (`wiki-ingest`, `palace-mine`, `shape --from-source`)
must call into it or replicate the handling.

When the rule skips a repo, the brain still processes — but flags the
snapshot as *"(read from feature branch '<name>'; may not match
production)"* and marks `confidence: low` if the divergence looks
meaningful.

### Working inside a sibling repo

The previous subsection covers when an agent is *reading* a sibling
repo to ingest content into the brain. This subsection covers the
other mode: when an agent is *editing* code in a sibling repo to
deliver a brain-authored ADR / PRD's build phase, or to fix a bug,
or any other direct work in that codebase. Five rules.

1. **The sibling repo's conventions win.** Read its `AGENTS.md` /
   `CLAUDE.md` (and any docs they point to) before editing. Follow
   that repo's naming, file layout, dependency shape, test idioms,
   and lint rules. The brain's authoring conventions (kebab-case
   page slugs, frontmatter shape, present-tense voice) apply to
   brain content only — never to sibling-repo code.

2. **No commentary comments above methods.** Method names should
   carry the meaning. If a method needs a paragraph above it to
   explain what it does, the method name is wrong — fix the name,
   not the comment. Comments are reserved for *why* an
   implementation is non-obvious: a hidden invariant, a workaround
   for a specific bug, behaviour that would surprise a careful
   reader from the code alone. The default the agent commits with
   is *zero* comments above methods; comments earn their place.

3. **Defer to the codebase on implementation shape.** The brain's
   ADRs and PRDs name *what* and *why*. The actual method names,
   class assignments, indirection layers, and refactor tactics are
   the codebase's call — read the surrounding code before
   extrapolating from the brain page. If the implementation shape
   that emerges during build is better than the ADR's sketched
   shape, *the implementation wins*. Update the ADR's
   `## Build notes` with the refinement and *why* it's structurally
   better, so the next ADR doesn't over-specify in the same
   direction.

4. **Reproduce CI gates locally before pushing.** Sibling repos
   have CI checks that may skip drafts, run late after long CI
   jobs, or otherwise hide failures from the agent's
   push-and-watch loop. When a check exists *and the agent is
   changing code it gates*, run the check locally before pushing
   rather than rely on remote signal. Per-repo invocations live on
   the repo's `wiki/<repo>/permanent/conventions.md` (or its
   testing subsection) — catalogue them as you encounter them so
   future agent runs reuse them without re-discovering.

5. **Verify pattern fit before pushing.** Active counterpart to
   rule 3. Brain-authored work (PRDs, ADRs, skill plans) names
   *what* and *why*; the *how* should reuse the patterns the
   target repo already uses for similar problems. Before pushing,
   scan adjacent code for prior art: how do existing files solve
   similar shapes? Is there an established class hierarchy,
   helper convention, service layer, formatter sibling, job-class
   pattern, component style, or configuration mechanism this work
   would naturally extend? **Most of the time the answer is yes**
   — reuse the pattern, the codebase has already paid the design
   cost. Rare divergent cases (the existing pattern genuinely
   doesn't fit the new need, or the new need exposes a real flaw
   in the established pattern) require explicit justification
   recorded in the ADR's `## Build notes` or the PR body, so the
   next agent inheriting the area knows *why* a parallel pattern
   was warranted instead of an extension of the existing one.

These rules apply equally to autonomous agent runs and to
human-supervised ones. The brain agent operating in any sibling
repo is a guest in that codebase; the host repo's conventions are
the contract.

### Sibling-repo sync cursors — incremental ingest

The brain records a per-sibling-repo "last sync cursor" at
`wiki/_state/sync-cursors.json`. Each entry is a commit SHA + branch
+ timestamp + tree state + scope + audit reference. The cursor is
the brain's record of *"what sibling-repo state did we last
ingest?"* — `wiki-ingest` consults it to do incremental ingests
instead of re-walking whole sibling trees on every pass.

Mechanics (managed by `tools/brain.py sync-cursor`):

- `brain.py sync-cursor get [<repo>]` — print cursor(s).
- `brain.py sync-cursor set <repo>` — advance cursor to current
  sibling `HEAD`. Refuses unless the sibling-repo-handling rule
  passes (on main/master, clean tree). `--force` overrides.
- `brain.py sync-cursor diff <repo>` — `git diff <cursor>..HEAD
  --name-only` against the sibling checkout. Returns the changed-
  paths list a skill walks. If the cursor is absent (first-pass
  ingest), prints all tracked files + a stderr note. If the
  cursor SHA isn't reachable (rebase / force-push), falls back
  to a full listing with a stderr warning.

Skill protocol for sibling-repo ingests (`wiki-ingest`):

1. Run sibling-repo handling first (see § Sibling-repo handling
   above).
2. **Consult the cursor** — `brain.py sync-cursor diff <repo>` to
   get the changed-paths list. Walk only those paths.
3. After successful synthesis + audit log entry: `brain.py
   sync-cursor set <repo> --synced-by "PR #<num>"` advances the
   cursor. If the sibling was on a feature branch or dirty
   (sibling-repo handling skipped advancing in step 1), don't
   advance the cursor; surface the divergence in the log line so
   the next ingest re-attempts.

Path-scoped ad-hoc ingests (e.g. *"just walk one subtree"*) **do
not** advance the cursor — only full-tree passes do. The cursor
records the `scope:` field for honesty.

## Reach surface — search, sibling-repo install, MCP, init

Five tools expose the brain to consumers beyond the Astro UI.
The first three are read-only over the synthesis layer; the
fourth scaffolds an empty brain shell for new adopters; the
fifth is a thin shell wrapper. The brain is never mutated
through any of these.

### `brain.py search` — hybrid keyword + source-aware ranking

```bash
python3 tools/brain.py search '<query>' [--top N] [--repo X] [--kind decision] [--json]
```

Combines keyword scoring (title 3× / body 1×) with source-factor
(cross-product 1.6× / org 1.5× / permanent 1.4× / decisions 1.2× /
ai-suggestions 0.75× / archive 0.3×) and confidence-tier (high 1.3× /
medium 1.0× / low 0.85×) multipliers. Excludes superseded/archived
unless `--include-superseded`. Returns ranked pages with title, kind,
confidence, score, excerpt — same shape consumed by the MCP server
and the sibling-repo hook.

### `brain.py install-sibling <repo>` — sibling-repo brain installer

```bash
python3 tools/brain.py install-sibling <repo>    # install
python3 tools/brain.py install-sibling <repo> --uninstall
python3 tools/brain.py install-sibling <repo> --dry-run
```

Idempotently installs a `<!-- brain:managed:* -->`-fenced block in
the sibling's `CLAUDE.md` (or `AGENTS.md`), drops a `brain-hook.sh`
PreToolUse hook into the *sibling repo's* `.claude/` that surfaces
relevant brain pages before `Grep`/`Glob`/`Read` tool calls, and
registers the hook in the sibling's `.claude/settings.json`.
Operator content outside the sentinels is never modified.

### `tools/brain-mcp.py` — stdio MCP server

```bash
claude mcp add brain --scope user -- python3 <path-to-brain>/tools/brain-mcp.py
```

Exposes read-only tools (`brain_search`, `brain_get_page`,
`brain_stats`, `brain_overlaps`, `brain_efforts`,
`brain_active_repos`, `brain_status`, `brain_verify_claims`) over
the Model Context Protocol. Any MCP-aware client can register the
server and query the brain natively. The MCP wraps `brain.py`
rather than duplicating its logic; improvements to `brain.py` flow
through automatically. Auto-loaded for this repo via `.mcp.json` +
`enabledMcpjsonServers: ["brain"]`.

**HTTP transport**: `python3 tools/brain-mcp.py --http [--port 8766]`
serves streamable-HTTP (stateless: POST /mcp, JSON responses,
localhost-bound, origin-checked). **Serving mode**
(`BRAIN_SERVING=1`): ai-suggestions are excluded from search and
page reads (the path is the signal), and every tool call is
appended to `log/queries.log` (git-ignored, append-only). A
deployment for people outside the product runs `--http` with
`BRAIN_SERVING=1` against a read-only checkout, behind an
identity-aware proxy — the process itself has no auth and no write
tools. **Hosted tier** (`BRAIN_HOSTED=1`): the authenticated, writable,
multi-agent counterpart to read-only serving. Agents hold per-agent
HMAC keys (`agent-key issue|rotate|revoke`); on this tier every
`/api/act` write is a signed event on the append-only stream under
`wiki/_state/events` (authored by the authenticated agent), and
`GET /api/events?since=<seq>` is the authenticated read. The auth
boundary rejects forged appends at write time and drops tampered lines
on read. **Owner-subscription wake**: an agent `subscribe`s to a
ref-pattern with a wake URL (a signed subscribe event); a matching
append POSTs a signed hint (seq + ref, no payload) to the owner through
an SSRF guard, capped per event, with the per-agent cursor as the
at-least-once backstop — the wake never invokes the agent. Off by
default — local-first is byte-for-byte unchanged, with no keyring, no
stream, and no subscriptions. **Datasette pilot**:
`tools/serve-datasette.sh` serves the derived index in immutable mode
with canned queries (`tools/datasette/metadata.yml`) — the
faceted-browse/SQL/JSON tier of the serving plane.

### `brain.py init <path>` — scaffold an empty brain shell

```bash
python3 tools/brain.py init ~/projects/my-org-brain --org "My Org"
BRAIN_DIR=~/projects/my-org-brain python3 tools/brain.py validate
```

Scaffolds a fresh brain shell at `<path>`: kernel-flavoured
AGENTS.md, `wiki/` skeleton with the contract sections, empty
`sources/`, an empty `log/log.md`. Runs `brain.py views` once so
the home links resolve. The new shell is `BRAIN_DIR`-aware — all
`brain.py` commands honour `$BRAIN_DIR` so the existing tools work
against the new shell without copying `tools/` over.

### `brain.py index` / `query` / `views/` specs — composable views

```bash
python3 tools/brain.py index [--schema]   # rebuild the derived index / print schema
python3 tools/brain.py query '<sql>'      # read-only SQL over the index
```

Per `wiki/brain/adrs/sql-views-over-derived-index.md`: a disposable,
gitignored SQLite index (`wiki/_views/index.db`) is rebuilt from the
files on every `views` run — pages + computed edges, links, inbox,
flattened state, connector snapshots, FTS5 over page and snapshot
text. **View specs** are YAML files in `views/` (blocks: raw `sql:`
or shorthands `pages:` / `state:` / `inbox:` that compile to SQL);
each renders to `wiki/_views/custom/<name>.md` on regeneration.
Example specs ship for engineer / pm / operator roles. The index is
never committed and never load-bearing — delete-and-rebuild is
always safe; consumers open read-only.

### `brain` (the app) / `install-agent` — the harness surface

```bash
brain                                  # serve + open the app
python3 tools/brain.py install-agent claude|cursor|codex|opencode [--all]
```

Per `wiki/brain/adrs/mcp-cli-surface.md`: the
app page at `/workbench` is the rendered brain under an ambient
strip (health + tend queue), auto-reloading as the wiki changes.
There is no embedded terminal or chat — the operator runs their
harness in their own terminal, wired to the brain over MCP.
`install-agent` idempotently registers the brain's MCP server per
harness from the `AGENT_TARGETS` fan-out table — JSON deep-merge or
sentinel-fenced TOML; a new harness is one row in the table. The
app page never mounts in serving mode (`BRAIN_SERVING=1`).

### `brain.py links` — link-graph health

```bash
python3 tools/brain.py links [--json]
```

Orphans (no inbound links — link or archive), hubs (most-linked;
keep freshest), dead ends (no outbound), and suggested links
(unlinked pages sharing `repos:`/`affects:`). The deterministic
input to pruning and to the deepening picker: `inbox-refresh`
queues an orphans item, and pages where **low confidence crosses
high centrality** (≥2 inbound links) become `research` inbox items
digested by `/tend` (findings snapshot to `sources/research/`).

### `brain.py setup` / `doctor` / `serve /dash` — the hands-off surface

```bash
python3 tools/brain.py setup [--org X --repos a,b --yes --dry-run]
python3 tools/brain.py doctor [--json]
python3 tools/brain.py serve      # JSON API + human ops page at /dash
brain tend [budget]               # wrapper: open the agent with /tend
brain dash                        # wrapper: serve + open localhost:8765/dash
```

`setup` is the idempotent bootstrap (env, config, pre-commit gate,
venv, timer, UI deps — each step detects "already done"); `doctor`
is the health checklist behind it (ok/warn/fail + the fixing
command; exit 1 only on fails); `/dash` renders doctor + the tend
queue + quick-start as a server-side HTML page for non-terminal
users. All three read the same `_doctor_checks()` source of truth.

### `brain.py status` — single-pane-of-glass dashboard

```bash
python3 tools/brain.py status
```

Reads every `wiki/_state/*.json` and surfaces one-line health
across corpus / security / issues / sync-cursors / in-flight
efforts / AI-suggestion backlog.

### `brain.py inbox` — the tend queue

```bash
python3 tools/brain.py inbox add --id <slug> --kind ingest|groom|research|custom \
    --summary "..." [--route "/in <source>"] [--priority high|normal|low]
python3 tools/brain.py inbox list [--json]
python3 tools/brain.py inbox summary     # one line; wired to session start
python3 tools/brain.py inbox done <id>
python3 tools/brain.py inbox ack <id>       # reviewed, no change — suppress re-add until the page changes
python3 tools/brain.py inbox pending-grades  # judged attention items awaiting a grade
```

One JSON file per item at `wiki/_state/inbox/<id>.json` — merge-safe,
committed (arrival and clearing are git-audited), idempotent on the
producer-chosen `--id`. The `inbox-refresh` schedule op reconciles
the deterministic slice (cursor diffs, half-life crossings, link
health) on every run; operator-defined producers are any script that
calls `inbox add`, registered as one more `brain-schedule.yml` entry
(template: `tools/producers/example-producer.sh`). `/tend`
digests — judging external-signal items with `inbox judge <id>
--attention needs-operator|fyi|routine --reason "..."` (in-session
only; the briefing's Needs-you band renders the verdicts, and
`inbox grade <id> --grade useful|noise` records the operator's
useful/noise calibration into `wiki/_state/attention-grades.json`).
The local timer is installed by `tools/install-timer.sh` (systemd
user timer; prints a crontab fallback). Per
`wiki/brain/adrs/queue-and-tend-inbox.md`: no LLM ever runs on the
schedule — the timer accumulates, sessions digest.

### `brain.py schedule` — declarative recurring operations

```bash
python3 tools/brain.py schedule list                    # print declared operations
python3 tools/brain.py schedule run --target <name>     # run one
python3 tools/brain.py schedule run-due                 # run every enabled op
```

Operations declared in `brain-schedule.yml`. The runner fires from
`.github/workflows/scheduled.yml` daily at 06:00 UTC; state JSON
updates auto-commit back to main.

### `tools/brain` — thin shell wrapper

```bash
ln -s <path-to-brain>/tools/brain ~/.local/bin/brain
brain stats
brain search 'authorization' --top 5
brain install-sibling --all
```

A bash wrapper that resolves the brain root (via `$BRAIN_DIR`
→ script location → `~/projects/brain`) and execs `brain.py`.
Lets sibling-repo agents and operator shells call `brain
<command>` directly without typing the full python invocation.

## Browseable UI

A production UI lives at `ui/` — a purpose-built Astro 5 app (per
`wiki/brain/adrs/human-legible-presentation-layer.md`) with
`src/content/docs` symlinked to `../../../wiki`. The root is the
**briefing**: three judgement bands (Needs you — attention verdicts,
pitches awaiting a bet, unconfirmed insights, AI drafts; In flight —
living post-bet work; On the table — open topics and ideas) over a
were/are/going orientation strip. Wiki pages render at their
existing paths with lifecycle chrome (kind/status/confidence/
appetite chips, the `summary:` lead, ai-suggestion and superseded
banners); the wiki home renders at `/home/`; Pagefind search at
`/search/`; `/dashboard/` (corpus numbers, bars, activity
sparkline), `/trail/` (the lifecycle as a timeline with supersedes
chains), and `/graph/` (the link graph as build-time SVG) round out
the read surfaces. The briefing filters by type and paginates per
band. **The interactive channel** (ADR amendment 2026-07-12): cards
and pages carry *queue* and *comment* actions that POST to the
local server's `/api/act`, which appends an inbox item
(`produced_by: ui-action`) for the next tend session — the UI's
only write surface is the inbox; the endpoint never mounts in
serving mode. **The conversation surface** (0.23.0): `/channels/`
renders every topic as a channel and each topic page grows a Thread
panel; a `post` action on `/api/act` queues a `channel_post` inbox
item (server-stamped `author`, the message fenced as untrusted data),
and the tend session replies in-thread by appending a dated topic
entry — async message-passing, never live chat, inbox-only-write
intact. Build: `npm run build` (Astro + Pagefind; details in
`ui/README.md`). **Local-first** — sharing happens via the repo
paths in `wiki/`, not a hosted URL. Mobile-native is a
non-negotiable rule for any UI iteration.

An onboarding deck at `/onboarding/` (rendered by
`ui/src/pages/onboarding.astro`) walks colleagues new to the brain
through the three missions, three layers, three levels, governance,
and slash-command surface in ~10 minutes.
