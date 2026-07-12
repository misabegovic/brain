---
name: review
description: Review and (if checks pass) merge a brain PR. Runs validate + check locally, sources/-immutability gate, confidence-floor gate, content-quality pass, then merges via `gh pr merge --squash`. The author and reviewer can be the same agent session — checks-green is the gate, not a second pair of eyes. Refuses to merge on any guardrail failure with a posted review comment. Load when the user says "review", "review pr", "check pr", "merge pr", or invokes `/review <PR#>`.
---

# Review and merge a brain PR

You are working in `~/projects/brain`. This skill reviews a PR and
merges it if every guardrail passes. The author and reviewer can be
the same agent session — at this scale, CI checks + the
sources/-immutability + confidence-floor gates are sufficient.

**Refuse to merge** on any guardrail failure. Post the failure as a
review comment so the next iteration can fix and re-request review.

## Local-first mode

If `.env` declares `LOCAL_FIRST=true`, this skill is **dormant** —
no remote PR exists to review. If the operator invokes `/review`
under local-first:

- If a `<PR#>` was supplied, run normally — they're explicitly
  reviewing a remote PR (perhaps one opened earlier via an explicit
  `/pr` invocation, or one a teammate opened).
- If no `<PR#>` was supplied, abort with a one-line note: under
  local-first the merge surface is the operator approving local
  commits inline. Surface `git log origin/main..HEAD --oneline` and
  stop.

```bash
[ -f .env ] && grep -q '^LOCAL_FIRST=true$' .env && LOCAL_FIRST=1
```

## Inputs

- `/review <PR#>` — the PR to review.
- `/review` (no arg) — list open PRs and pick the oldest unreviewed
  one.

## Protocol

### 1. Fetch and inspect

```bash
gh pr checkout <PR#>
gh pr diff <PR#>
gh pr view <PR#> --json title,body,files,baseRefName,headRefName,statusCheckRollup
```

Read the diff fully. Don't skim.

### 2. Schema + sources gate

Run locally on the PR's state:

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py validate
~/.local/share/mempalace-venv/bin/python3 tools/brain.py check --no-net
```

Either failure → post the output as a review comment, request changes,
**do not merge.**

### 3. CI gate

Read the PR's check runs from the `gh pr view` output above. If
`validate` (the GitHub Actions workflow) hasn't completed
successfully, **wait** — `gh pr merge --squash --auto` will block on
it anyway, but posting a comment makes the state clear.

If `validate` has *failed*, post its log and refuse. Don't merge a
failing PR even if your local checks pass — the runner is the source
of truth for CI.

### 4. `sources/` immutability gate

`sources/` is *additive only*: agents may add new files but not
modify or delete existing ones. Compute the diff against `sources/`:

```bash
gh pr diff <PR#> -- sources/ | grep -E '^(deleted file|modified)'
```

Any non-additive change → refuse with a review comment.

### 5. Confidence-floor gate

Walk every wiki page modified by the PR. If any has `confidence: high`
in its frontmatter and was *introduced* by this PR (not just modified),
fail: agent-authored content cannot self-promote to `high` in the same
PR. Post a comment naming the offending page.

(`confidence: medium` and `low` are fine. Existing pages staying at
their current confidence are fine. The rule is specifically against
*new* `high` from agent authors.)

### 5a. `/shape`-PR human-approval gate

Per `AGENTS.md` § Governance > `/shape` PRs are human-gated at
every phase, any PR that touches the human-approved ADR/PRD
shelves requires an explicit human `APPROVED` review before
merge. CI green is necessary but not sufficient.

**Detect a `/shape`-shaped PR.** Walk the PR's file list:

```bash
gh pr view <PR#> --json files --jq '.files[].path'
```

Match any path against:

```
wiki/(?!_)[^/]+/(adrs|prds)/[^/]+\.md
wiki/(?!_)[^/]+/[^/]+/(adrs|prds)/[^/]+\.md
```

(That is: `wiki/<scope>/adrs/<slug>.md` or
`wiki/<scope>/prds/<slug>.md` at any of the three scopes —
`wiki/<repo>/`, `wiki/org/`, `wiki/brain/`.) **Exclude
`ai-suggestions/`**: paths matching
`wiki/<scope>/ai-suggestions/(adrs|prds)/<slug>.md` are
suggestion-tier and follow the regular self-merge rule, **not**
this gate. The `ai-suggestions/` shelf has its own graduation
flow (a separate PR with human review when the suggestion is
promoted to the live shelf).

If at least one human-approved-shelf path matches, this is a
`/shape`-shaped PR.

**Require a human APPROVED review.** Look for an approving
review whose author is *not* the PR author and whose state is
`APPROVED`:

```bash
gh pr view <PR#> --json reviews,author --jq '
  .reviews[]
  | select(.state == "APPROVED")
  | select(.author.login != $author)
' --jq-arg author "$(gh pr view <PR#> --json author --jq .author.login)"
```

If no such review exists, **refuse to merge.** Post a review
comment naming the rule:

> Detected `/shape`-shaped PR (touches
> `wiki/<scope>/{adrs,prds}/<slug>.md`). Per `AGENTS.md`
> § Governance > `/shape` PRs are human-gated at every phase, an
> explicit human `APPROVED` review is required before merge.
> Surfacing the PR for human review.

Stop. Do not approve. Do not merge.

If a human APPROVED review *is* present, proceed to step 6.

### 6. Content-quality pass

Read the diff with judgement:

- Does new wiki content cite sources?
- Does it use the right `kind:` and corresponding required sections?
- Are claims hedged where they should be (`(unverified, YYYY-MM-DD)`)?
- Does it contradict any existing page? (Spot-check via mempalace
  search or by reading adjacent pages.)
- Is it within the spirit of the brain — synthesis, not narration?
- If the PR touches **restricted paths** (per `AGENTS.md` § Path
  conventions), pay extra attention. The flag is informational, not
  a gate; you still merge if everything else is green.

If concerns arise that aren't blocking guardrails, post them as
non-blocking review comments. Then proceed.

### 7. Approve and merge

If every gate passed:

```bash
gh pr review <PR#> --approve --body "Reviewed. All guardrails green. Merging."
gh pr merge <PR#> --squash --delete-branch --auto
```

`--auto` means GitHub will land it once required checks pass (CI).
If checks are already green, the merge happens immediately.

### 8. Post-merge audit log

After the merge has actually landed (poll
`gh pr view <PR#> --json mergedAt` if `--auto` was used), append to
`log/log.md` on `main`:

```
YYYY-MM-DD merge — PR #<num>: <title>
   diff: <files changed> files, +<insertions>/-<deletions>
   restricted-paths: <true|false>
```

Branch protection requires this update to also go through a PR. The
simplest pattern: include the audit log entry as the *last commit* on
the PR's own branch before merging — that way the merge commit on
`main` already carries the audit line. If you forgot, open a tiny
follow-up PR with just the audit line.

### 9. Post-merge validate

Pull `main`, re-run validate. If it fails:

```bash
gh pr revert <PR#>      # opens a revert PR
```

Auto-revert is a guardrail of last resort. It should rarely fire
because the pre-merge validate already ran on the PR's state.

## What review is *not*

- **Not a rubber stamp.** The agent reads diffs in full and makes
  judgement calls. Failing checks, broken citations, contradictions,
  or non-additive `sources/` changes all cause refusal.
- **Not the only source of merge.** Humans can still merge via the
  GitHub UI; this skill is the agent path.

## Done check

- [ ] Diff was read in full.
- [ ] Schema + sources + CI + immutability + confidence gates all
      passed (or PR was refused with a comment).
- [ ] Content-quality pass was performed.
- [ ] Either approved + merged, or refused with a clear review comment.
- [ ] If merged: `log/log.md` has the audit line; post-merge validate
      ran clean.
