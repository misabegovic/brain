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



### develop-the-brain-inside-the-brain

*Why* — the operator directed (2026-07-10) that the brain repo is a
standalone project whose own evolution is its first workload: every
pitch, decision, build, and lesson about the brain lands in the
brain, or the substrate's claim to be a working memory is theatre.
The 0.x arc was built this way and the trail (pitches → PRDs → ADRs
→ audit log) is the proof.

*How to apply* — when working on the brain itself: open the
workbench (`brain workbench`) so the rendered corpus sits beside the
terminal; capture intent before building (`/capture`, `/shape
--pitch`); let `/tend` drive maintenance; record mechanism decisions
as brain-meta ADRs and bump `VERSION` when a roadmap slice ships.
Work products that live outside the repo (scratch files, untracked
notes) are the smell to correct.

*Graduated from* — the operator's 2026-07-10 session directive
(sources/conversations/ holds the arc's capture trail).
