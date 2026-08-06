---
title: Intent compilation — the wiki joins the architecture graph
kind: reference
status: living
updated: 2026-08-06
confidence: medium
sources:
  - tools/brain.py
  - https://github.com/enola-labs/enola/pull/197
enola_intent:
  page:
    type: reference
    status: living
    origin:
    - repo
    - web
---
# Intent compilation — the wiki joins the architecture graph

*Agent-authored synthesis. The first page to read before touching
the `enola_intent:` machinery; the mechanics live in `tools/brain.py`
and the upstream standard in enola's `docs/INTENT.md`.*

## The picture

enola is a surveyor who re-walks the estate and draws an exact map
of what is built — every file, symbol, and dependency. The wiki is
the filing cabinet: every decision about *why* things are the way
they are lives here as prose. Intent compilation pins each page onto
the surveyor's map. The pin is the `enola_intent:` frontmatter block,
and nobody writes its `page:` half by hand — it is *derived* from
what the page already says (its kind, its links to other pages, the
exact repo files its `sources:` cite) by `brain.py intent stamp`,
re-run automatically by the pre-commit hook. When the surveyor walks
the estate he picks up the pins too, so one map holds both **what
is** and **what we said should be**.

Every snapshot compares the two and only speaks on disagreement: a
pin at a demolished path (**dangling anchor** — the stale-citation
check made mechanical), a measured cross-repo dependency no
declaration covers (**unexpected seam**), a page number the estate
no longer matches (**failed claim**), a replaced decision whose seam
still runs (**superseded intent still measured**). Silence stays
honest: *the graph was not asked* (a repo not loaded, a file kind no
extractor parses, an annotated citation) is never dressed up as *the
graph disagreed*.

It also answers backwards — the **reverse query**. Any file or
symbol answers *which decisions govern this?* with the page, its
type and status, and its relation trail (what it is part of, depends
on, supersedes): `brain.py enola govern <target>` headlessly, or the
`governing_intent` MCP tool in sessions.

## The loop

1. **Author** a page normally; cite exact repo files, link the pages
   it builds on. A trailing ` (…)` annotation marks a citation
   knowingly not current — the stamp retires its anchor and `check`
   skips it rather than breaking.
2. **Stamp** — automatic at commit (auto-restamp, scoped staging),
   gated at push (`intent-page-block`) and in CI. Never hand-edit
   the `page:` half; the hand-authored halves (`consumes:`,
   `claims:`, `layers:`) are deliberate declarations on the few
   pages that own such decisions.
3. **Snapshot** — `brain.py enola generate` compiles pages into
   knowledge nodes, relations, and anchors beside the measured
   facts.
4. **Verdict** — the intent explainer diffs declared against
   measured. Findings are candidates: confirm against the code,
   record the judgment with `brain.py enola judge` so the next
   session inherits it.
5. **Repair** — `/groom` owns the residue: moved path → fix the
   citation; removed or branch-only path → annotate it; real but
   unmeasured path → extraction-gap verdict. Never delete a citation
   to silence a finding.

## Release gate

The compile-and-verdict half requires an enola release carrying the
intent standard (upstream PR #197: declarations, verdicts, anchors,
the reverse query). Until the pinned binary crosses that release,
every stamp-side gate runs and the blocks compile forward-compatibly;
`govern` answers *no knowledge pages compiled* — a named skip, not
an error — and verdicts simply do not exist yet. Nothing needs
migrating at the flip: regenerate the snapshot and the wiki is in
the graph.
