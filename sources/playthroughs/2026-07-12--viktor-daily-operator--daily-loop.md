---
persona: .claude/personas/users/viktor-daily-operator.md
scenario: daily operator loop — queue quality, health honesty, judgement ergonomics
version: 0.19.3
date: 2026-07-12
executed_by: claude subagent
---

# Playthrough — Viktor runs the daily loop (0.19.3)

Real execution in a worktree of the repo. Viktor is the daily
operator: months into the queue-and-tend rhythm, trusts the
morning glance, gives up on an inbox that cries wolf or a health
strip that lies. The walk: health surface → producer → attention
loop end-to-end → the served app.

## Step 1 — the morning health glance

### `python3 tools/brain.py doctor`

    ✓ git repository       initialised
    ✓ token counting       tiktoken available in the local venv (...)
    − operating mode       .env missing — defaults to PR-gated mode
        fix: cp .env.example .env
    − brain.config.yml     org and active_repos are empty — the shell is unconfigured
        fix: python3 tools/brain.py setup
    − pre-commit gate      not installed — validate/views run only in CI
        fix: ln -s ../../tools/git-hooks/pre-commit .git/hooks/pre-commit
    − accumulation timer   no local timer — producers only run when invoked by hand
        fix: tools/install-timer.sh
    − browse UI            ui/node_modules missing
        fix: cd ui && npm install
    ✓ agent CLI            claude on PATH — `brain tend` works
    ✓ tend queue           empty
    ✓ billing check        no API-key env vars — harness sessions bill your logged-in subscription

    10 checks — 0 failing, 5 warning(s)

*In character:* every line has a fix command next to it — that's
how I like my mornings. But "0 failing" while the **accumulation
timer is dead** grates. For me the timer *is* the product: if it's
dead, nothing accumulates and my queue silently reads clean forever.
Doctor calls that a warning, same tier as "UI deps missing". It is
not the same tier.

Also noted: the billing line exists and is explicit. That is my
third frustration (surprise bills) answered directly. Good.

### `python3 tools/brain.py status`

    corpus: 52 pages
      by kind: decision=22, initiative=6, insight=1, meta=5, pitch=6, reference=8, topic=4
      by status: accepted=19, draft=2, living=15, superseded=16
      by confidence: high=7, low=4, medium=41
    security: wiki/_state/security.json absent
    sync-cursors: 0 sibling repos tracked
    ai-suggestions: 0 pending review, 0 graduated

Honest about absences ("absent", not fake-green). Fine.

### `python3 tools/brain.py inbox summary`

    brain inbox: empty

### `python3 tools/brain.py links`

    # link graph — 53 pages
    orphans (0) — no inbound links; link or archive:
      (none)
    hubs (top 15) — most-linked; keep these freshest:
        5← brain/adrs/mcp-cli-surface.md
        ...
    dead ends (26) — no outbound links:
      ...

0 orphans, 26 dead ends (mostly leaf ADRs — plausible). No nagging.

## Step 2 — the producer

### `python3 tools/brain.py schedule run --target inbox-refresh`

    # running: inbox-refresh
    inbox-refresh: 0 added, 0 refreshed, 0 cleared; 0 pending total

Empty queue. Is "0 added" honest, or is the producer blind? Checked
the producer's slice against the corpus (real verification, reading
the implementation at `tools/brain.py` `_schedule_run_inbox_refresh`):

- half-life items: corpus is 2 days old, nothing past any threshold — correct.
- orphans item: 0 orphans — correct.
- deepening picker (low/medium confidence × ≥2 inbound links):
  the picker has a **7-day grace period** and excludes
  topic/pitch/initiative kinds whose confidence tier is
  policy-correct. Every candidate page here was updated 2026-07-10
  or later — inside grace, correctly skipped.

*In character:* this is the anti-wolf-cry machinery working. Two
days ago I'd apparently have been nagged about brand-new pages;
the grace-period amendment (2026-07-10, per the code comment)
fixed exactly the thing that makes me stop reading queues. Every
future item this producer emits has a deterministic trigger I can
re-derive. Trust: earned.

## Step 3 — attention loop end-to-end

Read the tend skill's judgement rules first
(`.claude/skills/tend/SKILL.md` § Attention judgement): read
calibration first, `routine` is the default under uncertainty,
reserve `needs-operator` for interrupt-someone's-day signal, reason
is one line and never quotes raw payloads.

### add

    $ python3 tools/brain.py inbox add --id datadog-monitor-flap-2026-07-12 --kind custom \
        --summary "Datadog: monitor 'api-p95-latency' flapped 3x in 24h (warn<->ok); SLO burn unchanged" \
        --route "/in sources/datadog/" --priority normal
    inbox: wrote datadog-monitor-flap-2026-07-12

    $ python3 tools/brain.py inbox summary
    brain inbox: 1 pending (1 custom) — run /tend to digest

### judge

Calibration check first: `wiki/_state/attention-grades.json` did not
exist (no history — first run). A warn↔ok flap with SLO burn
unchanged is textbook not-worth-an-interrupt:

    $ python3 tools/brain.py inbox judge datadog-monitor-flap-2026-07-12 \
        --attention routine --reason "Flapping warn<->ok with SLO burn unchanged; no operator action indicated"
    inbox: judged datadog-monitor-flap-2026-07-12 → routine (...)

The item JSON gained `attention`, `attention_reason`, `judged` —
verdict is durable and git-auditable. Good shape.

### grade

    $ python3 tools/brain.py inbox grade datadog-monitor-flap-2026-07-12 --grade useful
    inbox: graded datadog-monitor-flap-2026-07-12 → useful (verdict was routine)

`wiki/_state/attention-grades.json` after:

    { "grades": [ { "id": "datadog-monitor-flap-2026-07-12",
                    "verdict": "routine", "grade": "useful",
                    "note": "", "graded": "2026-07-12" } ] }

**Friction (judgement ergonomics):** to grade I had to *know the
item id*. Nothing lists "verdicts awaiting your grade" — no
`inbox grades --pending`, no strip count, no briefing band. Once an
item is `done` its verdict leaves the queue; if I don't grade in
the moment, the calibration loop starves silently. The tend skill
tells the *agent* to mention the command; nothing holds the
*operator's* side of the loop.

Cleared the test item (`inbox done`) — leaving a synthetic Datadog
item in a committed queue is exactly the noise I hate.

## Step 4 — the served app

`ui/node_modules` was missing → `npm install --no-audit --no-fund`
in `ui/` (297 packages, 2s), then `bash tools/ui-build.sh` (silent
success, builds `ui/.build-cache/`). Served with
`BRAIN_PORT=8801 python3 tools/brain.py serve`.

### `GET /` (briefing) — 200

    Briefing — The brain's judgement of what matters right now · v0.19.3
    Needs you (1): hypothesis — confirm or refute · insight ·
      "The quickstart's third command (`brain`) is fragile on cold-start machines"
    In flight (0): "No bets in flight. Shape one: ..."
    On the table (3): one-point-oh-criteria, market-readiness-gaps, phoenix-adoption
    Orientation: were / are / going — all entries dated, all verifiable

*In character:* the briefing tells the truth. "0 in flight" is
rendered as an honest zero with a next action, not padded. The one
Needs-you item is a real unconfirmed hypothesis. I'd read this
daily.

### `GET /workbench/status` — 200

    { "inbox": 0, "fails": 0, "warns": 4, "mtime": 1783860215.7 }

(4 warns, not 5 — the UI-deps warning cleared after npm install;
re-ran doctor and confirmed `0 failing, 4 warning(s)`. The status
endpoint is live, not a stale snapshot. Good.)

### The strip's rendering logic (from the served workbench page)

    fails ? '✗ ' + s.fails + ' failing · ' :
    warns ? '− ' + s.warns + ' notice · ' : '✓ healthy · ')
    inbox ? s.inbox + ' to tend' : 'queue clear');

**Finding (health honesty):** the strip never claims "healthy"
while warns exist — Viktor's literal give-up phrasing is avoided.
But with a dead accumulation timer the strip reads
**"− 4 notice · queue clear"**, and *"queue clear" is the lie of
omission*: clear-because-tended and clear-because-the-producer-is-
dead render identically. The one warn that poisons the meaning of
every other signal on the strip (a dead timer means "queue clear"
and "0 to tend" are vacuously true) is flattened into an
undifferentiated notice count. A week of that and my glance is
worthless — and I wouldn't know.

### `GET /dashboard/` — 200

    53 pages · 143 links · 0 orphans · 0 pages >30d old · 0 inbox pending ·
    60 audited ops · 100% verdicts graded useful

**Finding (calibration honesty):** "100% verdicts graded useful" is
computed from my **single** test grade
(`ui/src/pages/dashboard.astro` line 69–71: `useful/(useful+noise)`,
no sample size shown). One grade renders as a headline percentage.
At n=1 that stat is decoration; worse, when the verdicts *do* start
degrading, a 5-grade history shows "80%" with the same confident
face as a 500-grade history.

## Would I have given up?

Asked honestly, twice:

1. **At the UI install step** — no. Doctor told me exactly what to
   run before I hit the missing dependency, and the build script
   was silent-on-success. Mild, guided friction.
2. **At the strip, one hypothetical week in** — this is the real
   risk. Not a rage-quit: a *quiet* one. If my timer died Monday
   and the strip said "− 4 notice · queue clear" all week, I'd keep
   glancing, see clear queues, and stop opening the terminal to
   run doctor. By Friday the brain is rotting and my glance says
   calm. I would not have *given up* — I'd have been **betrayed
   politely**, which for a daily-trust product is worse. Verdict:
   the strip needs to treat producer-death as first-class, not as
   one more notice.

Three wrong verdicts killing the band: the machinery to *catch*
degradation exists (grades land in `attention-grades.json`, the
tend rules tell the agent to read calibration first), but the
operator-side surface is thin — no pending-grades list, an n-free
percentage. The loop can starve without anyone noticing.

## Findings by disposition

- **PRD suggestion** — timer/producer death is flattened into the
  generic notice count while "queue clear" renders as calm;
  `wiki/brain/ai-suggestions/prds/producer-death-first-class-health.md`.
- **PRD suggestion** — attention-calibration loop has no
  operator-side surface (no pending-grades list, sample-size-free
  percentage); `wiki/brain/ai-suggestions/prds/attention-calibration-operator-surface.md`.
- **Transcript-only** — doctor tiering puts "timer dead" at the same
  warn tier as "UI deps missing" (folded into PRD 1's problem
  statement); `inbox grade` requires knowing the item id (folded
  into PRD 2); dashboard "60 audited ops" sparkline unlabeled at
  first glance (minor).
- **Positive (no action)** — inbox-refresh's grace period + kind
  damping prevent wolf-crying; billing check is explicit; briefing
  renders honest zeros; `/workbench/status` is live, not stale.

Server on 8801 killed after the walk.
