#!/usr/bin/env bash
# Home staleness hook — ensures every wiki/ edit is paired with a
# wiki/index.md (the agent-maintained home page dashboard) edit.
#
# Used by:
#   - Claude Code PostToolUse hook (.claude/settings.json on Edit|Write|MultiEdit)
#       — invoked as `bash tools/home-staleness.sh post`. Reads the
#       hook's tool_input JSON from stdin; sets the sentinel when a
#       wiki/ file other than wiki/index.md is edited; clears it when
#       wiki/index.md is edited.
#   - Claude Code Stop hook (.claude/settings.json)
#       — invoked as `bash tools/home-staleness.sh stop`. Reads the
#       sentinel; exits non-zero with a blocking message if stale.
#
# CI's check-home-fresh (tools/brain.py) is the load-bearing
# enforcement; this hook is local-session ergonomics so the agent
# notices before pushing.
#
# Sentinel location: wiki/_views/home-staleness.json (gitignored).
#
# See ADR: wiki/brain/adrs/home-content-shape.md
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

SENTINEL="wiki/_views/home-staleness.json"
HOME_FILE="wiki/index.md"

mode="${1:-}"

case "$mode" in
  post)
    payload=$(cat 2>/dev/null || true)
    f=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null || true)
    [ -z "$f" ] && exit 0

    case "$f" in
      "$REPO_ROOT"/*) f="${f#$REPO_ROOT/}";;
    esac

    if [ "$f" = "$HOME_FILE" ]; then
      mkdir -p "$(dirname "$SENTINEL")"
      printf '{"stale": false, "cleared_at": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$SENTINEL"
      exit 0
    fi

    case "$f" in
      wiki/_views/*|wiki/_archive/*) exit 0;;
      wiki/*)
        mkdir -p "$(dirname "$SENTINEL")"
        if [ -f "$SENTINEL" ]; then
          edits=$(jq --arg f "$f" '.edits // [] | . + [$f] | unique' "$SENTINEL" 2>/dev/null || printf '["%s"]' "$f")
        else
          edits=$(printf '["%s"]' "$f")
        fi
        printf '{"stale": true, "since": "%s", "edits": %s}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$edits" > "$SENTINEL"
        exit 0;;
      *) exit 0;;
    esac
    ;;

  stop)
    [ ! -f "$SENTINEL" ] && exit 0
    stale=$(jq -r '.stale // false' "$SENTINEL" 2>/dev/null || echo "false")
    if [ "$stale" = "true" ]; then
      edits=$(jq -r '.edits // [] | join(", ")' "$SENTINEL" 2>/dev/null || echo "<unknown>")
      {
        printf 'home is stale: edited wiki content (%s) but did not update %s.\n' "$edits" "$HOME_FILE"
        printf 'Touch the relevant section on %s and retry.\n' "$HOME_FILE"
        printf 'See wiki/brain/adrs/home-content-shape.md for the section ownership table.\n'
      } >&2
      exit 2
    fi
    exit 0
    ;;

  *)
    printf 'usage: %s {post|stop}\n' "$0" >&2
    exit 64
    ;;
esac
