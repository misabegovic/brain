---
description: Add something to the brain (auto-routes to ingest / mine / feedback)
---

Apply the `intake` skill to: $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user what to bring in. Otherwise let
the skill route the input to the right underlying operation
(`wiki-ingest`, `palace-mine`, `feedback-ingest`, or a combination).
Announce the routing decision in plain English before running anything.
