---
title: "Research — second tend sweep: epic ADR, roadmap, operator-lessons verified"
captured: 2026-07-10
kind: research-note
method: /tend research items; claims checked against the shipped mechanism
---

# Tend sweep 2 verification (2026-07-10)

## brain/adrs/multi-prd-epic-shape.md → verified, high

Every mechanism claim checked against the shipped kernel:
parent_epic resolution + no-umbrella-ADR rule in the validator
(tools/brain.py — 12 parent_epic references, "epics have no
umbrella" check), epic required-sections registered, by-epic view
emitted by the views pipeline, child_prds/child_adrs reverse edges
computed through the same code path as affects/affected_by, /shape
--epic mode + epic-detection pre-flight in the shape skill,
epic-aware briefs in zoom-out, epic rows in /continue, template at
tools/templates/epic.md. All primary sources read today.

## brain/roadmap.md → verified, high

Every "shipped" claim checked by artifact existence: workbench
module, deploy profile (Dockerfile, entrypoint, compose,
railway.toml), view specs + rendered custom views, producer
template, timer installer, datasette launcher, and all five 0.x
decision ADRs (queue-and-tend, connector contract, sql-views,
workbench bridge, serving profile). 0.10 claims (topic kind,
constraints/implementation-memory in the schema) present. The
roadmap describes what exists.

## org/operator-lessons.md → verified, high

The shelf's convention text matches the operator-lesson ADR's
sub-shape (### slug, prose Why / How to apply / Graduated from);
the one lesson's referenced mechanisms (brain workbench, /tend,
VERSION discipline, /capture) all exist as shipped. Confidence
policy satisfied: every load-bearing claim cites primary sources
read today.
