---
description: Walk the product as a user persona — real execution, findings routed to insights
---

Apply the `playthrough` skill.

Picks a persona from `.claude/personas/users/` (or the one named in
`$ARGUMENTS`), executes their scenario against the running product
for real, snapshots the transcript to `sources/playthroughs/`, and
routes decision-worthy findings to `wiki/insights/` at
`confidence: low` (the cap holds until a human confirms). Fixable
bugs get fixed in-session; small frictions stay in the transcript.

`$ARGUMENTS`: `<persona> [<scenario>]`, `sweep` (one scenario per
touched persona), or empty (best-fit persona for the latest
release).
