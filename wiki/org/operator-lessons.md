---
title: "Operator lessons"
kind: reference
status: living
updated: 2026-07-10
confidence: medium
sources:
  - ../../.claude/skills/capture/SKILL.md
---

# Operator lessons

Durable lessons the operator teaches the agent — corrections and
confirmed approaches worth applying beyond the session they came up
in. `/capture` routes lesson-shaped signal here (see the
[operator-lesson pattern ADR](../brain/adrs/operator-lesson-pattern.md)).

Each lesson is one `### <slug>` subsection (kebab-case, ≤ 6 words): a
short prose *Why* paragraph naming the incident or constraint that
produced it, a short prose *How to apply* paragraph naming when and
where the rule kicks in, and an inline *Graduated from* citation
pointing at the memory entry or source it came from. Newest first.
Repo-bound lessons live on that repo's `permanent/conventions.md`
instead; a repo-specific lesson lands here with a *Scope:* note only
while that conventions page doesn't exist yet.

*(none yet)*
