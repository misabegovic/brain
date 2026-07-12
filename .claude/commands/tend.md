---
description: Digest the brain's inbox — pending synthesis work queued by the deterministic producers
---

Apply the `tend` skill.

Reads `wiki/_state/inbox/` (via `brain.py inbox list --json`), digests
items priority-first within the given budget, lands each item's work
as LOCAL_FIRST commits (or PRs in remote mode), clears items with
`brain.py inbox done <id>`, and closes with a home-dashboard line +
views regen.

`$ARGUMENTS` bounds the sweep: empty = whole queue; `3` = first three
items; `15m` = time-box; `ingest` / `groom` / `research` / `custom` =
one kind; an item id = just that item.
