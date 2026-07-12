---
title: "What stands between this repo and being a credible market entrant?"
kind: topic
status: draft
updated: 2026-07-10
confidence: low
summary: >
  Six repo-verified gaps between the kernel and a credible market entry. License (MIT) and packaging closed; the product name and repo visibility remain operator calls.
sources:
  - ../../../README.md
  - ../../org/competitive-positioning.md
---

# What stands between this repo and being a credible market entrant?

## Question

The positioning page names the category and the moat; this topic asks
the unglamorous complement: what does the repo *itself* still lack to
be adoptable by a stranger? The 1.0 criteria (see
[1.0 topic](one-point-oh-criteria.md)) gate mechanism readiness;
market readiness is a different axis — legal, naming, distribution,
and discoverability. Resolving it unblocks pointing anyone outside
this machine at the kernel.

## Discussion

- **2026-07-10** (`by: claude chat session`) — six gaps, each
  verified against the repo state today:
  1. **No LICENSE file** — the repo root has none (`ls` verified).
     Default copyright means no one may legally use, copy, or
     instance the kernel. Blocks all adoption; operator decision.
  2. **The name `brain` is not ownable** — a generic English word;
     the remote is a personal namespace (`misabegovic/brain`), the
     CLI installs as `brain`, the config is `brain.config.yml`. Not
     trademarkable, not searchable, collides with everything.
     Operator decision.
  3. **No releases or tags** — `git tag -l` returns nothing despite
     `VERSION` reading 0.12.2; the whole 0.x arc exists only as
     commits on `main`. Distribution today is "clone HEAD of one
     personal remote" (repo visibility unverified — `gh` unavailable
     in this session).
  4. **No public docs or site** — the Astro UI is local-first by
     design; the only workflows are `validate.yml` and
     `scheduled.yml` (no pages deploy), so the onboarding deck
     renders only on machines that already cloned the repo.
  5. **No install artifact** — no `pyproject.toml`, `setup.py`, or
     root `package.json`; installation is a hand-made symlink of
     `tools/brain`. No pip / npm / homebrew path for a newcomer.
  6. **No community scaffolding** — `CHANGELOG`, `CONTRIBUTING`,
     `SECURITY`, and `CODE_OF_CONDUCT` are all absent (the home
     § What-changed serves as a changelog, but only inside a live
     instance).
  Each gap is queued as an inbox item (`market-gap-*`) for `/tend`.
  Gaps 1 and 2 are pure operator decisions; 3–6 are mechanical once
  1–2 are settled.

- **2026-07-10** (`by: claude (fable 5)`) — five of six gaps
  closed the same day on the operator's picks: **Apache-2.0**
  adopted (LICENSE + NOTICE; the adoption-as-moat argument won),
  CHANGELOG/CONTRIBUTING/SECURITY landed, packaging via
  `pyproject.toml` (editable installs provide the `brain` script
  per checkout — the repo is the artifact by design), first release
  tagged, and the docs-publish workflow is ready but
  **gated on repository visibility** (Pages on a private repo needs
  a paid plan). The **name** is explicitly deferred by the operator
  — 'brain' stays the working name and the CLI command; rename
  remains cheap until the first public release.

- **2026-07-12** (`by: claude (fable 5)`) — license changed on the
  operator's direction: **Apache-2.0 → MIT** (two days after
  adoption, before any public release, so no downstream reliance
  existed). MIT is the maximum-simplicity end of the permissive
  spectrum — shorter, universally understood, no NOTICE mechanism,
  no explicit patent grant (the trade against Apache-2.0).

- **2026-07-12** (`by: claude (fable 5)`) — the repository is now
  **public** (operator action); the visibility gap closes. Follow-up
  landed the same day: the operator's personal email removed from
  SECURITY.md and pyproject packaging metadata in favour of GitHub
  private vulnerability reporting (enabled on the repo), and the
  repo-local git author switched to the GitHub noreply address so
  future commits don't carry it. Note: existing git history retains
  the personal author email — rewriting published history is not
  worth the breakage; the operator can decide otherwise.

## Outcome

`(open)` — the license and the name are operator decisions; the rest
sequence behind them.
