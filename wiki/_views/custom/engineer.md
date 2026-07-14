---
title: "Engineer view"
kind: meta
status: living
updated: 2026-07-14
confidence: high
sources:
  - ../../../views/engineer.yml
---

# Engineer view

What changed in the decision trail, what the brain wants deepened, and the production surfaces at a glance.


## Recent decisions

- [Give recurring tend-queue items an operator acknowledgement path](/brain/adrs/acknowledge-recurring-tend-items/) — accepted · updated 2026-07-12
- [The briefing is a build-time derivation; summaries live in frontmatter; attention verdicts live on inbox items](/brain/adrs/human-legible-presentation-layer/) — accepted · updated 2026-07-12
- [The kernel's interaction surfaces are MCP and the CLI — the embedded terminal retires with the chat pane](/brain/adrs/mcp-cli-surface/) — accepted · updated 2026-07-12
- [Public artifacts carry no personal data; a deterministic guard strips session URLs regardless of harness behaviour](/brain/adrs/no-personal-data-in-public-artifacts/) — accepted · updated 2026-07-12
- [Playthroughs are executed skills with immutable transcripts; synthetic findings are confidence-capped insights](/brain/adrs/persona-playthrough-loop/) — accepted · updated 2026-07-12
- [Uniform loopback Host-header guard across both HTTP serving surfaces](/brain/adrs/sam-uniform-loopback-host-guard/) — accepted · updated 2026-07-12
- [Connectors are pull-only snapshot-writers: immutable dedup-keyed files under sources/, cursors in state, inbox items out — never a wiki write](/brain/adrs/connector-snapshot-contract/) — accepted · updated 2026-07-10
- [Home page is the wiki index as an agent-maintained dashboard](/brain/adrs/home-content-shape/) — accepted · updated 2026-07-10
- [Instances are born by manifest: init --full copies the mechanism and the kernel's decision trail, scaffolds the rest fresh](/brain/adrs/kernel-manifest-instancing/) — accepted · updated 2026-07-10
- [Epics are single-page umbrella artifacts with parent_epic linkage, validator-enforced no-umbrella-ADR, epic-aware briefs, and a quiet-on-day-one promotion heuristic](/brain/adrs/multi-prd-epic-shape/) — accepted · updated 2026-07-10

## Research queue (deepening picks)

No deepening picks queued — the link-health producer adds them.

## Load-bearing pages by inbound links

| path | confidence | inbound |
|---|---|---|
| brain/adrs/mcp-cli-surface.md | medium | 6 |
| brain/state.md | medium | 5 |
| brain/adrs/multi-prd-epic-shape.md | high | 4 |
| brain/adrs/queue-and-tend-inbox.md | high | 4 |
| brain/adrs/successor-ssg-for-ui.md | high | 4 |
| brain/epics/event-driven-agent-triggers.md | low | 4 |
| brain/topics/one-point-oh-criteria.md | medium | 4 |
| brain/adrs/connector-snapshot-contract.md | medium | 3 |
| brain/adrs/home-content-shape.md | medium | 3 |
| brain/adrs/human-legible-presentation-layer.md | medium | 3 |

## Production state (Datadog)

*Nothing here right now.*

---

*Generated from [`views/engineer.yml`](../../../views/engineer.yml) by `brain.py views` · audience: team/engineer.*