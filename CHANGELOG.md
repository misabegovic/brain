# Changelog

All notable changes to the brain kernel. Versions correspond to
shipped roadmap slices (`wiki/brain/roadmap.md` holds the full
narrative; the ADR shelf holds the decisions).

## 0.31.2, 2026-10-25
Published on PyPI as `tended`, so `uvx tended init my-wiki` creates a
working instance anywhere.
- The wheel carries the kernel manifest (every path in
  `KERNEL_COPY_PATHS`, plus `sources/README.md` and `brain.config.yml`)
  inside the `tended` package, copied at build time by `setup.py`. The
  top-level `tools` package is no longer shipped, so it cannot collide in
  site-packages. Checkout use is unchanged.
- New `tended` command: `tended init <dir> [--org X]` births a full
  instance from the bundled kernel, `tended --version` prints the version,
  and any other verb says to run it inside an instance with
  `python3 tools/brain.py <verb>`. The `brain` console script is gone;
  `tools/brain` and `python3 tools/brain.py` remain.
- `init --full` now makes every copied file and directory writable by the
  new owner, so an instance born from a read-only install (a wheel in
  site-packages) can be edited and its seeded ADR filter can run.
- README leads with `uvx tended init my-wiki`; the clone route is the
  contributor path. Nothing inside an instance is renamed.

## 0.31.1, 2026-10-25
Final polish: documentation made to match the code, and defects that
could mislead or hurt a user fixed. No new features.
- Scheduling: `schedule run-due` now honours `cadence:` (daily, weekly,
  monthly; last runs are recorded under `ran` in
  `wiki/_state/schedule.json`) and takes `--force` to run everything. It
  writes the producer heartbeat after every completed run and records
  which jobs failed in it, so `doctor` and the app strip report a failing
  job as failing and a running producer as running (a new `failing`
  state beside `current`, `stalled`, `never`). Before, one failing job
  withheld the heartbeat and the producers read as dead.
- `overlap-refresh` no longer writes `No module named 'sklearn'` into a
  report and records `ok`. Without scikit-learn it writes nothing and
  records a named `skipped`; a failing cluster run records a failure.
  scikit-learn is declared as the optional `cluster` extra.
- Event stream: `seq` assignment and append are now one locked step
  (thread lock plus a file lock where `flock` exists). The docs and the
  code comments state the real trust model: symmetric keys (the hub can
  sign as any agent), no replay or clock check, append-only by
  convention, and a revoked or rotated key makes that agent's history
  fail verification and vanish from reads.
- `tools/emulate-agentic.py` refuses to start when the repository
  already has a keyring, cursors or event stream, instead of deleting
  them.
- `.claude/settings.json` calls `enola` from `PATH` and skips the hook
  when it is absent, rather than a machine-specific absolute path that
  `init --full` copied into every instance. The machine-specific
  permission entry is gone too.
- Specialized agents say they emit a note on the event stream; nothing
  moves those notes into the tend inbox, and the docs now say so.
- Seven wiki pages that claimed `confidence: high` with a 2026-07-10
  `updated:` date were demoted to `medium`: `reflection-check` failed on
  them every day, and so did a freshly born instance.
- Contribution policy: no AI attribution in commits or pull requests.
- Documentation: this changelog gains 0.21.0 to 0.30.0 (reconstructed,
  see the note there); the roadmap, state page, README, CONTRIBUTING
  and `AGENTS.md` corrected for skill count, subcommands, dependencies
  and the hosted tier's missing deploy story.

## 0.31.0 — 2026-08-06
- Intent compilation: every wiki page carries a derived `enola_intent:`
  block (`brain.py intent stamp`, idempotent — kind → type, repos →
  scope, relation fields → typed edges, repo citations → code anchors,
  sources → origin channels), so the whole wiki compiles into the
  architecture graph when the pinned enola release carries the intent
  standard (enola-labs/enola#197). Annotated citations (a trailing
  ` (…)` note) mark paths knowingly not current: the stamp retires
  their anchors and `check` skips instead of breaking.
- The reverse query: `brain.py enola govern <target>` answers *which
  compiled pages govern this file or symbol* (with relation trails)
  and, for a page, *which code its anchors cover* — headless, from the
  on-disk fact union. Wired into eight skills at their natural moments
  (shape deepdive, continue pre-push, query, ingest cursor-walk, plan
  reading-list, review anchor-coverage, zoom-out trail, groom repair
  table).
- Gates: pre-commit auto-restamps (staging only pages the stamp itself
  touched); `intent-page-block` and `intent-compile-drift` join the
  reflection detectors; preflight gates the page-block check before
  push. The enola binary itself never gates a commit (skip-when-absent).
- Instance birth re-stamps the filtered wiki and the empty-sources
  fallback now finds `sources:` mid-frontmatter (it anchored on
  end-of-string, which the stamped block broke).

## 0.30.0, 2026-07-14
*0.21.0 to 0.30.0 were reconstructed on 2026-10-25 from git history
(`VERSION` bumps, one per merged pull request) and
`wiki/brain/state.md`; they were not written at release time, and only
`v0.20.0` and `v0.31.0` were tagged.*
- Specialized spoke agents under `tools/agents/` (a drift-reconciler and
  an observability-triage agent) that subscribe, do deterministic prep
  and emit a note on the event stream; never an LLM.
- `tools/emulate-agentic.py`: the whole hub-and-spoke loop on one
  machine (real hub, real agents, emulated producers).
- `agent-key provision <agent>` prints the env, listener and subscribe
  block that wires a harness in.

## 0.29.0, 2026-07-14
- Spoke client `tools/brain-agent.py` (`emit`, `pull`, `subscribe`,
  `listen`), stdlib-only, mirroring the server's signing; `POST
  /api/events` is the matching authenticated agent write endpoint.

## 0.28.0, 2026-07-14
- Owner-subscription wake: `subscribe --agent --pattern --wake-url`; a
  matching event sends a signed webhook hint (seq and ref, no payload)
  through an SSRF guard, capped at 32 per event, with the per-agent
  cursor as the at-least-once backstop.

## 0.27.0, 2026-07-14
- Per-agent identity and a signed event stream for the hosted tier
  (`BRAIN_HOSTED=1`): `agent-key issue|rotate|revoke`, `events
  emit|since|verify`, `GET /api/events?since=<seq>`. Keys and the stream
  are git-ignored runtime state. Local-first is unchanged.

## 0.26.0, 2026-07-14
- Graph provenance and drift shown as page trust signals: a "pages rely
  on this" chip and an "uncertain but load-bearing" banner.

## 0.25.0, 2026-07-14
- Topics lead with an executive brief and collapse the discussion; the
  compose form stays hidden until opened.

## 0.24.0, 2026-07-14
- One collaboration control on every card, page and thread (comment,
  queue, post, plus edit and remove of your own pending items);
  `/api/act` gains `edit` and `remove`, `/api/pending` lists them.

## 0.23.0, 2026-07-14
- Async conversation surface over the inbox: `/channels/`, a Thread
  panel on each topic, server-stamped attribution, post text fenced as
  untrusted data.

## 0.22.0, 2026-07-14
- Deterministic structure connector (source inventory and Python
  symbols, no network or LLM) writing snapshots to `sources/structure/`
  and queueing drift inbox items; ships off.

## 0.21.0, 2026-07-14
- Per-edge provenance on the link graph (`wiki/_views/graph.json`:
  extracted, inferred, ambiguous), rendered at `/graph/` and surfaced in
  MCP page reads.

## 0.20.0 — 2026-07-12
- Playthrough-sweep delivery: all eight three-persona suggestions
  built, merged, and graduated to the approved ADR/PRD shelves —
  reader-trust (status-honest lists, brief-style views, banner
  render-proof), serving-mode hardening (draft exclusion across every
  read surface, uniform loopback Host guard), and operator-trust
  (producer-death health via a heartbeat, inbox ack, attention
  calibration surface).
- Public-repo hygiene: all named-competitor content and the origin
  client's lineage removed; SECURITY.md added to the kernel manifest;
  the birth citation filter scrubs body refs so graduated ADRs stay
  instance-safe.
- Repository history squashed to a single commit at the operator's
  direction; the operations trail persists in log/log.md.

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
