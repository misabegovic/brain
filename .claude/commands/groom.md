---
description: Knowledge GC — confidence demotion, insight decay, supersede→archive
---

Apply the `groom` skill.

Walks every wiki page against the half-life table in `AGENTS.md`.
Demotes confidence when sources have moved; flags decayed insights
and stale initiatives for human review; transitions long-superseded
pages to `wiki/_archive/`. Logs every decision in the consolidated
`groom —` line.

`$ARGUMENTS` is currently unused; the sweep is whole-corpus.
