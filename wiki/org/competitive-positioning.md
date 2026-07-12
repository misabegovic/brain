---
title: "Competitive positioning — the brain kernel"
kind: reference
status: living
updated: 2026-07-10
affects:
  - brain
confidence: low
sources:
  - wiki/org/competitors/codeplain/index.md
  - ../../sources/research/2026-07-10--openknowledge-terminal-architecture.md
  - ../../sources/research/2026-07-10--composable-views-prior-art.md
---

# Competitive positioning — the brain kernel

> **Agent-authored synthesis.** Descriptive positioning inferred
> from public material and local repo study; not a human-approved
> strategy statement. For a human to review and correct.

## Category

The brain kernel competes in the emerging category of
**LLM-maintained knowledge substrates** — adjacent to, and partly
overlapping, **spec-first development**. The shared thesis: the
durable artifact of an organisation is its synthesis (specs, ADRs,
PRDs, permanent knowledge), maintained by agents against immutable
sources, with code as a downstream, regenerable consequence.
Codeplain's June 2026 seed round validates the thesis commercially
from the codegen side ([competitor page](competitors/codeplain/index.md));
open-knowledge validates the markdown + git + MCP substrate from the
editor side; the prior-art trail (Obsidian Bases, Notion views,
Datasette) shows the demand for composable views over such corpora
while exposing the lock-in and performance failure modes the kernel
deliberately avoids (research notes, 2026-07-10, in
`sources/research/`).

## Positioning table

| Player | What it is | Their bet | Where we differ |
|---|---|---|---|
| **Brain kernel** (us) | Open, local-first knowledge substrate maintained by agents under a governance rail | The *maintained synthesis* is the product; regeneration, views, and serving are consequences | — |
| **open-knowledge** | Editor-first Electron desktop app over markdown + git + MCP, with embedded terminal and harness launches | The human's *editing session* is the centre; agents are launched alongside | We are agent-first: the substrate carries its own maintenance mechanism (skills, inbox, producers, audit); no desktop app dependency |
| **Codeplain** | Venture-backed spec-driven code-regeneration platform ($3M seed, 2026-06) | Specs in, tested production code out — codegen is the product | Regeneration is our mission #1 but one output among several; we add governance, provenance, and the operational loop their public story lacks |
| **Plain wikis / Notion** | Human-authored knowledge bases; Notion sets the views UX bar | Humans keep docs current by discipline | No agent maintenance mechanism at all — and Notion's export drops the computed layer (lock-in); our views are git files rendering to markdown |

## Defensible differentiators

- **Governance rail.** Confidence floor, `ai-suggestions/`
  separation from human-approved shelves, human gates on
  commitment-class artefacts, additive-only `sources/`, and an
  audit log distinguishing human from agent authorship. None of
  this appears in competitors' public stories.
- **Queue-and-tend economics.** No LLM ever runs on a schedule:
  deterministic producers accumulate an inbox, operator sessions
  digest it. Inference cost is bounded by presence, not cron.
- **Instance-birth distribution.** `init --full` births a working
  instance from the kernel manifest — distribution is a repo, not
  a hosted platform, so adoption carries no vendor dependency.
- **Harness independence.** Gates live in git/CI, not in any one
  agent product; per-harness adapters (`install-agent`) and an
  MCP-first serving plane mean any agent harness works.
- **Bring-your-own-harness.** Bare `brain` opens the live
  knowledge with ambient health; any MCP-aware harness or chat
  client is the conversation surface (`install-agent`) — the kernel
  ships no chat, terminal, or per-seat AI billing of its own.

The moat, in one line: competitors ship an editor or a codegen
pipeline; the kernel ships the *institution* — rules, economics,
and distribution — that keeps an agent-maintained corpus
trustworthy over time.
