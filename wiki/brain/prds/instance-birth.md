---
title: "Instance birth — init --full creates a working brain instance from the kernel manifest"
kind: initiative
status: living
updated: 2026-07-10
confidence: medium
supersedes: brain/pitches/instance-birth.md
summary: >
  init --full births a working instance from the kernel manifest: mechanism plus kernel trail, no dogfood, git-initialised, gates passing — the adoption path for real projects.
sources:
  - ../pitches/instance-birth.md
  - ../../../sources/conversations/2026-07-10--tool-repo-constraint.md
---

# Instance birth

## What

One command creates a working brain instance at a target path: the
whole mechanism, the kernel's own documentation trail, none of the
tool repo's self-tracking content. The instance passes its own
gates immediately (validate, views, doctor) and is ready for
`setup` + first ingest.

## How

A kernel manifest — data in the CLI, one list of copy-paths and one
of scaffold-fresh surfaces — drives an `init --full` mode beside
the existing thin `init`. The manifest boundary: mechanism and its
documentation cross; observations and self-tracking never do. The
birth is exercised end-to-end in this repo's test suite, which
doubles as the first 1.0 criterion's executable form.

## Why

The operator's standing constraint makes instances the only
adoption path — so instance birth *is* the product's delivery
mechanism, and "happy with the outcome" is meaningless until a
birth is one clean command.

## Now

Shipped 2026-07-10 with the bet: manifest + `init --full` + the
end-to-end birth test (create, validate, doctor, delete) green.

## Perceived

Fresh. Risk to watch: manifest drift — a new kernel file that
someone forgets to add to the manifest ships in this repo but not
in instances. The birth test catches missing load-bearing files;
a reflection detector could later diff the manifest against the
tracked tree.

## Target

A real instance born for the first adopted project, once 1.0
criteria pass. CI release artifacts (tarball of a born instance)
as a follow-up if distribution beyond this machine is wanted.
