# Changelog

All notable changes to the brain kernel. Versions correspond to
shipped roadmap slices (`wiki/brain/roadmap.md` holds the full
narrative; the ADR shelf holds the decisions).

## 0.19.4 — 2026-07-12
- Fixed: `doctor` / `/dash` operating-mode check read LOCAL_FIRST as
  a substring, matching the commented `.env.example` boilerplate —
  it reported local-first after the operator removed the flag.
  Anchored to the canonical `^LOCAL_FIRST=true$` test via a shared
  `_local_first()` helper. Found by the Viktor daily-operator
  playthrough sweep.

## 0.19.3 — 2026-07-12
- Standalone-guarantee detectors: internal-refs scans ui/src source
  strings (.astro/.mjs/.ts) — immediately caught a dangling ADR
  reference in the onboarding deck's header; new `denylist`
  reflection check reads a machine-local, git-ignored
  .reflection-denylist (BRAIN_DENYLIST override) so operators can
  flag org/client terms without committing them.
- Operating mode: LOCAL_FIRST removed on this brain (operator
  direction) — changes land via PR with CI green from here on.

## 0.19.2 — 2026-07-12
- Repo public: SECURITY.md now directs to GitHub private
  vulnerability reporting (enabled) instead of a personal email;
  email removed from packaging metadata; repo-local commits switch
  to the GitHub noreply author.

## 0.19.1 — 2026-07-12
- Delegated cold-start: the full first-session tutorial executed
  against a born instance with a real OSS ingest (1.0 criteria 3+4
  evidence, recorded as operator-delegated agent execution).
- Fixed: CI built the UI after pytest, so serve tests saw the
  first-run placeholder — main had been red since 0.14.x; the
  briefing's empty-brain guidance never fired on born instances
  (kernel trail inflated the page count); `setup` now ends by
  printing the next command verified to work on that machine.

## 0.19.0 — 2026-07-12
- Onboarding surfaces (presentation-layer ADR, amendment 2): the
  deck rewritten to the current product — 14 slides including a
  six-step first-session tutorial and project-onboarding guidance;
  README gains an Onboarding section pointing at it. The refresh
  removed a leftover origin-org repo description (standalone
  guarantee).
- Project overviews: every shelf home renders a generated panel —
  start-here reading path, open work, recent decisions, freshness,
  and honestly-stated gaps — derived at build time from the
  shelf's own pages.

## 0.18.0 — 2026-07-12
- The briefing becomes two-way (presentation-layer ADR amendment):
  queue/comment actions on cards and pages POST to the local
  /api/act, which appends an inbox item (produced_by: ui-action)
  for the next tend session. Custom-header CSRF guard; never
  mounts in serving mode. Tend treats ui-action items as direct
  operator intent.
- Briefing gains type filters and per-band show-more pagination.
- New read surfaces, all dependency-free and build-time:
  /dashboard/ (stat cards, kind/status/confidence bars, 30-day
  activity sparkline, hubs), /trail/ (lifecycle timeline with
  supersedes chains), /graph/ (link graph as clickable SVG).
- Closes the presentation-layer bet (0.17 within-appetite
  remainders delivered).

## 0.17.0 — 2026-07-12
- Human-legible presentation layer (pitch → PRD → ADR → build, one
  bet, corrected mid-shaping to a full rewrite): Starlight retired;
  ui/ is a purpose-built Astro app. Root = the briefing (Needs you /
  In flight / On the table + were/are/going orientation, guiding
  empty states); wiki pages keep their URLs and gain lifecycle
  chrome (chips, summary lead, AI-draft + superseded banners);
  Pagefind search at /search/. Build ~30s → ~2s.
- `summary:` frontmatter in the schema (validated; authored across
  37 card-kind pages; exported via pages.json); groom checks drift.
- Attention judgement: `inbox judge` (needs-operator/fyi/routine +
  one-line reason, in-session only) and `inbox grade`
  (useful/noise calibration at wiki/_state/attention-grades.json);
  tend judges external signal, routine-by-default.
- JSON /search API claims its path only with ?q= (route collision
  with the UI search page); shipped PRDs groomed to superseded.

## 0.16.0 — 2026-07-12
- Persona playthrough loop (pitch → PRD → ADR → build, one bet):
  four brain-as-product user personas, the `/playthrough` skill
  (real execution, transcripts to sources/playthroughs/, findings
  as confidence-capped insights), and a version-cursor producer
  queueing one sweep per shipped release.
- Cold-start fixes from the first dogfood walk: non-interactive
  `setup` no longer consents to side-effectful steps (timer, PATH
  symlink, npm) without `--yes`; a fresh clone's first `brain` run
  shows a self-refreshing "building the site" placeholder instead
  of a raw JSON error while the first UI build lands.

## 0.15.0 — 2026-07-12
- Surfaces settle at MCP + CLI (superseding ADR mcp-cli-surface):
  the embedded terminal removed — PTY bridge, websocket slice,
  xterm.js assets, and harness-launch registry deleted. The app
  page is the rendered knowledge under the ambient strip
  (auto-reload kept). Billing guard degrades to a doctor warning;
  `serve --workbench` becomes a deprecated no-op (the app page
  mounts whenever BRAIN_SERVING is unset); static 404s now return
  HTTP 404.

## 0.14.2 — 2026-07-12
- README rewritten for cold-start readers: one-line pitch, app
  screenshot (`docs/workbench.png`), the three ideas, a true
  3-command quickstart; machinery pushed below the fold.
- `setup` gains a `brain`-on-PATH step (~/.local/bin symlink) so
  the quickstart's third command works out of the box.
- Fixed: the workbench's self-healing UI rebuild was orphaned when
  0.12 moved the page's poll from `/workbench/changed` to
  `/workbench/status` — the kick now rides the live poll, so the
  rendered pane can't serve a stale build.

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
