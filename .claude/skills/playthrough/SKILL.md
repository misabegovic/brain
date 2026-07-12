---
name: playthrough
description: Walk the product as a user persona — real execution, not simulation. Load when the user says "playthrough", "walk the product", "test as a user", "persona sweep", or invokes /playthrough, or when tending a playthrough-<version> inbox item. Executes a scenario against the running product as one persona from .claude/personas/users/, snapshots the transcript to sources/playthroughs/, and routes findings worth a human decision to wiki/insights/ at confidence: low. Per wiki/brain/adrs/persona-playthrough-loop.md.
---

# playthrough — walk the product as a user

Synthetic user testing with structural honesty: the agent *becomes*
one persona and *actually operates* the product — real commands,
real pages, real output. A playthrough that imagines results
instead of producing them is invalid. Findings are hypotheses, not
user feedback; the provenance path and the confidence cap keep that
distinction machine-checkable.

## Protocol

### 1. Pick persona and scenario

`/playthrough <persona> [<scenario>]`. Personas live in
`.claude/personas/users/` — match on filename fragment (`noor`,
`cold-start`, …). With no argument, pick the persona whose
anchored scenarios (listed in each persona file) best cover what
changed since the last sweep (`CHANGELOG.md` top entry is the
guide; a `playthrough-<version>` inbox item names the version).
Say which persona and scenario you picked and why before starting.

A sweep (`/playthrough sweep` or a tended inbox item) means: one
scenario for each persona whose surfaces the release touched,
budgeted like `/tend` — say the plan first.

### 2. Read the persona, adopt the frustrations

Read the persona file fully. The goals define the scenario's win
condition; the frustrations define the give-up points you must
actively probe — not avoid. At least once per playthrough, ask in
character: *"would I have given up here?"* and answer honestly.
This is the counterweight to self-confirmation: you built this
product; the persona did not.

### 3. Execute for real

Run the scenario against the actual product:

- Commands actually run (`Bash`), pages actually fetched (the local
  server, the rendered site), output actually read. Screenshots
  where layout matters.
- Stay in character for judgement calls: what the persona would
  type, where they would click, what they would *not* know to do.
- Cold-start scenarios use a fresh surface (a scratch `init --full`
  instance or a clean checkout), never the operator's live state.
- Never fabricate output. If a step can't be executed (missing
  dependency, needs a human), record that as a finding — it is one.

Narrate as you go: step, expectation, what actually happened,
friction felt (in persona voice, briefly).

### 4. Snapshot the transcript

Write `sources/playthroughs/YYYY-MM-DD--<persona-slug>--<scenario-slug>.md`
with frontmatter (`persona:`, `scenario:`, `version:` from
`VERSION`, `date:`) and the full narrated walk including real
command output excerpts. Sources are additive-only; a re-run is a
new file, never an edit.

### 5. Route findings

Triage what the walk surfaced:

- **Defect or friction a human should decide about** → one
  `kind: insight` page in `wiki/insights/` (template
  `tools/templates/insight.md`): `confidence: low`,
  `affected_personas:` pointing at the persona file, `sources:`
  citing the transcript. **The cap is structural: an insight whose
  only sources are `sources/playthroughs/` stays at
  `confidence: low`** — it may rise only when a human (cold-start
  tester, operator, or `/feedback`-ingested user report) confirms
  it, cited as an additional source.
- **Small friction below the decision threshold** → stays in the
  transcript; don't inflate the shelf.
- **Outright bug you can fix mechanically** → fix it in the same
  session (normal LOCAL_FIRST commit), and still record it in the
  transcript; the insight page is only needed if the bug reveals a
  pattern worth a product decision.

Link new insight pages from `wiki/index.md` (or the insights index
once one exists) so the orphan gate passes.

### 6. Close the loop

- Tended from an inbox item → `brain.py inbox done <id>`.
- Run the gates (`validate`, `check --no-net`, `views`), commit
  per LOCAL_FIRST with the audit-log line.
- Report in one paragraph: persona, scenario, steps executed,
  findings by disposition (insight / transcript-only / fixed), and
  the give-up-point verdict.

## What this skill never does

- Never presents a synthetic finding as user feedback — the words
  "users want/said/feel" are banned in playthrough-born insights;
  write "the <persona> playthrough suggests".
- Never raises a playthrough-born insight past `confidence: low`.
- Never simulates output it could execute, and never executes
  against the operator's live corpus in a destructive way —
  cold-start walks use scratch instances.
- Never runs on a schedule. The producer queues; sessions play.
