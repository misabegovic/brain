---
persona: .claude/personas/users/viktor-daily-operator.md
scenario: daily tend loop + timer/doctor health honesty + queue quality (agent sweep)
version: 0.19.3
date: 2026-07-12
executed_by: "claude (fable 5) — agent"
---

# Viktor, daily operator — the morning loop, health honesty, and the cries-wolf probe (2026-07-12)

Environment: live server at `localhost:8765` serving the primary
checkout at `~/projects/brain`; CLI probes run against both the
primary checkout (Viktor's real instance) and an isolated worktree
(for the destructive nag experiment, so the operator's live queue
is never touched). Every command below actually ran; output
excerpts are verbatim.

Viktor's win condition: the queue tends in minutes, the health
signals are honest, nothing nags, nothing bills without him
saying so. His give-up points, actively probed: an inbox that
cries wolf; a health strip that lies; a billing surprise.

## Step 1 — the morning glance

Expectation: `brain` strip says whether there's work; doctor tells
the truth.

```
$ python3 tools/brain.py inbox summary
brain inbox: empty

$ python3 tools/brain.py status   (excerpt)
corpus: 52 pages
  by confidence: high=7, low=4, medium=41
ai-suggestions: 0 pending review, 0 graduated
```

Doctor on the primary checkout (Viktor's instance):

```
$ cd ~/projects/brain && python3 tools/brain.py doctor
  ✓ operating mode       local-first (single operator)
  ✓ pre-commit gate      installed
  ✓ accumulation timer   brain-brain-974d60-schedule.timer active (daily run-due)
  ✓ tend queue           empty
  ✓ billing check        no API-key env vars — harness sessions bill your logged-in subscription
  10 checks — 0 failing, 1 warning(s)
```

Viktor: fine, ten seconds, mostly green. But wait.

## Step 2 — two surfaces disagree about the operating mode

The `/dash` header reads **"52 pages · local-first mode"** and the
health list shows **"✓ operating mode local-first (single
operator)"**. The briefing at `/` — same server, same corpus —
says in its orientation strip: **"PR mode is the operating mode
(2026-07-12). The operator removed `LOCAL_FIRST` from this
brain's `.env`"**.

Ground truth, the primary checkout's `.env`:

```
$ cat ~/projects/brain/.env
# Machine-local toggles. Copy to .env (git-ignored) and edit.

# LOCAL_FIRST=true suspends the PR/CI ritual for single-operator
# sessions: work lands as local commits on the current branch, all
# validations still run locally. See AGENTS.md § Governance.
# LOCAL_FIRST removed by operator direction 2026-07-12 — PR mode active.
```

`LOCAL_FIRST` is **not set** — the operator explicitly removed it
today. The instance is in PR mode. Doctor and `/dash` report
local-first with a green tick.

Root cause, `tools/brain.py` (doctor's operating-mode check):

```python
env_path = REPO / ".env"
if env_path.exists():
    local_first = "LOCAL_FIRST=true" in env_path.read_text()
```

A naive substring match. The `.env.example` boilerplate — which
the fix command `cp .env.example .env` itself installs — contains
the *comment* line "`# LOCAL_FIRST=true suspends the PR/CI
ritual…`", so the substring matches documentation, not
configuration. AGENTS.md's own canonical check is anchored:
`grep -q '^LOCAL_FIRST=true$' .env`. Doctor re-implements the
predicate and diverges from it. Any operator who keeps the
shipped explanatory comment gets the wrong governance mode
reported as healthy, forever.

Viktor, in character: *"The dash says local-first, my own
briefing says PR mode. One of these is lying about how changes
land in my corpus. This is exactly the 'healthy while broken'
strip I quit tools over."* This is a governance-load-bearing
misreport: an agent (or the operator) trusting doctor's line
could treat the instance as local-first — commit to the current
branch, skip PRs — against explicit operator direction issued
the same day.

**Finding 1 (defect, mechanical fix available):** doctor's
operating-mode check must use the same anchored predicate as the
governance contract (`^LOCAL_FIRST=true$`, comments excluded).
One-line fix in `tools/brain.py`; `/dash` inherits it. Recorded
here for a normal fix commit — the pattern-level lesson (health
checks re-implementing governance predicates and drifting) is
folded into the ADR suggestion's open questions.

## Step 3 — timer honesty

Expectation (Viktor's trap #2): strip says timer fine while it's
been dead for days. Verified against systemd directly:

```
$ systemctl --user list-timers --all | grep brain
Mon 2026-07-13 06:15:00 CEST 15h  Sun 2026-07-12 06:15:28 CEST 8h ago  brain-brain-974d60-schedule.timer

$ systemctl --user status brain-brain-974d60-schedule.service  (excerpt)
   Active: inactive (dead) since Sun 2026-07-12 06:15:28 CEST; 8h ago
   Main PID: 1819324 (code=exited, status=0/SUCCESS)
```

Timer active, last run this morning, exit 0. Doctor's ✓ is
truthful here. Pass.

## Step 4 — queue liveness and quality

Mid-walk, an item arrived in the primary inbox (produced by
another session's UI comment action):

```
$ python3 tools/brain.py inbox list
[normal]   custom  ui-comment-20260712-144654  (2026-07-12)
         operator comment on security-review: "sam adversarial probe 2026-07-12"  → /tend ui-comment-20260712-144654

$ python3 tools/brain.py doctor | grep "tend queue"
  ✓ tend queue           1 pending
```

Doctor picked the new item up immediately on re-run — the queue
signal is live, not cached. The item is real work (a routed
operator comment), not machinery noise. The UI's
comment-to-inbox channel demonstrably works end-to-end. Queue
quality: pass.

## Step 5 — the winning moment: search for a forgotten decision

```
$ python3 tools/brain.py search 'queue tend timer accumulate' --top 3
 59.80  [h] brain/adrs/queue-and-tend-inbox.md
        Self-maintenance is queue-and-tend: deterministic producers accumulate
        a per-item inbox; synthesis digests in-session via /tend — never on a schedule
```

Instant, correct, confidence-labelled. The decision Viktor
recorded and forgot comes straight back. Pass — this is the
moment that keeps him.

## Step 6 — billing probe

Doctor's billing check is explicit and honest (no API-key env
vars; sessions bill the logged-in subscription). The schedule was
audited for hidden LLM runs:

```
$ python3 tools/brain.py schedule list  (excerpt)
  ✓  monthly   brain-repo-truth-verification
      Heuristic + LLM-grade verification that brain claims still match repo state.
```

That description reads like a scheduled LLM run — Viktor's red
line. The handler (`brain.py reflection-check repo-claims`) is in
fact documented in source as "Mechanical-only — no LLM
verification of code semantics." No billing exposure exists, but
the truth lives only in the source; the operator-facing label
says the opposite of the ADR's "no LLM ever runs on the
schedule" guarantee.

**Finding 2 (small friction, transcript-only):** relabel
`brain-repo-truth-verification`'s description to match its
mechanical-only handler.

## Step 7 — the nag experiment (isolated worktree, scratch page)

Viktor's frustration #1 verbatim: "queue items that reappear
after being handled, or flag policy-correct pages." Code reading
showed `inbox done` deletes the item file while `inbox-refresh`
"upserts while the trigger holds" and never consults the
operator's `inbox grade` calibration in
`wiki/_state/attention-grades.json`. Proven empirically against a
scratch high-confidence page dated 72 days back (created in the
isolated worktree, deleted after):

```
$ python3 tools/brain.py schedule run --target inbox-refresh
inbox-refresh: 2 added, 0 refreshed, 0 cleared; 2 pending total
[   low]    groom  half-life-brain-viktor-nag-probe-md  (2026-07-12)
         brain/viktor-nag-probe.md: confidence:high but 72d since update (30d refresh rule) — refresh or demote  → /groom

$ python3 tools/brain.py inbox done half-life-brain-viktor-nag-probe-md
inbox: cleared half-life-brain-viktor-nag-probe-md

$ python3 tools/brain.py schedule run --target inbox-refresh   # "next morning"
inbox-refresh: 1 added, 1 refreshed, 0 cleared; 2 pending total
[   low]    groom  half-life-brain-viktor-nag-probe-md  (2026-07-12)
         brain/viktor-nag-probe.md: confidence:high but 72d since update (30d refresh rule) — refresh or demote  → /groom
```

Cleared with `done`; back the very next producer run. The
structural trap: the only ways to make the trigger clear are (a)
bump `updated:` — which AGENTS.md forbids unless content actually
changed — or (b) demote `confidence:` — wrong when the page *is*
still accurate. An operator who re-verifies a page and finds it
correct has **no policy-correct way to say so**. Every
high-confidence page that crosses 30 days without needing a
content change becomes a daily, unsilenceable flag. With a
7-page high-confidence corpus today, that is several guaranteed
wolf-cries per week within two months — Viktor's stated
threshold ("three false positives in a week and he stops reading
it") is not a risk, it's a schedule.

The design already acknowledges this failure mode elsewhere: the
deepening picker carries damping ("first dogfooding amendment,
2026-07-10" — kind exclusions plus a 7-day grace period). The
half-life producer got no equivalent.

On trigger-clear the reconciler removed both scratch items ("2
cleared") — self-cleaning works; the gap is purely the missing
acknowledgement path.

**Finding 3 (decision-worthy — the ADR suggestion):** recurring
tend-queue producers need an operator acknowledgement path that
sticks without falsifying page metadata. Routed to
`wiki/brain/ai-suggestions/adrs/acknowledge-recurring-tend-items.md`.

## Step not executed

`brain tend` (the wrapper execs `claude "/tend …"`) was not
launched: it starts an interactive harness session billing the
operator's subscription. Doctor's billing line told Viktor
exactly this beforehand — the cost boundary is legible, which is
the pass criterion available without spending his money.

## Give-up verdict

Asked in character at the sharpest point (step 2): *would Viktor
have given up here?* Not on day one — search, timer honesty, the
live queue, and the explicit billing line are all wins, and the
loop is genuinely cheap (the whole glance is under a minute).
But both of his abandonment triggers are armed: the health strip
reports the wrong governance mode with a green tick (trust in
`doctor` is the product for him — one more caught lie and he
stops believing every ✓), and the half-life producer is a
cries-wolf machine on a timer — deterministic nagging as soon as
his corpus ages past 30 days. Verdict: **retained today,
churning within weeks if the acknowledgement gap and the
doctor predicate stay as they are.**

## Findings by disposition

- **Defect, mechanical fix:** doctor/`​/dash` operating-mode check
  matches the commented-out boilerplate in `.env` (substring vs.
  the contract's anchored grep) and misreports governance mode
  (step 2).
- **Decision-worthy → AI-suggestion ADR:** no policy-correct
  acknowledgement path for recurring half-life tend items;
  `inbox done` does not stick (step 7).
- **Transcript-only:** `brain-repo-truth-verification` schedule
  description says "LLM-grade" while the handler is mechanical-
  only (step 6).
- **Passes worth keeping:** timer honesty vs. systemd; live
  queue pickup; queue-item quality; search recall of a recorded
  decision; explicit billing legibility.
