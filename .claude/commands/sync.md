---
description: One-shot health sweep — siblings + lint + check + validate + views
---

Apply the `sync` skill.

Runs the full sweep: `tools/sync-siblings.sh`, the `wiki-lint` skill,
`python tools/brain.py check`, `python tools/brain.py validate`, and
`python tools/brain.py views`. Surface anything that needs judgement
in the consolidated `sync —` log line.

`$ARGUMENTS` is currently unused; the sweep is whole-corpus.
