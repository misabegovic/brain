---
title: "Research — throwaway SQLite index prototype over the live corpus"
captured: 2026-07-10
kind: research-note
method: local prototype (scratchpad; repo untouched)
---

# Prototype results

Built a disposable index over the live shell (24 pages, 52 links,
inbox, flattened _state surfaces) with system Python 3.12.3 /
SQLite 3.45.1:

- **Build: 19 ms. Size: 304 KB.** FTS5 present and working.
- Schema: `pages` (scalar columns + repos/affects as JSON),
  `links(src,dst)`, `inbox`, `state(surface,key,value)`, external
  FTS5 over title+body.
- Representative view blocks all worked as plain SQL:
  - recent accepted decisions (filter + sort);
  - **the 0.4 research picker reproduced in 5 lines of SQL** — same
    rows the Python producer queued (hubs with low/medium
    confidence, inbound ≥ 2);
  - bm25-ranked FTS search ('connector cursor' → the connector ADR
    first);
  - cross-plane join via json_each(repos) × inbox;
  - orphan anti-join (correctly empty);
  - state tiles from flattened _state JSON.

Conclusion: the derived-index design is validated end-to-end at
trivial cost; several existing Python producers could *become*
saved SQL queries over the index.
