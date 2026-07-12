#!/usr/bin/env bash
# sync-siblings — fetch each sibling repo, list commits since the last
# brain ingest/mine line that named that repo. Output is read by /lint
# and /mine to decide what's worth re-ingesting.
#
# Usage: tools/sync-siblings.sh [repo1 repo2 ...]
#   No args = sweep every active repo declared in brain.config.yml.
#   Archived repos are out of the default sweep; pass them explicitly
#   as args if you want to sync them.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO_ROOT/log/log.md"
PROJECTS="${BRAIN_PROJECTS_ROOT:-$HOME/projects}"

if [[ $# -gt 0 ]]; then
  SIBLINGS=("$@")
else
  mapfile -t SIBLINGS < <(python3 - "$REPO_ROOT/brain.config.yml" <<'PY'
import sys, pathlib
import yaml
p = pathlib.Path(sys.argv[1])
config = (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}
for repo in config.get("active_repos") or []:
    print(repo)
PY
)
  if [[ ${#SIBLINGS[@]} -eq 0 ]]; then
    echo "no active repos declared in brain.config.yml — nothing to sync" >&2
    exit 0
  fi
fi

# For each sibling, find the most recent log line that names it after
# a "mine —" or "ingest —" prefix. We want the date so we can ask git
# "what's happened since then." If we can't find one, fall back to 30d.
last_touch_date() {
  local repo="$1"
  local d
  d=$(grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2} (mine|ingest) — .*${repo}" "$LOG" \
        2>/dev/null | tail -n1 | awk '{print $1}' || true)
  if [[ -z "$d" ]]; then
    d=$(date -d '30 days ago' +%Y-%m-%d)
  fi
  echo "$d"
}

for repo in "${SIBLINGS[@]}"; do
  path="$PROJECTS/$repo"
  if [[ ! -d "$path/.git" ]]; then
    printf "%-22s  (skipped — not a git repo at %s)\n" "$repo" "$path"
    continue
  fi

  since=$(last_touch_date "$repo")

  # Fetch quietly. Don't fail the whole sweep if one repo's remote is
  # unreachable.
  if ! git -C "$path" fetch --quiet --all 2>/dev/null; then
    printf "%-22s  (fetch failed)\n" "$repo"
    continue
  fi

  # Per AGENTS.md § Sibling-repo handling — first step is to land on
  # main + pull latest, so the brain processes the canonical state.
  # *Unless* the repo has uncommitted changes (user is mid-work) or
  # is on a non-main / non-master branch (user is on a feature branch).
  # In that case, leave the working tree alone and report so the
  # operator knows the data may be stale relative to remote main.
  default=""
  for cand in main master; do
    if git -C "$path" show-ref --verify --quiet "refs/heads/$cand"; then
      default="$cand"
      break
    fi
  done
  if [[ -z "$default" ]]; then
    printf "%-22s  (no main/master branch)\n" "$repo"
    continue
  fi

  current=$(git -C "$path" symbolic-ref --short HEAD 2>/dev/null || echo "(detached)")
  dirty=$(git -C "$path" status --porcelain 2>/dev/null | head -n 1)

  if [[ "$current" != "$default" ]]; then
    printf "%-22s  (skipped main checkout — on '%s'; user work)\n" \
      "$repo" "$current"
  elif [[ -n "$dirty" ]]; then
    printf "%-22s  (skipped main pull — uncommitted changes)\n" "$repo"
  else
    if ! git -C "$path" pull --ff-only --quiet 2>/dev/null; then
      printf "%-22s  (pull --ff-only failed; not fast-forward?)\n" "$repo"
    fi
  fi

  # Count commits on the default branch's tracking branch since `since`.
  default_branch=$(git -C "$path" symbolic-ref --short HEAD 2>/dev/null || echo "main")
  upstream=$(git -C "$path" rev-parse --abbrev-ref "${default_branch}@{upstream}" 2>/dev/null || echo "$default_branch")

  count=$(git -C "$path" log --oneline --since="$since" "$upstream" 2>/dev/null | wc -l || echo 0)

  printf "%-22s  since %s on %-30s  %3d commits\n" \
    "$repo" "$since" "$upstream" "$count"

  if [[ "$count" -gt 0 ]]; then
    git -C "$path" log --since="$since" --oneline --abbrev-commit "$upstream" 2>/dev/null \
      | head -n 5 | sed 's/^/    /'
    if [[ "$count" -gt 5 ]]; then
      echo "    ... +$((count - 5)) more"
    fi
  fi
done
