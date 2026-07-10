---
description: One-shot health sweep — siblings + lint + check-sources + validate + views
---

Apply the `sync` skill.

Runs the full sweep: `tools/sync-siblings.sh`, the `wiki-lint` skill,
`tools/check-sources.py`, `python tools/brain.py validate`, and
`python tools/brain.py views`. Surface anything that needs judgement
in the consolidated `sync —` log line.

`$ARGUMENTS` is currently unused; the sweep is whole-corpus.
