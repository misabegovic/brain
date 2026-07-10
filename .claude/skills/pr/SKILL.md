---
name: pr
description: Open a pull request from the current working changes. Creates a feature branch if you're on main, commits with a structured message, pushes, runs `gh pr create` with a body that includes Why / Affects / Sources / Restricted-paths flag. Replaces direct `git push` to main once the PR workflow is enforced. Load when the user says "pr", "open a pr", "ship", or invokes `/pr`.
---

# Open a pull request

You are working in `~/projects/brain`. The brain is a shared working
space for humans and autonomous agents. To prevent unsupervised writes
to `main`, all agent-authored changes go through a PR that is reviewed
by a *different* agent session before merging.

This skill is the author side. The reviewer side is `/review`.

## Local-first mode

If `.env` declares `LOCAL_FIRST=true`, this skill is **opt-in only**
— it fires only when the operator explicitly says "open a PR" /
"ship this" / `/pr`. Other skills (`/shape`, `/continue`, ingest
sweeps, etc.) **do not chain into `/pr`** under local-first; their
work lands as local commits per AGENTS.md § Local-first mode.

When the operator does invoke `/pr` under local-first, this skill
runs end-to-end as documented below — it's the single moment the
session flips into remote mode. After the PR opens, the next
operation reverts to local-first.

```bash
[ -f .env ] && grep -q '^LOCAL_FIRST=true$' .env && LOCAL_FIRST=1
```

If `LOCAL_FIRST=1` and the agent reached this skill *without* the
operator's explicit invocation, abort: surface the local commit log
since `origin/main` and stop. Don't push.

## Pre-flight

1. Are we already on `main`? If yes, create a feature branch:
   ```bash
   git checkout -b agent/<short-slug>-$(date -u +%Y%m%dT%H%M%S)
   ```
   Slug should be 3–6 words, kebab-case, summarising the change. The
   timestamp keeps branch names unique across concurrent agent runs.

2. Are we on a feature branch with uncommitted changes? Stage and
   commit them. If the working tree is clean and HEAD == origin/HEAD,
   abort — there's nothing to PR.

3. Are any *restricted paths* (per `AGENTS.md` § Path conventions)
   touched? Restricted paths are: `AGENTS.md`, `.claude/**`,
   `tools/**`, `railway.toml`, any `Dockerfile`, `.dockerignore`,
   `.github/**`, `ui/Dockerfile`, `ui/serve.mjs`,
   `ui/quartz.config.ts`, `ui/quartz.layout.ts`, `ui/package.json`,
   `ui/package-lock.json`. If yes, set `restricted-paths: true` in the
   PR body — it's an *informational* flag for reviewer attention, not
   a merge gate.

## Pre-flight checks before pushing

Run locally so the reviewer doesn't have to. **All three commands**
must run; CI runs the same set and will fail the PR otherwise.

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py validate
~/.local/share/mempalace-venv/bin/python3 tools/brain.py check --no-net
~/.local/share/mempalace-venv/bin/python3 tools/brain.py views
git diff --exit-code --quiet wiki/_views/    # auto-regen must be committed
```

What each guards:

- `validate` — frontmatter / required sections / references.
- `check --no-net` — every `sources:` citation resolves locally.
- `views` — regenerates `wiki/_views/` (`pages.json`,
  `by-{kind,team,repo,epic}.md`, `ai-suggestions.md`). The CI gate
  *Check views are up-to-date* re-runs `views` and fails if it
  produces *any* diff, including the date bump in `pages.json`'s
  `"generated"` field on a fresh-day run. Always re-run `views` and
  `git add wiki/_views/` before push, even when your edits are
  outside `wiki/`.

**Use the mempalace venv python**, not system `python3`. System
python lacks `tiktoken`; CI installs it. A different `tiktoken`
state produces different per-page token counts in `pages.json` and
the views-up-to-date gate flips red on the runner.

If `validate` fails, fix and recommit. If `check --no-net` flags
broken citations, that's a fail too — fix the citation or remove
the offending line. If `views` shows a diff after regen, commit it
in the same PR.

### Home-page pairing (PRs only)

CI also runs `tools/brain.py check-home-fresh` against
`origin/<base>`. If your PR edits anything under `wiki/` you must
also touch `wiki/index.md` (§ Where to find things and/or § What
changed, per
[`wiki/brain/adrs/home-content-shape.md`](../../../wiki/brain/adrs/home-content-shape.md)).
Ingests that only add files under `sources/`, or only touch
`.claude/`, `tools/`, `ui/`, `log/` etc., don't trigger this gate.

## Commit

```bash
git add <specific paths>     # avoid `git add -A` on agent runs
git commit -m "<imperative summary, ≤72 chars>"
```

If multiple coherent changes, multiple commits. If a single change
spans many files, one commit is fine.

Co-author footer (Claude Code already adds this when committing on
the agent's behalf — preserve it):

```
Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

## Push and open the PR

```bash
git push -u origin HEAD
```

Then `gh pr create` with the title (one-line summary, ≤72 chars)
and a body shaped per the rule below. **The PR body is an
executive summary, not a section-heavy long-form** — see § PR
body shape below for the binding rule, applies to every PR this
skill opens.

```bash
gh pr create --base main --title "<one-line summary>" --body "$(cat <<'EOF'
<executive-summary body — see § PR body shape below>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### PR body shape — *executive summary, not section-heavy*

PR descriptions are read at scan-speed by humans and agents.
The diff is the source of truth for *what changed*; the linked
PRD/ADR/source is the source of truth for *why*; the audit log
is the source of truth for *when*. A long PR body duplicates
all three and rots faster than any of them.

**Total length under 200 words.** Lead with one sentence
naming the change. Optional one short paragraph for context
(link the parent PR / PRD / ADR / epic / source in prose, not
in a separate `## Sources` block). One short sentence noting
restricted-paths only when applicable. Standard 🤖 footer.

**Lead with WHY and HOW in plain human language, not with a
feature/file dump.** The first sentence or two name the problem
the change solves *as a human would describe it to a stakeholder
who hadn't seen the diff* — what was broken, slow, missing, or
risky before, and what the new shape replaces it with at a
conceptual level. *Then* link the PRD/ADR/epic and (briefly)
list what landed. A reader who skims only the first paragraph
should walk away with the why and the rough shape of the how;
the full taxonomy of files and features is what the diff and
the linked PRD/ADR are for.

A useful test: read the first paragraph out loud. If it sounds
like a release-notes bullet ("This PR ships X, Y, and Z") or a
table of contents, it's wrong. If it sounds like an answer to
*"why are we doing this?"* in plain English, it's right. User
flagged this convention 2026-05-12 after an FT-prototype PR
opened with a feature dump.

**Write paragraphs as single lines — no hard-wrap mid-paragraph.**
GitHub renders the PR body source verbatim; it does not reflow
within a paragraph. If the heredoc wraps prose at 60-72 columns
the description hugs the left side of the page on wide screens.
Use one line per paragraph, blank lines as paragraph separators.
The 200-word cap is the length gate; line width is not. User
flagged this convention 2026-05-12 alongside the WHY/HOW rule
above.

**Do NOT scaffold the body with H2 sections.** No
`## Why`, `## What`, `## Affects`, `## Sources`,
`## Restricted-paths`, `## Phase-N gate`, `## Decision needed`,
`## Backlinks`, `## Smoke test`, `## Test plan`, `## Verification`.
This shape produces lengthy lab-notebook descriptions the user
has flagged as breaking convention (2026-05-07). The same rule
applies to sibling-repo PRs opened by `/shape` Phase 3 — see
that skill's Phase-3 protocol § Open a SHORT draft PR.

What to *cut*:

- Multiple H2 sections.
- Re-listing files touched (the diff shows them).
- Re-stating the ADR's Decision section (link the ADR; trust the reader).
- Lengthy "Why now" or "Background" duplicating the PRD.
- Restating Phase-1 / Phase-2 gate rules (they live in AGENTS.md).
- Smoke-test prose that reads like a lab notebook.

Example shape (Phase-1 PRD PR — paragraphs as single lines so
GitHub reflows on wide screens):

```
Phase 1 PRD for `<slug>`, the <Nth> child of the [<epic-name> epic](<github-link>). Names the load-bearing decisions, deferred to the Phase 2 ADR. Phase-1 gate per AGENTS.md § Governance — conversational approval covers the gate; CI must still pass.

Restricted-paths: false.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

If the PR genuinely warrants a *test plan* (changes the
operator must verify that CI doesn't cover) or a *rollout
note* (multi-region deploy concerns, feature-flag flip
sequencing), include it as a 2–4 line bulleted block — not
as an H2 section. Keep it tight.

Return the PR URL — but **`/pr` does not end here.** Continue with the
landing chain below.

## After opening — watch CI, hand off to `/review`

`/pr` is the author half of the landing chain. The PR is not "done"
until it lands on `main` (or, for `/shape`-shaped PRs, until a human
has been asked to approve). Stopping at PR-open leaves the work
invisible on `main` and the audit line missing from `log/log.md`.

1. **Watch CI to completion.** Use the Monitor tool (or the equivalent
   in your harness) so each check transition surfaces as a
   notification and the watch exits when every check has left
   `pending`. **Helper fan-out (parallel-first).** When this step
   has parallel shape — multiple PRs to watch concurrently,
   multiple checks to diagnose in parallel, multiple sibling-repo
   PRs paired with this brain PR — default to fanning out helper
   subagents in a single message rather than serial tool calls.
   Per [`wiki/brain/adrs/parallel-execution-agent-teams.md`](../../../wiki/brain/adrs/parallel-execution-agent-teams.md).
   The minimal poll body:

   ```bash
   prev=""
   while true; do
     s=$(gh pr checks <PR#> --json name,bucket 2>/dev/null || echo "[]")
     cur=$(jq -r '.[] | "\(.name): \(.bucket)"' <<<"$s" | sort)
     comm -13 <(echo "$prev") <(echo "$cur")
     prev=$cur
     jq -e 'length > 0 and all(.bucket != "pending")' <<<"$s" >/dev/null 2>&1 && break
     sleep 20
   done
   ```

   Don't fire-and-forget; don't sleep without a notifier.

2. **CI green → `/review <PR#>`.** Same session. `/review` is
   responsible for the schema / `sources/`-immutability / confidence /
   `/shape`-human-approval / content-quality gates and the merge.

3. **CI red → fix and push.** Diagnose locally, commit on the same
   branch, push. The monitor restarts on the new push.

4. **`/shape` exception.** If the PR touches
   `wiki/<scope>/{adrs,prds}/<slug>.md` outside any
   `ai-suggestions/` subfolder, `/review` will refuse to merge
   without a human `APPROVED` review. After CI green: surface the
   PR URL to the user and **stop**. Do not self-approve.

## What /pr is *not*

- **Not a merge.** Merging is `/review`'s job. The same agent can
  author and merge — checks-green is the gate, not a second pair of
  eyes — but the operations are still distinct skills.
- **Not a force-push tool.** Never use `--force` or `--force-with-lease`
  inside this skill. If the branch is rebased, the human handles it.

## Done check — terminate on observable state, not declared intent

Each item must be verifiable from current repo / wire state. "I
armed the watcher" is not done; "the PR merged" is.

- [ ] `git rev-parse --abbrev-ref HEAD` ≠ `main` (work landed on a
      feature branch).
- [ ] `tools/preflight.sh` exited 0 locally before push (validate +
      check --no-net + views regen + clean diff). The PreToolUse
      hook in `.claude/settings.json` re-runs this on `git push`
      and `gh pr create`; both are blocked on failure.
- [ ] `gh pr view <PR#> --json title,body --jq '.body'` contains
      Why / Affects / Sources / Restricted-paths sections.
- [ ] `gh pr view <PR#> --json mergedAt --jq .mergedAt` is non-null
      **OR** the PR is `/shape`-shaped (touches
      `wiki/<scope>/{adrs,prds}/<slug>.md` outside
      `ai-suggestions/`) and the user was asked to take over **OR**
      the user explicitly halted the chain.
- [ ] `gh pr checks <PR#> --json bucket --jq 'all(.[]; .bucket != "pending")'`
      returns `true` — no in-flight check left armed.
- [ ] If merged: `git -c log.showSignature=false log origin/main -1 --pretty=%H -- log/log.md`
      shows the audit line for this PR (or a tiny follow-up PR
      lands the line immediately after).
