# Changelog

All notable changes to the brain kernel. Versions correspond to
shipped roadmap slices (`wiki/brain/roadmap.md` holds the full
narrative; the ADR shelf holds the decisions).

## 0.14.1 — 2026-07-12
- License changed to MIT (from Apache-2.0; no public release had
  occurred, so no downstream reliance). NOTICE removed.

## 0.14.0 — 2026-07-12
- Surfaces simplified: first-party chat pane removed (superseding
  ADR mcp-cli-terminal-surface) — MCP + CLI + terminal cover it;
  ambient strip, bare-`brain` entry, install-agent, and the billing
  guard retained. CI cron disarmed to manual dispatch (one runner).

## 0.13.1 — 2026-07-10
- Market-readiness: Apache-2.0 license, NOTICE, CHANGELOG,
  CONTRIBUTING, SECURITY, pyproject packaging, first tagged
  release, docs-publish workflow (visibility-gated).

## 0.13.0 — 2026-07-10
- The chat builds: `acceptEdits` on the claude chat row; first
  product artifacts (competitive positioning, market-readiness
  topic) authored through the app by the nested agent.
- Billing guard (0.12.2): API-key env vars stripped from every
  harness subprocess — turns bill the logged-in subscription only.
- Persona-playthrough upgrades (0.12.1): composer autofocus,
  markdown-lite bubbles, suggestion chips.

## 0.12.0 — 2026-07-10
- Chat-first app: conversation as the interface via per-harness
  print-mode rows; terminal demoted to a toggle; bare `brain`
  opens the app.

## 0.11.0 — 2026-07-10
- Instance birth: `init --full` births a gate-passing instance from
  the kernel manifest; 1.0 gate settled (five criteria).

## 0.10.0 — 2026-07-10
- Topics (`kind: topic`) — discussion threads with attributed,
  dated entries; Phoenix-Architecture ingest; `constraints.md` +
  `implementation-memory.md` join the permanent layer.

## 0.9.0 — 2026-07-10
- Every read is a briefing: graph-context page reads (CLI + MCP);
  write-time lint hook; `by:` audit attribution; rendered wiki
  serves at the local server root.

## 0.8.0 — 2026-07-10
- Work happens inside the brain: workbench navigation, self-healing
  UI rebuilds, sidebar mirroring the shelves, `VERSION`.

## 0.7.0 — 2026-07-10
- Hosting: one infra-agnostic image (`deploy/`), Railway reference
  config, per-instance isolation (env ports, hashed timer units).

## 0.6.x — 2026-07-10
- Serving software: MCP over streamable HTTP, `BRAIN_SERVING=1`
  guardrails, Datasette pilot. Harness workbench: loopback PTY
  bridge, launch registry, `install-agent` adapters.

## 0.5.0 — 2026-07-10
- Composable views: derived SQLite index (FTS5), SQL view specs,
  `brain.py query`; Datadog + Langfuse connectors.

## 0.4.0 — 2026-07-10
- Pruning + deepening: link-graph health, per-kind half-life scans,
  the research picker, coverage gaps.

## 0.3.0 — 2026-07-10
- Connectors: GitHub / Notion / Slack as pull-only snapshot-writers
  under one contract.

## 0.2.0 — 2026-07-10
- Queue-and-tend: per-item inbox, `/tend`, local timer, producer
  contract. No scheduled LLM runs, ever.

## 0.1.0 — 2026-07-10
- Kernel extracted as a standalone, client-agnostic shell:
  schema, tools, skills, UI, CI, tests; config-driven registry.
