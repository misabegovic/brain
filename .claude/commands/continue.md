---
description: Resume in-flight /shape work — detect phase, ingest new context, pre-push verify per AGENTS.md rules 4+5
---

Apply the `continue` skill to: $ARGUMENTS

`$ARGUMENTS` formats:

- `<slug>` — continue work on `wiki/<repo>/{prds,adrs}/<slug>.md`.
- `<PR#>` — continue work tied to a brain or sibling-repo PR.
- (empty) — list in-flight `/shape` work and ask which to continue.

The skill detects what phase the work is in (PRD draft → Phase 2 ADR
authoring → Phase 3 build → Build notes after merge), surfaces any
new context (PR comments, new sources) that arrived since the last
run, runs pattern-fit (rule 5) + local-CI-verify (rule 4) checks
before any code change leaves local, and stops at `/shape` phase
boundaries for human approval.

Pairs with `/shape` (which starts new work) and `/in` (which ingests
fresh sources unrelated to in-flight work). Refuses anything that
needs a fundamental re-pitch — surfaces the issue and asks whether
to re-shape.
