---
title: "Instances are born by manifest: init --full copies the mechanism and the kernel's decision trail, scaffolds the rest fresh"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
summary: >
  Instances are born from an explicit copy-path manifest: mechanism and the kernel's decision trail cross; this repo's self-tracking dogfood never does. init --full is the only birth path.
sources:
  - ../prds/instance-birth.md
  - ../../../sources/conversations/2026-07-10--tool-repo-constraint.md
---

# Instances are born by manifest: `init --full` copies the mechanism and the kernel's decision trail, scaffolds the rest fresh

**Decision.** Instance birth is a CLI operation driven by an explicit
kernel manifest held as data in the CLI itself. The manifest names what
**crosses** into every instance — the tools, the skill and command
surface, the agent personas, the UI source, the deploy profile, the
tests, the schema, the schedule, the example view specs, and the
kernel's own documentation trail (the brain-meta decision records, the
authoring playbook, and the org methodology shelf, which document the
tool the instance runs) — and what is **scaffolded fresh** — the config,
the wiki skeleton with home and state pages, empty sources and log, an
environment example. The tool repo's self-tracking content (its roadmap,
state, topics, pitches, initiatives, observations, competitor shelf, and
audit history) never crosses. The born instance is git-initialised,
regenerates its views, and reports its health before the command
returns.

## Context

The operator fixed the frame: this repository is the tool's own project
permanently, so separate instances are the only adoption path — which
makes birth the delivery mechanism. The failure modes on either side
were both already lived: cloning carries the dogfood (the contamination
the original extraction from the client brain existed to remove), while
the thin `init` carries nothing and leaves instances dependent on this
checkout's tools through an environment variable. The manifest boundary
follows the line the extraction already drew and the skills already
depend on: skill protocols cite the kernel decision records by path, so
a mechanism without its trail would recreate the dangling-reference
class the standalone guarantee closed.

## Alternatives

- **Manifest-driven `init --full`** *(chosen)* — one explicit,
  reviewable boundary as data; birth testable in this repo's suite;
  no platform coupling.
- **Git clone plus a strip script** — starts from everything and
  subtracts; every new dogfood surface becomes a leak until someone
  updates the strip list. The manifest inverts the default to
  fail-closed. Rejected.
- **A platform template repository** — couples birth to one forge and
  drifts from the working tree between syncs. Rejected.
- **Release tarballs from CI** — right as a distribution follow-up,
  wrong as the primary path: it hides the boundary inside a pipeline
  instead of the CLI where the operator can read it. Deferred, not
  rejected.
- **Instances track the kernel as an upstream remote** — real merge
  machinery exists in git already; blessing a mechanism invites
  upgrade coupling the shell's portability posture avoids. Left to
  operators who want it.
- **Do nothing** — birth stays a hand-run extraction like the one
  that created this repo. Rejected: that took a session; it should
  take a command.

## Consequences

- **Closes** the contamination class in both directions: fail-closed
  manifest, dogfood never crosses, mechanism always does.
- **Opens** adoption as a one-command operation, and makes the first
  1.0 criterion executable (the birth test runs in CI).
- **Costs** manifest maintenance — a new kernel file must be added
  deliberately; the birth test catches load-bearing omissions, and a
  manifest-vs-tree reflection detector is the named follow-up if
  drift bites.

## Build notes

Shipped 2026-07-10. The born instance's wiki carries the kernel ADR
shelf read-only-by-convention (instances may supersede kernel
decisions with their own records); the birth test creates an
instance in a temporary directory, requires validate + views +
doctor to pass inside it, and confirms no dogfood paths crossed.
