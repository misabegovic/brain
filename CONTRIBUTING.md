# Contributing

This repository is governed by its own mechanism — read `AGENTS.md`
(the schema) before anything else; it is the contract for humans and
agents alike.

**The short version:**

- Every change lands via PR with CI green (`validate`, `check`,
  views-up-to-date, pytest, reflection-check, UI smoke build). The
  pre-commit hook (`ln -s ../../tools/git-hooks/pre-commit
  .git/hooks/pre-commit`) runs the load-bearing gates locally.
- **Decisions need humans.** ADRs and PRDs are authored only through
  the `/shape` workflow with explicit human approval at every phase;
  agent-initiated proposals live under `ai-suggestions/` until a
  human graduates them. Don't hand-write into `adrs/` or `prds/`.
- `sources/**` is additive-only. Never edit or delete an existing
  snapshot.
- **No personal data in public artifacts.** PR descriptions, commit
  messages, and release notes must not contain session URLs, private
  links, tokens, emails, or account-tied identifiers. The PR template
  (`.github/pull_request_template.md`) sets the shape.
- **No AI attribution.** Commits and PRs carry no `Co-Authored-By`
  line naming an assistant, no session link and no "generated with"
  line. The author is the contributor of record; a tool is not a
  co-author. If a harness adds such a line by default, strip it before
  the commit lands. (The commit-msg hook checks session URLs only; the
  rest is yours to keep.)
- Agent-authored content starts at `confidence: low` (or `medium`
  with cited evidence) and cannot self-promote to `high` in the
  same change.
- Kernel code uses the standard library plus two declared packages:
  `pyyaml` (required) and `tiktoken` (listed in `requirements.txt`; the
  tools run without it but fall back to a rough token estimate, so
  committed `wiki/_views/` drift from CI's unless it is installed).
  `scikit-learn` is optional (the `cluster` extra, used by the
  overlap job). The UI is the only npm surface. A new dependency is an
  ADR-sized decision.
- Discussion belongs in `wiki/<scope>/topics/` (dated, attributed
  entries), not in issue threads the corpus can't cite.

Run the suite: `pytest tests/` (see `README.md` § Everyday
commands). Instances are born with `brain.py init <path> --full` —
never develop against a born instance's kernel copy; fix the kernel
here.
