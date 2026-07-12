---
title: "Conversation capture: briefing filters, dashboards, and the interactive channel"
kind: source
captured: 2026-07-12
participants: operator (Muhamed), claude (fable 5)
context: >
  Immediately after 0.17.0 shipped. The operator extended the
  presentation-layer bet with interaction and data-visualisation
  asks, and re-confirmed the remaining within-appetite items.
---

# Conversation capture — interactive briefing direction (2026-07-12)

**Operator (verbatim intent):** "ok, maybe we need pagination also
and filtering on the page to only show a type of item? also
dashboards for showing data in html components with numbers,
graphs, etc... also, should we make it interactive? so I can click
and mark something for execution, leave comments etc and the agent
can pick that up? do this and the things you mentioned are
remaining"

Four asks: (1) pagination + per-type filtering on the briefing;
(2) dashboards — numbers and graphs as HTML components; (3) an
interactive channel — click to mark for execution, leave comments,
agent picks it up; (4) the within-appetite remainders (trail
timeline, link-graph visual).

**Design note recorded at decision time:** ask (3) bends the
presentation-layer ADR's "UI stays read-only" consequence. The
resolution that keeps every other guarantee intact: the UI's write
surface is the **inbox** — clicking "queue for the agent" or
leaving a comment POSTs to the local server, which appends a
normal inbox item (`produced_by: ui-action`); the next tend
session digests it. The UI still never writes the wiki, no second
content store appears (the inbox was always the human↔agent seam),
and the channel is structurally absent in serving mode (POST only
mounts locally, like the app page). Cross-origin abuse is blocked
by requiring a custom header (forces a CORS preflight the server
never grants) plus the existing Host check. Recorded as an
amendment on the presentation-layer ADR — the direction (UI
derives from the wiki; humans act through their agent) is
unchanged; the click is just a faster way to hand the agent work.
