---
name: tend
description: Digest the brain's inbox — the queue of pending synthesis work accumulated by the deterministic producers (cursor diffs, half-life crossings, link health, connector batches, operator-defined producers). Load when the user says "tend", "do the inbox", "digest the queue", "catch the brain up", or invokes /tend. The in-session half of the queue-and-tend loop per wiki/brain/adrs/queue-and-tend-inbox.md.
---

# tend — digest the inbox

The queue-and-tend split: a local timer runs deterministic producers
that accumulate pending work into `wiki/_state/inbox/` (one JSON item
per file); `/tend` is where the model half happens — inside the
operator's normal session, visible and implicitly supervised. This
skill never runs on a schedule.

## Protocol

### 1. Read the queue

```bash
python3 tools/brain.py inbox list --json
```

Empty → say so and stop. Otherwise deserialize; items arrive
priority-ordered (high → normal → low), then oldest-first.

### 2. Parse the budget

The invocation may carry a bound: `/tend` (whole queue), `/tend 3`
(first N items), `/tend 15m` (time-box — stop starting new items
past the bound), `/tend ingest` (one kind only), `/tend <id>` (one
item). Announce the plan in one line before starting: item count,
order, budget.

### 3. Digest items, one at a time

Each item carries `kind`, `summary`, `source`, and an optional
`route` (a suggested skill invocation). The route is a hint, not a
command — judge from the summary whether it still fits.

| kind       | default handling                                                                                  |
|------------|----------------------------------------------------------------------------------------------------|
| `ingest`   | Follow the `/in` routing tables against `source`. For `cursor-diff-<repo>` items: sibling-repo handling first, then walk `brain.py sync-cursor diff <repo>`, synthesise into the repo's shelves, advance the cursor per the wiki-ingest protocol. |
| `groom`    | Apply the groom skill's judgement to the named page(s) — refresh-or-demote half-life crossings, fix link-health findings, supersede→archive transitions. |
| `research` | Deepdive per the shape skill's pre-flight discipline: fetch constraining context (sibling code, web sources read verbatim), snapshot findings into `sources/research/`, land the synthesis that earns the confidence bump with citations. |
| `custom`   | Judge from `summary` + `route`. When genuinely ambiguous, ask the operator one short question rather than guessing. |

Fan out per the parallel-first discipline when a single item has
parallel shape (multiple files to read, multiple pages to check).

### 4. Land and clear, per item

After each item's work is committed (LOCAL_FIRST: local commit +
audit-log line, exactly as any other operation):

```bash
python3 tools/brain.py inbox done <id>
```

Clear the item **in the same commit** as its synthesis where
practical — the diff then tells the whole story (work + queue
removal together). An item that turns out to be moot (trigger no
longer holds, duplicate) is cleared with a one-line note in the
commit body. An item too big for the session's budget is *not*
cleared — leave it queued, note the partial progress in the audit
line.

### 5. Close the sweep

- Home dashboard: update `wiki/index.md` § What changed with one
  line summarising the sweep (the home-pairing gate requires it
  whenever wiki content moved).
- Regenerate views; run validate + check as the pre-commit hook
  enforces.
- Report to the operator: items digested / cleared / deferred, and
  the new `inbox summary` line.

## Boundaries

- **Never author ADRs/PRDs from an inbox item.** If digestion
  surfaces a decision- or initiative-shaped need, stop and hand off
  to `/shape` (manual default) — tend is synthesis, not commitment.
- **Producers are not edited from here.** A producer that queues
  noise gets a note to the operator, not an in-sweep edit
  (`tools/**` is a restricted path).
- Confidence floor, `sources/` immutability, and all authoring
  conventions apply unchanged.
