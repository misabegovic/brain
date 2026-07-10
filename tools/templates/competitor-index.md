---
title: <Competitor name> — competitor
kind: reference
status: living
updated: YYYY-MM-DD
team: brain
division: engineering
affects:
  # Repos whose product strategy this competitor's surface touches.
  # Reverse `affected_by:` is auto-computed in pages.json.
  - <repo>
  # - <another-repo>
confidence: low
sources:
  - sources/web/competitors/<competitor>/<slug>--<shortid>.md
  # Add additional snapshots as they are ingested.
---

# <Competitor name>

Per-competitor synthesis page for `wiki/org/competitors/<competitor>/index.md`,
authored per [`wiki/brain/adrs/competitor-intel-ingestion.md`](../../../brain/adrs/competitor-intel-ingestion.md).

> **Agent-authored synthesis from public sources.** Describes the
> competitor's product surface and strategic posture as observed
> from publicly cited material; not an internal assessment, not a
> recommendation. Citations resolve back to immutable snapshots
> under `sources/web/competitors/<competitor>/`.

## What it is

One-paragraph summary of the company and what it sells. Cite the
clearest authoritative source (the company's own product page,
its Crunchbase / About page, or a recent trade-press profile).

## Product surface

What the competitor's products cover today. One short
paragraph or a bulleted list when the surface is wide. Anchor
each capability claim in a citable snapshot.

## Strategic implications for us

How the competitor's surface overlaps our `repos:`
listed in `affects:` above. One paragraph. Where the overlap
lines up with an in-flight `/shape` cycle (a PRD, ADR, or epic),
cross-link the relevant brain page in prose.

## Recent events

Date-stamped milestones — fundings, acquisitions, GA launches,
strategy shifts — newest first. Each entry cites the
corresponding snapshot. Keep to ~5–10 entries; older events
graduate to a dedicated `news/<event>.md` sub-page if a single
event earns more than three sentences.

- **YYYY-MM-DD** — <event>. *(snapshot: `<slug>--<shortid>.md`)*

## Open threads

What this page can't yet answer. *(needs source)* markers stay
visible to the next ingest agent.

- *(open thread, needs source)*
