---
title: "Research — tend verification of the hub ADRs"
captured: 2026-07-10
kind: research-note
method: /tend research items; claims checked against the shipped mechanism
---

# Hub-ADR verification (tend sweep, 2026-07-10)

## brain/adrs/queue-and-tend-inbox.md → verified, high

Every mechanism claim checked against the shipped kernel today:
per-item JSON files at `wiki/_state/inbox/` (`tools/brain.py`
INBOX_DIR + `inbox add|list|summary|done`); slug-validated dedup ids
with idempotent re-adds and arrival-date-preserving upserts
(`tests/test_inbox.py::test_inbox_add_is_idempotent_on_id`);
refresh-op set reconciliation limited to its own items
(`test_inbox_refresh_reconciles_only_its_own_items`); the /tend
skill at `.claude/skills/tend/SKILL.md`; the SessionStart summary
hook in `.claude/settings.json`; the local timer installer
(`tools/install-timer.sh`, installed and active on this machine —
`systemctl --user is-active brain-schedule.timer` = active); the
producer template at `tools/producers/example-producer.sh` plus its
disabled `brain-schedule.yml` entry. No scheduled LLM invocation
exists anywhere in the schedule surface. All claims cite primary
sources read today.

## brain/adrs/successor-ssg-for-ui.md → verified with one scoped caveat, high

Substrate claims verified locally: `ui/package.json` pins astro ^5,
@astrojs/starlight ^0.30, pagefind ^1.1 (npm-managed, nothing
vendored); `ui/src/content/docs` symlinks the wiki; the build passes
today (28 pages); the serve layer (`ui/serve.mjs`) is SSG-agnostic;
github-slugger is the pinned anchor slugger. The Build notes'
Lighthouse figures (54/64 → 100, 705 KB → 4 KB first-load JS) are
origin-deployment measurements that cannot be re-run from this
shell — retained as clearly-scoped historical evidence of the
cutover, not as claims about this checkout. The operative decision
content (substrate, constraints, exit ramps) is fully verified.

## brain/pitches/harness-workbench.md → moot

The picker queued the pitch for deepening the same day its deepdive
research landed (a prior-art architecture study) and its
graduation was directed. Cleared as moot; the pitch is superseded by
the PRD.
