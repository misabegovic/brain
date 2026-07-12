---
persona: .claude/personas/users/noor-cold-start-adopter.md
scenario: the full first-session tutorial (deck slide 11), executed end-to-end against a born instance
version: 0.19.0
date: 2026-07-12
executed_by: claude (fable 5)
context: >
  The operator delegated the cold-start test to the agent ("I don't
  want to point anyone to anything. You do it."). This walk executes
  the tutorial script the deck teaches, against a freshly born
  instance with a real OSS repo — the closest executable stand-in
  for the human cold-start run, recorded as such.
---

# Delegated cold-start — the tutorial, end to end (2026-07-12)

Environment: `init --full` instance ("Acme") in a scratch
directory; a real OSS sibling repo (a markdown editor) as the first
project. Every step actually executed; machine side-effects avoided
by the non-interactive consent guard (0.16.0 fix) doing its job.

## Step 0 — birth

`brain.py init <path> --full --org "Acme"` → "kernel 0.19.0 ·
validate+views green". Clean.

## Step 1 — setup

**Finding A (tutorial gap, transcript-only).** Piping the repo name
to `setup` does nothing: non-interactive mode skips the org/repos
*questions* along with the consents, so the answer is silently
unconsumed. The scripted path is `setup --repos <r> [--org X]` —
which worked. The deck/tutorial says plain `setup`, which is right
for interactive humans; scripted adopters need the flags (README
documents them).

**Finding B (defect, fixed in-session).** `setup` ended with the
doctor checklist but never said what to type next — and the
quickstart's third command is exactly the fragile step the standing
insight names. `setup` now ends with `next: brain` or
`next: tools/brain`, whichever is *verified to work* on that
machine.

## Steps 2–3 — the app + install-agent

`serve` on a fresh instance showed the first-run placeholder, the
status poll kicked the first build (npm deps installed), and the
briefing rendered.

**Finding C (defect, fixed in-session).** The "this brain is empty —
feed it" guidance never fired: a born instance carries the kernel's
own ADR trail, so the `live.length <= 2` heuristic was never true.
Now keyed on "no project content outside brain/ + org/". Verified:
the instance briefing shows the guidance; the tool's own repo does
not.

`install-agent claude` → "unchanged" (the kernel manifest had
already crossed `.mcp.json`) — correct idempotence.

## Step 4 — first ingest (real data)

the repo's shelf authored: index + purpose + architecture +
state, citations to real repo paths, `confidence: low`, unknowns
marked "(unknown — needs source)". The instance's own gates
enforced the conventions on me: the orphan check refused the new
shelf until the home page linked it (the pairing rule teaching the
adopter), and the instance's pre-commit hook validated the commit.
Landed as `5298f92` in the instance.

## Step 5 — ask

`search 'harness integrations editor'` returned the new shelf's
architecture page (ranked under a kernel ADR — the source-factor
weighting being honest about `confidence: low` first-pass pages).

## Step 6 — tend

`schedule run --target inbox-refresh` → clean; queue empty (fresh
cursor init, no half-life crossings). The loop closes.

## Give-up verdict (in character, Noor)

"Post-fixes: nothing stops me. The moment that sold me was the
validator refusing my orphan page and telling me exactly what to do
— the tool teaches its own conventions. The setup now telling me
what to type next removes my last dead end."

## 1.0-gate relevance

- **Criterion 3 (real-data loop in a born instance):** demonstrated
  — birth → setup → real ingest → gates → commit → search → tend,
  all inside the instance.
- **Criterion 4 (cold-start onboarding test):** executed by the
  agent under explicit operator delegation. Recorded honestly: this
  is the playthrough protocol standing in for a human at the
  operator's direction, not a human run.

## Disposition

- Finding A — transcript-only (documented behaviour; deck already
  aims at interactive humans).
- Findings B, C — fixed in-session.
- Insight `quickstart-third-command-fragility` — its failure mode
  reproduced (non-interactive skip → `brain` absent), its fix
  implemented (verified next-command print), and the operator's
  machine given a working `brain` on PATH.
