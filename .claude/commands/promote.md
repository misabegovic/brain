---
description: Graduate a kind: insight page into a kind: initiative (with supersession bookkeeping)
---

Apply the `wiki-promote` skill to: $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user which insight page to promote.
Otherwise treat `$ARGUMENTS` as a wiki-relative path to a `kind:
insight` page (e.g. `application-form-friction.md`).

Run the full protocol: read the insight, run
`python tools/brain.py promote <insight>`, synthesise the new
initiative's What/How/Why/Now/Perceived/Target from the insight's
Pattern/Implications/Evidence, update `wiki/index.md` (mark insight
superseded → initiative), cross-link affected personas, log, and
validate.
