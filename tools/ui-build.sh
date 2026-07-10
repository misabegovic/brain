#!/usr/bin/env bash
# Build the brain UI quietly. Used by:
#   - Claude Code hook (.claude/settings.json on Edit/Write to wiki/**)
#   - CI smoke step (.github/workflows/validate.yml)
#
# Silent on success (no stdout/stderr); non-zero exit on failure.
# Builds into ui/.build-cache/ (gitignored) so it never collides with
# the committed ui/public/ artefacts owned by other workflows.
#
# See ADR: wiki/brain/adrs/ui-auto-refresh-hook.md
# Substrate: wiki/brain/adrs/successor-ssg-for-ui.md (Astro+Starlight)
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Skip when ui/ scaffolding hasn't been installed yet (first-clone
# state, or environments that don't carry node_modules). The hook
# is supposed to be cheap and silent; missing dependencies are not
# a failure mode it should surface.
if [[ ! -d ui/node_modules ]]; then
  exit 0
fi

mkdir -p ui/.build-cache

# Astro reads astro.config.mjs from cwd, so cd into ui/ before
# invoking. `--outDir` writes the static site to a sandbox path
# (relative to ui/) instead of the configured ui/public/. Quiet
# stdout; stderr stays so failures are legible in the agent
# transcript and CI log.
cd ui
npx astro build --outDir .build-cache >/dev/null
