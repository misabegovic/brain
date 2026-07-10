# brain

An empty, reusable **brain shell** — an LLM-maintained knowledge base
kernel, extracted as a harness you can point at any organisation or
project. Clone it, fill in `brain.config.yml`, and an agent (Claude)
maintains a synthesis of your repos, decisions, and roadmap with
enough fidelity that:

1. **Codebases could be regenerated** from the specs that live here.
2. **Cross-team overlaps surface** rather than hide.
3. **Autonomous agents can use this as their primary working memory.**

The methodology is the one Karpathy describes in
<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>:
raw sources stay immutable, the wiki layer synthesises them, and a
schema document (`AGENTS.md`) tells the agent how to maintain it.
Verbatim history / semantic recall is handled by
[mempalace](https://github.com/mempalace/mempalace).

## What ships in the shell

The **kernel** — mechanism, no content:

- **`AGENTS.md`** — the schema/protocol the agent follows: three
  layers (sources → wiki → schema), three levels (brain / org /
  repo), page kinds, governance, the `/shape` workflow,
  `ai_suggestion` discipline.
- **`tools/`** — `brain.py` (validate / check / views / search /
  stats / status / schedule / sync-cursor / install-sibling / init),
  the stdio MCP server, sibling-repo sync, local hooks, page
  templates.
- **`.claude/`** — the full slash-command surface (`/in`, `/capture`,
  `/ask`, `/sync`, `/groom`, `/shape`, `/continue`, `/zoom-out`,
  `/rfc`, `/pr`, `/review`, `/spawn`, `/rebase`, …) as skills, plus
  the three agent personas (PM / Tech Lead / Developer) that drive
  Shape Up.
- **`ui/`** — Astro 5 + Starlight + Pagefind browse surface with an
  onboarding deck at `/onboarding/`.
- **`.github/workflows/`** — the validate gates and the daily
  scheduled-operations runner.
- **`tests/`** — kernel invariants (shape-only; no content coupling).

The **content** is yours: `wiki/` starts as an empty three-level
skeleton, `sources/` starts empty, `log/log.md` starts empty.

## Adopting the shell for a project

1. **Configure.** Edit `brain.config.yml` — org name plus the
   `active_repos:` this brain tracks. Repos resolve on disk under
   `$BRAIN_PROJECTS_ROOT` (default `~/projects/`).
2. **Pick a mode.** Copy `.env.example` to `.env`. `LOCAL_FIRST=true`
   (the default in the example) suspends the PR/CI ritual for
   single-operator work; unset it to get PR-gated multi-agent
   governance. See `AGENTS.md` § Governance.
3. **Author personas.** `.claude/personas/team/` (internal
   archetypes) and `users/` (customer archetypes) are authored
   per-organisation — see `.claude/personas/README.md`. The
   `agents/` roles ship with the kernel.
4. **Ingest.** Point the agent at a repo or document: `/in <source>`.
   Shelves grow under `wiki/<repo>/` as content earns them.
5. **Wire the reach surface** (optional). Register the MCP server,
   symlink `tools/brain` onto your PATH, run
   `brain.py install-sibling <repo>` to surface brain pages inside
   sibling-repo agent sessions.

## Repo layout

```
AGENTS.md           # schema / protocol the agent follows (CLAUDE.md → AGENTS.md)
brain.config.yml    # per-organisation config: org name, repo registry
.claude/            # slash commands, skills, settings, personas
sources/            # raw, immutable inputs (additive only)
wiki/               # synthesis layer — per-repo + org + brain-meta
log/                # append-only operations log (log.md)
tools/              # brain.py CLI, sync-siblings, hooks, templates
ui/                 # Astro 5 + Starlight + Pagefind — src/content/docs symlinks ../../wiki
tests/              # kernel invariant tests (pytest)
```

## Configuration

### Local Python venv (recommended)

`tools/preflight.sh` and the PreToolUse hook in
`.claude/settings.json` look for python3 at
`~/.local/share/mempalace-venv/bin/python3` and fall back to
system python3 when missing. The fallback works for `validate`
+ `check`, but `brain.py views` needs **tiktoken** to compute
the same per-page token counts as CI — without it `pages.json`
drifts and the views-up-to-date gate rejects the push.

Create the venv once with:

```bash
tools/setup-local.sh
```

### Sibling-repo root

All tooling resolves sibling-repo paths through one configurable
root: the `BRAIN_PROJECTS_ROOT` environment variable, defaulting to
`~/projects/`. Set it in your shell profile if your repos live
elsewhere:

```bash
export BRAIN_PROJECTS_ROOT="$HOME/work"
```

## Everyday commands

```bash
python3 tools/brain.py validate     # frontmatter + section conformance
python3 tools/brain.py check        # source citations resolve
python3 tools/brain.py stats        # corpus shape
python3 tools/brain.py views        # regen wiki/_views/ (by-kind, by-team, by-repo, pages.json, ai-suggestions)
python3 tools/brain.py search '<q>' # hybrid keyword search
python3 tools/brain.py status       # single-pane health dashboard
python3 tools/brain.py inbox summary # the tend queue in one line
tools/install-timer.sh              # daily accumulation timer (systemd user / cron)
pytest tests/                       # kernel invariants
```

### Pre-commit hook

```bash
ln -s ../../tools/git-hooks/pre-commit .git/hooks/pre-commit
```

Gates: `brain.py validate` + auto-stages `wiki/_views/` regen +
`brain.py reflection-check links`.

## Workflow — slash commands

| Command                      | What it does                                                                                       |
|------------------------------|----------------------------------------------------------------------------------------------------|
| `/in <source>`               | Add something to the brain. Auto-routes; hands off to `/shape` when it spots a pitch or pre-existing decision. |
| `/capture <scope>`           | Capture in-flight signal (conversation, design discussion) without a source URL.                  |
| `/ask <question>`            | Query. Default factual lookup; escalates to plan / overlap / coverage by phrasing.                |
| `/sync`                      | Mechanical health sweep: sibling-repo fetch, lint, source-link check, schema validate, regen views. |
| `/tend [<budget>]`           | Digest the inbox — pending synthesis work queued by the deterministic producers. Budget = count / time-box / kind / id. |
| `/groom`                     | Judgement sweep: confidence demotion, insight decay, supersede→archive transitions.                |
| `/shape <scope> <pitch>`     | **The only path to ADRs/PRDs.** Manual by default — pauses at every load-bearing decision. `--auto`, `--pitch`, `--record`, `--epic`, `--rfc` modes. |
| `/continue <slug-or-PR#>`    | Resume in-flight `/shape` work; detects phase from artifact state.                                |
| `/zoom-out <target>`         | Per-work-item zoom-out brief — big-picture fit during deep focus.                                 |
| `/rfc <page>`                | Standalone RFC pass — append a multi-perspective section to a wiki page.                          |
| `/promote <insight>`         | Graduate `kind: insight` → `kind: initiative`.                                                    |
| `/pr <summary>`              | Open a PR for current changes; runs preflight, watches CI, chains to `/review` on green.          |
| `/review <PR#>`              | Review and auto-merge after every guardrail passes.                                               |
| `/spawn <slug> [--target …]` | Opt-in parallel-effort spawn: worktrees + branches + effort registry + background owner subagent. |
| `/list-efforts [<status>]`   | Read-only surface for in-flight parallel efforts.                                                 |
| `/rebase`                    | Cheap-rebase onto `origin/main`, auto-resolving `wiki/_views/` conflicts via regen.               |

Full protocols live in `.claude/skills/<skill>/SKILL.md`; governance
rules in `AGENTS.md` § Governance.

## External integrations

| System            | State                | Notes                                                          |
|-------------------|----------------------|----------------------------------------------------------------|
| Planning tool     | bring your own       | Read-only; snapshot before ingest. Notion export tool included. |
| GitHub            | via `gh` CLI         | Pre-allowed in `.claude/settings.json`.                        |
| MCP               | ✅ `tools/brain-mcp.py` | Read-only brain access for any MCP-aware client.            |
| mempalace         | optional             | Verbatim / semantic-recall layer.                              |

## Browse (UI)

```bash
cd ui && npm install                # first run only
npm run build                       # production build
npm run dev                         # local dev server
```

`ui/src/content/docs` symlinks to `../wiki`, so the wiki renders as a
Starlight site with Pagefind search. Local-first — share via repo
paths, not a hosted URL.
