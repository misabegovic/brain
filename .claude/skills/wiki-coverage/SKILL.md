---
name: wiki-coverage
description: Run repo-vs-brain coverage analysis — for a sibling repo, list which top-level directories are covered by wiki pages claiming that repo, which are gaps, and (optionally) write a `kind: reference` coverage page summarising the result. Load when the user says "coverage", "what's the brain miss for X", "what's uncovered in repo Y", or otherwise asks how complete the brain is for a given repo.
---

# Repo coverage gap analysis

You are working in `~/projects/brain`. Goal #1 of the brain is that
codebases could be regenerated from the specs stored here. This skill
turns "could we regenerate it?" from gut feel into a measurable answer
for one repo at a time.

## When to run

- The user asks "how much of <repo> does the brain cover?"
- Before promising a regeneration test of any sibling repo.
- Periodically as a corpus-health signal — uncovered % over time should
  trend down.
- Before starting a `/ingest` pass on a sibling repo, to see where to
  spend time.

## Inputs

- `/coverage <repo-name>` — sibling repo name (under `~/projects/`).
- `/coverage` (no arg) — ask which repo.

## Protocol

### 1. Run the mechanical pass

```bash
python tools/brain.py coverage <repo>
```

Output lists:

- pages claiming this repo (`repos: [...]` includes `<repo>`),
- top-level directories covered (mentioned in any of those pages),
- top-level directories uncovered.

Read the full output. Don't summarise from the percentage alone — the
*identity* of uncovered dirs matters more than the count.

### 2. Interpret the gaps

For each uncovered directory, decide:

- **Genuine gap.** Significant code lives here and the brain should cover
  it. Mark as a `/ingest` candidate.
- **Trivial / generated.** `bin/`, `public/`, `patches/`, etc. — fine
  to leave uncovered, but note that the heuristic is over-reporting.
- **Already covered indirectly.** A subfolder is described by a deeper
  sibling-repo cite from another page. Mark as "covered, not
  surfaced" — recommend cross-linking.

The mechanical pass does substring matching on dir names; it cannot
distinguish these on its own.

### 3. Run mempalace search to validate

For each "genuine gap" dir, run:

```bash
mempalace search "<repo>/<dir>"
```

If the palace shows recent material from that path, an `/ingest` pass
is likely cheap (mempalace already has the verbatim).

### 4. Decide on the artefact

Three options based on the user's request and the gap density:

- **Just report.** If the user asked "what's covered?" verbally, output
  a structured summary and stop.
- **Append to the existing reference page.** If the repo already has a
  `kind: reference` page (e.g. `<repo>.md`), update its `## Open
  threads` with the gap list. Bump `updated:`. Append to
  `log/log.md`.
- **Write a dedicated coverage page.** Only if the user explicitly
  asks for a standing artefact, *or* the repo has no reference page
  yet. Use `kind: reference`; sections suggested by the template plus
  an explicit `## Coverage` section listing covered / uncovered /
  notes. Cite `tools/brain.py coverage` output as the source.

Don't auto-create a coverage page on every `/coverage` run — that
would litter the wiki with auto-generated pages that aren't really
synthesis.

### 5. Cross-link

If the coverage report is appended to an existing reference page,
ensure the page's `## Open threads` lists each genuine gap as
`(needs source — ingest)`. This is what `/lint` will surface as work
on subsequent sweeps.

### 6. Log

```
YYYY-MM-DD coverage — <repo>: <covered>/<total> dirs covered;
   gaps: <list of genuine-gap dirs>
   action: <reported | appended to <page> | wrote <page>>
```

## What coverage is *not*

- **Not a proof of regenerability.** Mentioning a directory in a
  reference page is the floor, not the ceiling. A repo can be 12/12
  covered and still uncrenable if the pages are thin.
- **Not authoritative for "does the brain know X."** It's a
  directory-level heuristic. A page may describe a system that lives
  in a directory not currently named in the page; this skill won't
  catch that.
- **Not a license to delete files.** The brain doesn't delete code; it
  doesn't even read code that isn't surfaced through `/ingest`.

## Done check

- [ ] `python tools/brain.py coverage <repo>` was run and its output
      was read in full.
- [ ] Each uncovered dir was classified (genuine / trivial / covered
      indirectly).
- [ ] If an artefact was produced, it cites the brain.py output as a
      source.
- [ ] `log/log.md` records the run.
- [ ] Reference page (if updated) bumped its `updated:` date.
