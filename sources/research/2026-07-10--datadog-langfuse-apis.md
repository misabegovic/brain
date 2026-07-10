---
title: "Research — Datadog and Langfuse pull-connector APIs"
captured: 2026-07-10
kind: research-note
method: web research (agent)
---

# Datadog / Langfuse pull connectors

**Datadog auth.** Reads need `DD-API-KEY` + `DD-APPLICATION-KEY`;
application keys are scopeable — minimal read set: `monitors_read`,
`slos_read` (+ `logs_read_data`, `logs_read_index_data` only if
logs). `DD_SITE` is required config (api.datadoghq.com / .eu / us3 /
us5 / ap1); wrong site = 403.

**Datadog daily pull.** `GET /api/v1/monitor?group_states=all&
with_downtimes=true` (full snapshot, small) + `GET /api/v1/slo` +
incremental `GET /api/v2/events?filter[from]=<last_run>` (cursor
within run). **Monitor state, not logs, is the production-state
primitive** — logs search is quota-scarce (~300 req/hr/org) and
opt-in only. Rate limits arrive via X-RateLimit-* headers.

**Langfuse auth.** Basic auth: public key as user, secret key as
password; base `<host>/api/public`. **No read-only key type exists**
(open feature request) — keys are project-scoped and write-capable.
Guidance: dedicated project keys or self-host; treat `sk-lf-` as
write-capable, never log it.

**Langfuse daily pull.** Full prompt inventory (`/v2/prompts` +
production-labeled bodies); incremental traces/observations/scores
via `fromTimestamp=<last_run>` (page-based, limit 100); datasets
weekly. Rate limits per-minute per-org (20/min Hobby → 1000/min
Pro): throttle page loops.

**Cursor strategy (both).** Durable cross-run cursor is
`last_run_iso` in the state file; server cursors are within-run only
(they expire). Overlap the window ~5 min for late writes; dedupe by
id. 429 handling: one retry honoring Retry-After /
X-RateLimit-Reset.

**Prior art.** datadog-sync-cli (official: monitors/dashboards/SLOs
→ local JSON files), dd2tf / Terraform-as-read-model, and Langfuse's
official prompt→GitHub webhook sync — file snapshots of both systems
are established practice.
