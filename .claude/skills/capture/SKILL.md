---
name: capture
description: Capture conversation context, design discussion, customer interaction, or any unstructured signal into the brain — picks the right shelf based on scope (brain / org / <repo>) and routes the synthesis there. Distinct from `/in <source>` (which expects an external source) and from `/shape` (which is the formal pitch-to-PRD path). `/capture` is for the in-flight stuff — what the user just told you, what a customer just said, what a design doc just argued — that needs to go *somewhere* without a clear source path. Load when the user says "capture", "note that", "remember this", "the user just said", "design discussion", "we just decided", or invokes `/capture <scope>`.
---

# Capture — in-flight context into the right shelf

You are working in `~/projects/brain`. `/capture <scope>` is the
ingest path for **unstructured signal** — conversation context,
design discussion, customer interaction, observations from a
session — that doesn't have a clean source URL or file path but
deserves to land in the brain.

It exists because:

- `/in <source>` expects a *source* — a path or a URL. Pasted text
  works as a fallback, but the entry point is source-shaped.
- `/shape` is the formal Shape Up workflow. Heavyweight for
  capturing "here's a thing the user mentioned in passing."
- `/feedback` is for AI-summarised user-feedback batches. Different
  shape entirely.

`/capture` is the lightweight middle. The agent saves a transcript
under `sources/conversations/` and edits the relevant shelf.

## Scope

`/capture <scope>` — `scope` is one of:

| Scope     | Lands in                                             |
|-----------|------------------------------------------------------|
| `brain`   | `wiki/brain/state.md` § *(appropriate section)* + a snapshot in `sources/conversations/`. Brain-self observations — workflow gaps, schema rough edges, things the brain itself should change. |
| `org`     | `wiki/org/<page>.md` (existing or new) + snapshot. Cross-team signals — process changes, methodology decisions, org-level shifts. |
| `<repo>`  | `wiki/<repo>/state.md` § *(appropriate section)* + snapshot. Repo-level observations — what shipped, what's stale, what changed in the team's mental model. |

If the scope is ambiguous, **ask one short clarifying question
before running.**

## Inputs

- The conversation context (what was just said).
- The scope (`brain` / `org` / `<repo>`).
- (Optional) explicit text the user wants captured verbatim.

## Protocol

### 1. Snapshot

Write the captured content (or a faithful summary if the user
hasn't dropped explicit text) to:

```
sources/conversations/<YYYY-MM-DD>--<scope>--<slug>.md
```

Frontmatter:

```yaml
---
title: <one-line description of what was captured>
captured: YYYY-MM-DD
scope: <brain|org|repo-name>
captured_by: <agent name or model id, if known>
---
```

Followed by the verbatim or summarised content.

This is now an immutable source under `sources/`.

### 2. Decide the shelf

Match the captured content against the existing shelves of the
scope:

- **brain**: usually `wiki/brain/state.md`'s *Open threads* /
  *Perceived* / *Target* sections. Sometimes a new
  `wiki/brain/permanent/<concept>.md` page if the capture is a
  durable rule (rare).
- **org**: usually one of the existing pages in `wiki/org/`. If
  the capture introduces a new org-level concept, create a new
  page (sparingly).
- **<repo>**: usually `wiki/<repo>/state.md` *Now* or *Perceived*.
  Sometimes `<repo>/permanent/*` if the capture is a stable fact
  about how the repo works.

Default to **editing existing pages.** New pages need real
material to earn their place.

### 3. Apply the edit

- Cite the snapshot path (`sources/conversations/...`) in the
  page's `sources:` list.
- Add a short paragraph or bullet to the appropriate section.
- Bump `updated:` on the page.
- If the capture surfaces a forward intent or a decision the user
  is making *now*, hand off to `/shape <scope>` — `/capture` is
  not a substitute for `/shape`.

### 4. Hand-off detection

If the captured content contains:

- **A forward pitch** ("we should add X" / "let's build Y") →
  hand off to `/shape <scope> <pitch>` after the capture lands.
- **A decision being made** ("we're going to do X over Y") →
  hand off to `/shape <scope> --record <description>`.
- **A user-facing problem with affected personas** → hand off to
  `/feedback` (or surface it as material for the next feedback
  batch).
- **An operator lesson** (rule-shaped capture — *"do X, don't Y;
  Why; How to apply"* — distinct from a *"what's true today"*
  observation) → land it as a `### <slug>` subsection under the
  `## Lessons` heading on the target repo's
  `wiki/<repo>/permanent/conventions.md` if the rule is
  repo-bound, or as a `## <slug>` subsection on
  `wiki/org/operator-lessons.md` if the rule spans repos. Per
  [`wiki/brain/adrs/operator-lesson-pattern.md`](../../../wiki/brain/adrs/operator-lesson-pattern.md);
  authoring shape (Why + How to apply + *Graduated from*
  citation) per
  [`wiki/brain/authoring-adrs-and-prds.md`](../../../wiki/brain/authoring-adrs-and-prds.md)
  § Operator lessons.

The hand-off is **same-session, same-PR** per AGENTS.md hand-off
mechanics.

### 5. Log

Append one line to `log/log.md`:

```
YYYY-MM-DD capture — <scope>: <one-line summary> → <pages edited>
```

## Done check

- [ ] Snapshot exists under `sources/conversations/YYYY-MM-DD--<scope>--<slug>.md`
      with required frontmatter.
- [ ] Edited page(s) cite the snapshot in `sources:`.
- [ ] If a forward pitch or decision was detected, `/shape` was
      invoked in the same session.
- [ ] `log/log.md` has the capture line.
- [ ] No content from `wiki/` was treated as a source.

## What `/capture` is *not*

- Not a substitute for `/in` when there's a real source URL or
  path. Use `/in` then.
- Not a substitute for `/shape` for forward work. Hand off.
- Not for ephemeral session notes. The bar is "would a future
  agent / human want to know this?" — if not, the conversation
  itself is enough; nothing needs to land.
