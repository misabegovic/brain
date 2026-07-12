#!/usr/bin/env bash
# tools/setup-local.sh — create the local mempalace venv brain.py expects.
#
# Why this exists:
#   tools/preflight.sh and the PreToolUse hook in .claude/settings.json
#   look for python3 at ~/.local/share/mempalace-venv/bin/python3 and
#   fall back to system python3 when missing. The fallback works for
#   validate / check, but `brain.py views` needs tiktoken to compute
#   the same per-page token counts as CI — without it the regen
#   produces drifted pages.json that the views-up-to-date gate then
#   rejects.
#
#   This script creates the venv and installs the deps validate.yml
#   uses (pyyaml + tiktoken + pytest), so local preflight and CI
#   converge.
#
# Idempotent: re-running upgrades pip and re-installs the deps.
#
# Usage: tools/setup-local.sh

set -euo pipefail

VENV=~/.local/share/mempalace-venv
PY_SYS=${PYTHON:-python3}

if ! command -v "$PY_SYS" >/dev/null 2>&1; then
  echo "setup-local: $PY_SYS not found on PATH" >&2
  exit 1
fi

if ! "$PY_SYS" -c 'import ensurepip' 2>/dev/null; then
  cat >&2 <<EOF
setup-local: $PY_SYS lacks ensurepip — venv creation will fail.

On Debian/Ubuntu install the missing package:
  sudo apt-get install -y python3-venv python3-pip

Then re-run: tools/setup-local.sh
EOF
  exit 1
fi

if [ ! -x "$VENV/bin/python3" ]; then
  echo "setup-local ▶ creating venv at $VENV"
  mkdir -p "$(dirname "$VENV")"
  "$PY_SYS" -m venv "$VENV"
else
  echo "setup-local ▶ venv exists at $VENV"
fi

VENV_PY="$VENV/bin/python3"

echo "setup-local ▶ upgrading pip"
"$VENV_PY" -m pip install --quiet --upgrade pip

echo "setup-local ▶ installing pyyaml + tiktoken + pytest"
"$VENV_PY" -m pip install --quiet pyyaml tiktoken pytest

echo "setup-local ▶ verifying tiktoken"
"$VENV_PY" -c 'import tiktoken; tiktoken.get_encoding("cl100k_base"); print("tiktoken OK", tiktoken.__version__)'

cat <<EOF

setup-local ✓ ready

The venv is the python3 that tools/preflight.sh and the PreToolUse
hook prefer. tools/brain.py invocations from agent skills already
use this path. To use it in your shell:

  $VENV_PY tools/brain.py validate
  $VENV_PY tools/brain.py views

Or alias it:

  alias brainpy=$VENV_PY' tools/brain.py'

EOF
