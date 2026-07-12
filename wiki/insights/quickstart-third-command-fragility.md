---
title: "The quickstart's third command (`brain`) is fragile on cold-start machines"
kind: insight
status: draft
updated: 2026-07-12
confidence: low
affected_personas:
  - .claude/personas/users/noor-cold-start-adopter.md
sources:
  - sources/playthroughs/2026-07-12--noor-cold-start-adopter--readme-quickstart.md
---

# The quickstart's third command (`brain`) is fragile on cold-start machines

**Playthrough-born hypothesis** — synthetic finding from the Noor
cold-start walk; capped at `confidence: low` until a human
cold-start run confirms or refutes it.

## Pattern

The README quickstart promises three commands; the third (`brain`)
only works if a chain of optionals held: the setup PATH step was
offered *and* accepted (it is consent-gated, and skipped entirely
on non-interactive stdin), `~/.local/bin` exists *and* is on the
platform's PATH (true on most Linux shells, not on stock macOS),
and the shell has rehashed. Any broken link leaves a first-time
user with `command not found` on the exact command the README
centres, with no fallback shown at the failure point.

## Evidence

- `sources/playthroughs/2026-07-12--noor-cold-start-adopter--readme-quickstart.md`
  — the walk itself: the PATH step is one consent among several,
  and the non-interactive consent fix (Finding A) makes skipping
  it *more* likely, sharpening this gap.
- The playthrough suggests, does not prove: the walk ran on Linux
  with `~/.local/bin` present and on PATH; the macOS/no-PATH leg
  is reasoned, not executed.

## Affected personas

- [Noor — cold-start adopter](../../.claude/personas/users/noor-cold-start-adopter.md)

## Implications

- Suggests `setup` should end by printing the exact next command
  that is *known to work* on this machine (`brain` if resolvable,
  else `tools/brain`), rather than assuming the README's word.
- Suggests the README quickstart could hedge the third line
  (`brain   # or: tools/brain`).
- Likely candidate for a fix alongside the 1.0 cold-start human
  test — that run doubles as this insight's confirmation.

## Status

Open. Awaiting a real cold-start run (the 1.0 gate's human test is
the natural confirmation vehicle). Do not raise confidence on
synthetic evidence alone.
