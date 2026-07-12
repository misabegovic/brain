#!/usr/bin/env bash
# tools/preflight.sh — mirror the validate.yml CI gates locally.
#
# Used by:
#   - The /pr skill before push (manual invocation).
#   - The PreToolUse hook in .claude/settings.json on Bash calls
#     matching `git push` / `gh pr create`. The hook calls this
#     and blocks the tool call on failure (exit != 0).
#
# Runs every gate the runner runs, in the same order:
#   1. brain.py validate
#   2. brain.py check --no-net
#   3. brain.py views + diff against working tree
#
# The home-fresh and README-staleness gates are PR-only and run
# server-side against the base ref; not mirrored here because the
# hook fires before the PR exists. /pr's Pre-flight section
# documents them for the agent.
#
# Exits 0 on success; non-zero on the first gate failure with a
# clear message naming what to fix.

set -uo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "preflight: not inside a git repo" >&2
  exit 64
}

PY=~/.local/share/mempalace-venv/bin/python3
if [ ! -x "$PY" ]; then
  echo "preflight: mempalace venv python missing at $PY — falling back to system python3 (token counts may drift)" >&2
  echo "preflight: run tools/setup-local.sh to create the venv with tiktoken installed" >&2
  PY=python3
fi

step() { echo "preflight ▶ $*"; }
fail() { echo "preflight ✗ $*" >&2; exit 1; }

step "brain.py validate"
"$PY" tools/brain.py validate >/dev/null || fail "brain.py validate failed — fix frontmatter / required sections / references then re-run."

step "brain.py check --no-net"
"$PY" tools/brain.py check --no-net >/dev/null || fail "brain.py check --no-net failed — a sources: citation does not resolve. Fix or remove the line, then re-run."

step "brain.py views (regen + diff)"
"$PY" tools/brain.py views >/dev/null || fail "brain.py views regeneration errored."
if ! git diff --exit-code --quiet wiki/_views/; then
  echo "preflight ✗ wiki/_views/ regenerated to a new state — commit the diff before pushing." >&2
  echo "  git add wiki/_views/ && git commit -m 'regenerate wiki/_views'" >&2
  exit 1
fi

echo "preflight ✓ all gates passed"
