---
title: "Instance birth — a clean kernel→instance path that carries the mechanism, never the dogfood"
kind: pitch
status: superseded
superseded_by: brain/prds/instance-birth.md
updated: 2026-07-10
confidence: medium
summary: >
  Superseded pitch: one command births a complete, gate-passing brain instance from the kernel. Graduated and shipped as init --full (0.11.0).
sources:
  - ../../../sources/conversations/2026-07-10--instancing-and-one-point-oh.md
  - ../../../sources/conversations/2026-07-10--tool-repo-constraint.md
---

# Instance birth

Pitch graduated in the same directive ("go on all"); kept as the
shaped record.

## Problem

The tool's repo is permanently its own project; adoption happens in
separate instances. But no clean birth path exists: cloning this
repo drags the entire dogfooding corpus (its roadmap, topics,
decisions-about-itself, sources) into a fresh project's brain — the
same contamination we solved extracting from the origin client
brain, now in reverse — while `brain.py init` creates a shell
*without* the tools, skills, or UI. An instance must get the whole
mechanism and none of the self-tracking content.

## Appetite

Small — one focused build. The kernel file-set is known; the open
question is only its boundary.

## Solution

A kernel manifest (data, in the CLI) drives `init --full <path>`:
copy the mechanism (tools, skills, commands, agent personas, UI
source, deploy profile, tests, schema, schedule, example view
specs), carry the kernel's own decision trail (the brain-meta ADRs
+ authoring playbook + org methodology — they document the tool the
instance runs), scaffold everything else fresh (config, wiki
skeleton, home, state, empty sources/log), git-init, and finish
with the doctor. The birth is tested end-to-end as part of this
repo's suite.

## Rabbit holes

Platform template repos (GitHub-coupled); release tarballs (a CI
follow-up, not the primary path); trying to make the instance track
the kernel as an upstream (git remains available for that; no
mechanism).

## No-gos

No dogfood content crosses: no roadmap, state, topics, pitches,
PRDs-about-the-tool, sources, log lines, or competitor shelf.
