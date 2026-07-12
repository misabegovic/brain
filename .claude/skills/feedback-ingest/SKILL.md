---
name: feedback-ingest
description: Process a batch of AI-summarised user feedback into insights — read the batch under sources/ai_user_feedback/<date>/, attribute each record to the user personas in .claude/personas/users/, cluster records into themes, emit one kind: insight page per material theme under wiki/, cross-link affected personas, and log the run. Load when the user says "feedback", "process feedback", "ingest the feedback batch", "extract insights", or otherwise asks to turn user feedback into wiki insights.
---

# Process AI user feedback into insights

You are working in `~/projects/brain`. The brain ingests batches of
AI-summarised user feedback (`sources/ai_user_feedback/<date>/`) and
synthesises them into `kind: insight` pages. This skill is the
operation that does it. The user-side personas in
`.claude/personas/users/` are the lens; the raw feedback is the data;
insights are the output.

## When to run

- A new batch landed under `sources/ai_user_feedback/<YYYY-MM-DD>/`.
- The user explicitly asks "what's in the latest feedback batch?"
- Periodic: at the start of a planning cycle, walk recent batches that
  haven't been processed yet.

## Inputs

- `/feedback <YYYY-MM-DD>` — process the named batch.
- `/feedback` — process the most recent unprocessed batch (check
  `log/log.md` for prior `feedback —` lines).

## Protocol

### 1. Confirm the batch

- Check that `sources/ai_user_feedback/<date>/` exists.
- Read `provenance.yaml`. Confirm `record_count` matches what's in
  `raw.jsonl` (or `summary.md` if `raw.jsonl` is absent).
- Run `mempalace search` for prior insight pages near this batch's
  themes if the batch has a `summary.md`. Past insights inform whether
  this batch *adds* a pattern or *strengthens* one.

### 2. Load the user personas

Read `.claude/personas/users/*.md`. Specifically pay attention to each
persona's **Feedback signature** and **Example feedback** sections —
these are the attribution lens.

### 3. Attribute records to personas

For each record in the batch:

- Read `verbatim` and `metadata.user_role_hint`.
- Match against persona signatures — each `users/` persona file
  declares the complaint / request shapes it typically produces
  (time-and-clicks complaints, strategic metric-shaped requests,
  settings-and-permissions gaps, infrequent-use relearning pain,
  etc.). Build the pattern table from the persona files the org
  has authored; keep it in this section as it stabilises.

A record may attribute to more than one persona. Record the
attribution as a list of persona slugs per record. Don't skip
attribution because it's uncertain — `metadata.user_role_hint` is
already a hint; combined with `verbatim`, you can usually pick at
least one strong candidate.

If a record clearly fits no persona, flag it. A persistent
no-fit cluster suggests a missing persona and is worth surfacing in
the log.

### 4. Cluster records into themes

Group records by recurring topic. A *theme* is at minimum:

- **3+ records** from the batch saying related things, OR
- **2 records** that strengthen a theme already on the wiki (i.e.
  there's a prior `kind: insight` page on this topic — strengthen it
  rather than create a new one).

Below the threshold: don't write a new insight page. One-off feedback
goes in the log entry, not in the wiki.

### 5. For each theme, decide: new insight or update existing?

Walk `wiki/index.md` (and the auto-generated `wiki/_views/by-kind.md`)
looking for existing `kind: insight` pages on adjacent topics.

- **Existing page is the natural home.** Edit it. Add new evidence to
  `## Evidence`, add new affected personas if the cohort widened,
  bump `confidence` if appropriate, update `updated:`. Don't recreate.
- **No existing page.** Start from `tools/templates/insight.md`. Slug:
  `<theme-slug>.md` at `wiki/`. Promote into `wiki/insights/` once
  there are three or more insight pages.

### 6. Write the insight page

Required sections (validated by `tools/brain.py validate`):

- `## Pattern` — what the recurring observation is, in 1–2 paragraphs.
- `## Evidence` — citations to specific records from `raw.jsonl` (use
  record `id`s) or to lines in `summary.md`. Quote the verbatim text
  where short; otherwise paraphrase + link.
- `## Affected personas` — link to each user persona this theme
  surfaces from. Use relative paths (`../.claude/personas/users/<slug>.md`).
- `## Implications` — what this means for the product. Surface, don't
  decide. If the theme suggests an initiative, name what would have to
  be true for an initiative to be worth opening.
- `## Status` — open / acknowledged / under investigation / acted-on /
  dismissed. New insights start at *open*. Note who's looking.

Frontmatter:

```yaml
---
title: <pattern in one phrase>
kind: insight
status: draft        # → living once a real PM/EM has read it
updated: YYYY-MM-DD
confidence: low      # bump as evidence accumulates
affected_personas:
  - .claude/personas/users/<slug>.md
sources:
  - sources/ai_user_feedback/<date>/raw.jsonl
  - sources/ai_user_feedback/<date>/summary.md
---
```

### 7. Cross-link

- On each affected user-persona file: don't edit the persona itself
  (personas are stable). The cross-link is one-way from insight → persona.
- Update `wiki/index.md` to list new insight pages under an `## Insights`
  section.
- If an insight strongly suggests action, mention candidate initiatives
  in `## Implications` so the next planning cycle can see them.

### 8. Log

Append one line to `log/log.md` per batch:

```
YYYY-MM-DD feedback — <batch-date> (<record-count> records) →
   <N insights written>, <M insights updated>
   no-fit cluster: <count> [optional, with one-line note]
```

If a no-fit cluster is significant, also surface a short bulleted note
under the log line — it's a signal that the user-persona roster may
need an addition.

### 9. Regenerate views

Once new insight pages have landed:

```
python tools/brain.py validate
python tools/brain.py views
```

Validate must pass. Views regenerates `wiki/_views/{by-kind,by-team,by-repo}.md`
and `pages.json`. Commit the auto-generated outputs alongside the new
insight pages.

## What feedback-ingest is *not*

- Not a customer-success channel. We synthesise *aggregate* signal; we
  don't reply to individual customers from inside this workflow.
- Not authoritative on whether to act. Insights surface; PMs and EMs
  decide. An insight graduates into `kind: initiative` only when a team
  commits.
- Not a replacement for direct user research. The brain reads what
  came in; it doesn't run interviews.

## Done check

- [ ] `provenance.yaml` was read and the record count was verified.
- [ ] All user personas were considered for attribution; no records
      silently dropped.
- [ ] Each theme reaches the 3+ records (or 2-records-on-existing-page)
      threshold before becoming an insight.
- [ ] Existing insight pages were preferred over new ones.
- [ ] Every new insight has all five required sections.
- [ ] Insight pages cite back into `sources/ai_user_feedback/<date>/`
      and to the affected user persona files.
- [ ] `wiki/index.md` § Where to find things lists new insight pages.
- [ ] `wiki/index.md` § Insights now updated with the new insight(s)
      surfaced in this run. Per
      [`wiki/brain/adrs/home-content-shape.md`](../../../wiki/brain/adrs/home-content-shape.md):
      every wiki/ edit must be paired with a wiki/index.md edit.
- [ ] `log/log.md` records the run.
- [ ] `python tools/brain.py validate` is clean.
