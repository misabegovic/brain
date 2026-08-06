---
name: groom
description: Knowledge garbage-collection sweep over the brain. Distinct from /sync — /sync is mechanical (broken links, validate); /groom makes value judgements (confidence demotion when sources have moved, insight decay flagging, superseded → archived transitions). Load when the user says "groom", "decay", "archive", "knowledge gc", "is anything stale", or invokes `/groom`.
---

# Groom — knowledge garbage collection

You are working in `~/projects/brain`. Permanent knowledge bases rot
when nothing actively prunes them. `/sync` catches structural rot;
`/groom` catches *epistemic* rot — pages that may still be technically
valid but are no longer trustworthy at their stated confidence, or
insights that have lingered without action for too long.

This skill makes value judgements. Every decision is logged. When in
doubt, **flag for human review** rather than acting silently.

## Half-life policy (per `AGENTS.md`)

| Page kind     | "Fresh"     | "Aging"      | "Stale"        |
|---------------|-------------|--------------|----------------|
| `reference`   | < 90 days   | 90–180 days  | > 180 days     |
| `initiative`  | < 30 days   | 30–60 days   | > 60 days      |
| `decision`    | < 1 year    | 1–2 years    | > 2 years      |
| `entity`      | < 180 days  | 180–365 days | > 365 days     |
| `insight`     | < 30 days   | 30–90 days   | > 90 days      |
| `overlap`     | < 60 days   | 60–120 days  | > 120 days     |

Plus: a page's clock resets on a *content* edit (not a frontmatter-only
bump). Use git blame / `git log -p` to confirm if unsure.

`brain.py links` is the deterministic pre-read: orphans and
dead-ends are pruning candidates, hubs are where demotions hurt
most. The daily `inbox-refresh` op queues half-life crossings and
an orphans item automatically — a groom pass often starts as
`/tend groom`.

## Protocol

### 1. Load the corpus

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py views
cat wiki/_views/pages.json
```

Walk every page. For each, compute: kind, age (today − `updated:`),
confidence, whether the cited sources have moved (use git on the
relevant sibling repo where possible).

### 2. Decisions per page

| Trigger                                                                                       | Action                                                                                  |
|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `reference` + age > 90d + cited sibling repo has moved > 30 commits since `updated:`           | Demote `confidence: high → medium`. Note in the page's intro: *(stale; sources moved)*. |
| `reference` + age > 180d + sources still moving                                                | Flag for re-validation. Do *not* edit — surface in the log instead.                     |
| `initiative` + status `living` + age > 60d                                                     | Flag *"is this still active?"*. Surface for human / authoring team.                     |
| `initiative` + status `living` + cited PRs/commits all merged                                  | Flag *"likely shipped — promote to reference or archive"*.                              |
| `insight` + status `draft\|living` + age > 90d + no `superseded_by`                            | Flag *"act, dismiss, or restate"*. Surface for review.                                  |
| Any kind + status `superseded` + age > 365d                                                    | Move to `wiki/_archive/<original-path>`. Update index. Page remains readable.           |
| Any kind + status `archived`                                                                   | Already moved; verify it's under `wiki/_archive/`.                                      |
| `decision` + age > 2y + a newer decision page references the same topic                       | Flag for *"supersede the old one explicitly"*.                                          |

`/groom` does **not** delete pages. Archive moves are reversible (just
move back). Confidence demotions are reversible (next ingest can promote).

| A page's structural claim contradicted by the code substrate (`brain.py structure findings --repo <repo>` always answers; `brain.py enola findings` / `enola impact <symbol>` add call graphs where the binary is installed. Both skip cleanly when absent — a named skip, never a silent pass.) | Flag the contradiction for judgment — **never apply it**. A finding is a candidate to verify, not a verdict. Resolving it means reading the code, then either correcting the page or recording the finding as `rejected` with the reason. |
| A verdict whose finding has left the snapshot (`brain.py reflection-check ledger-hygiene`) | Ledger hygiene. An `accepted` entry whose finding is gone is usually good news — the thing got fixed — and any page citing it may now overclaim; a `rejected` one that vanished can be dropped. `noise` entries describe the explainer, not the code, and never go stale. |
| A dangling-code-anchor finding (`intent` explainer) — a page's derived anchor covers a path the graph measures nothing at | Resolve against the measured tree, never by guess; `brain.py enola govern <page-or-path>` locates both ends. Three outcomes: the path **moved** → verify the rename in the repo's git history, then fix the citation in place; the path is **prototype/branch-only or deliberately removed** → annotate the citation with a trailing ` (…)` note so the stamp retires the anchor and `check` skips it as knowingly historical, and flag the page for re-ingest when its prose also describes the old world; the path **exists but unmeasured** → record an extraction-gap verdict with `brain.py enola judge`. Never delete a citation to silence a finding. |
| A receipt citation reported `stale` or `malformed` (`brain.py enola citations`) | Flag for *re-verification* — the graph moved past the cited digest, or the citation breaks the grammar. Never auto-edit; re-verifying is a judgment task. **Before re-reading the code, ask the history what moved**: `brain.py enola history blame <name-or-path> <repo>` reports when the cited thing entered the architecture and when it left, which usually turns "this digest is old" into "this claim died on a specific day". Experimental upstream; skips cleanly. |

### 3. Reserved archive folder

`wiki/_archive/` is a tooling-output folder like `_views` and
`_overlaps` — lint and orphan checks skip it. Pages there keep their
relative paths (e.g. `wiki/_archive/<page>.md`) so backlinks
continue to resolve.

When archiving:

1. `mv wiki/<page>.md wiki/_archive/<page>.md`
2. Update `wiki/index.md` — replace the entry with one in an `## Archive`
   section (group all archived links there).
3. For any page in `wiki/` that links to the archived one, leave the
   link as-is (Quartz's broken-link warning is a feature here — humans
   can decide whether to update).

### 4. Surface judgement calls

Anything that needs human review goes in the consolidated `groom —`
log line as a bulleted block. Flagged-for-review pages are *not*
edited; only the log surfaces them.

```
YYYY-MM-DD groom — walked <N> pages: <D> demoted, <A> archived,
   <F> flagged
   - flagged: wiki/<page>.md (<reason>)
   - flagged: wiki/<page>.md (<reason>)
```

### 5. Validate

```bash
~/.local/share/mempalace-venv/bin/python3 tools/brain.py validate
~/.local/share/mempalace-venv/bin/python3 tools/brain.py intent stamp
~/.local/share/mempalace-venv/bin/python3 tools/brain.py views
```

Validate must exit 0 — archive moves can break index links, the views
regen captures the new state.

## Summary drift

Pages carrying a `summary:` frontmatter field (the briefing renders
them as cards) get one extra check per sweep: does the summary
still match the body? A page whose content moved on while its
summary stayed put misleads at the exact altitude humans read.
Rewrite stale summaries in place (a summary edit alone does not
bump `updated:`).

## What groom is *not*

- **Not deletion.** Archive ≠ delete. Demotion ≠ removal.
- **Not silent re-synthesis.** If a page is genuinely wrong, that's
  `/in` (re-ingest) territory or human edit territory. `/groom` only
  changes status / confidence / location.
- **Not run on every push.** This is a periodic operation —
  recommended cadence is monthly.

## Done check

- [ ] Every page in `wiki/` was assessed against the half-life table.
- [ ] Each action taken is in the consolidated log line.
- [ ] Every flagged-for-review page is named under the log line, with
      a one-line reason.
- [ ] `brain.py validate` is clean.
- [ ] `wiki/_views/` regenerated.
- [ ] `wiki/index.md` § Drift surface updated with the top-N
      Now-vs-Perceived gaps from this groom pass. Per
      [`wiki/brain/adrs/home-content-shape.md`](../../../wiki/brain/adrs/home-content-shape.md):
      every wiki/ edit must be paired with a wiki/index.md edit.
- [ ] No page was edited beyond the documented actions (status,
      confidence, location, intro stale-tag).
