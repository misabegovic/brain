---
description: Ask the brain (auto-routes to query / plan / overlap / coverage)
---

Apply the `ask` skill to: $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user what they want to know.
Otherwise let the skill route the question — default is factual
`wiki-query`; phrasing escalates to `wiki-plan`, `wiki-overlap`, or
`wiki-coverage` when appropriate. Announce the routing decision before
running.
