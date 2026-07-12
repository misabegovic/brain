---
title: "Public artifacts carry no personal data; a deterministic guard strips session URLs regardless of harness behaviour"
kind: decision
status: accepted
updated: 2026-07-12
confidence: medium
summary: >
  PR descriptions, commit messages, and release notes must not
  contain session URLs or account-tied identifiers. Enforced by a
  commit-msg git hook and a /pr check (brain.py
  check-no-personal-data), so no harness directive can leak a
  session URL into a public repo. Operator-directed after real
  exposure.
sources:
  - ../../../AGENTS.md
  - ../../../CONTRIBUTING.md
---

# Public artifacts carry no personal data; a deterministic guard strips session URLs regardless of harness behaviour

**Decision.** Public-facing artifacts the brain (or an agent working
in it) produces — commit messages, PR/issue descriptions, release
notes — must never carry personal or account-tied data: session
URLs, private chat links, tokens, emails, or similar. Model
attribution (`Co-Authored-By: Claude …`) is acceptable; a session
URL is not. This is enforced **deterministically, not by
convention**: a `commit-msg` git hook and the `/pr` skill both run
`brain.py check-no-personal-data`, which rejects text matching
session-URL and account-link patterns (extensible per-org via a
git-ignored `.personal-data-patterns` file). The guard is the point
of control precisely because the leak originates upstream of the
repo — a harness may append a session URL to every commit by its own
directive, and the guard catches it regardless.

## Context

An operator using a harness that appends `Claude-Session:
https://claude.ai/code/session_…` to commit messages and PR bodies
noticed, after the repo went public, that the URL had leaked into
nine merged PR descriptions and the commit trail. The session URL
ties a public artifact to the operator's private account. Documenting
"don't do this" is insufficient — the leak comes from a standing
harness directive the repo can't see or change, so only a
repo-side guard that runs on every commit reliably stops it.

## Alternatives

- **Commit-msg hook + /pr check running a shared `brain.py`
  scanner** *(chosen)* — deterministic, runs regardless of harness
  behaviour, crosses to every born instance via the kernel manifest,
  and is extensible for org-specific patterns. Catches the leak at
  the last repo-controlled moment before it becomes public.
- **Documentation only (CONTRIBUTING + a PR template)** — necessary
  but not sufficient; it relies on every human and agent remembering,
  and does nothing against a harness that appends the URL
  automatically. Kept as the human-facing half, not the enforcement.
- **A CI check that fails the PR** — catches PR-body and commit
  leaks after the fact, but the data is already public in the PR by
  then; the pre-commit-time guard is strictly earlier. A CI mirror
  could be added later as defence in depth.
- **Redact in the harness** — not portable; every harness differs,
  and the repo can't depend on any of them.

## Consequences

- **Opens** a portable privacy floor: every brain instance inherits
  the guard through the manifest, so adopters get it without opting
  in.
- **Costs** a small chance of false positives if the pattern list
  grows careless; the matched *value* is never reprinted (that would
  re-leak it), only the pattern name, and `--no-verify` remains the
  documented escape hatch for the rare legitimate case.
- **Does not** retroactively clean already-public artifacts —
  existing leaks are scrubbed by hand (as the nine PR bodies were);
  the guard prevents recurrence.
