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
- Agent-authored content starts at `confidence: low` (or `medium`
  with cited evidence) and cannot self-promote to `high` in the
  same change.
- Kernel code is stdlib-only Python by design; the UI is the only
  npm surface. A new dependency is an ADR-sized decision.
- Discussion belongs in `wiki/<scope>/topics/` (dated, attributed
  entries), not in issue threads the corpus can't cite.

Run the suite: `pytest tests/` (see `README.md` § Everyday
commands). Instances are born with `brain.py init <path> --full` —
never develop against a born instance's kernel copy; fix the kernel
here.
