---
title: "Operator intent — self-hosting, automation, external chat access"
captured: 2026-07-10
kind: conversation-snapshot
participants: [operator, brain-agent]
---

# Operator directive (2026-07-10, verbatim intent)

> Self hosting and automating so the brain self-maintains, ingests
> diffs, pulls from Slack, Notion, GitHub, does pruning, deepening of
> knowledge and research etc. Also a small roadmap of providing chat
> access to folks outside of the product. In a safe enterprise way,
> of course, while keeping the intent to use it locally for your
> work. Nothing urgent, just stuff that comes next in 0.x.0 versions.

Referenced for inspiration: <https://openknowledge.ai/> and
<https://github.com/inkeep/open-knowledge> (cloned to
`~/projects/open-knowledge` for study).

# Study notes — inkeep/open-knowledge (2026-07-10)

Local-first, git-backed markdown editor + MCP server ("Notion meets
VSCode") by Inkeep, GPL-3.0. Validates the brain's thesis: filesystem
as database, git as history, MCP as the agent surface, agentic
retrieval loop (search→grep→read→follow-backlinks) instead of a
vector store. No ingestion connectors (Notion/Obsidian are one-shot
import migrations; GitHub is the sync remote), no built-in end-user
chat surface, no governance rail (no confidence tiers, no
suggestion/approved separation, no human gates). Unattended ingestion
is delegated to an external cron/webhook gateway that wakes an agent.

Ideas worth stealing: reads that return graph context (backlinks +
outbound links + history per page read); link-graph health views
(dead / orphans / hubs / suggest) as a pruning input; source-id dedup
addressing making connector re-sync idempotent; write-time validation
returning broken-link warnings; per-author (human vs named agent)
attribution in history.
