#!/usr/bin/env bash
# entrypoint — start the serving surfaces. Runs identically in the
# image and directly on a host (local emulation): all paths are
# repo-relative, all ports are env-driven, BRAIN_SERVING defaults on.
set -euo pipefail
cd "$(dirname "$0")/.."

export BRAIN_SERVING="${BRAIN_SERVING:-1}"
PORT="${PORT:-8080}"
SURFACE="${BRAIN_SURFACE:-ui}"
MCP_PORT="${BRAIN_MCP_PORT:-8766}"
UI_PORT="${BRAIN_UI_PORT:-8768}"
DS_PORT="${BRAIN_DS_PORT:-8767}"
HOST="${BRAIN_BIND:-0.0.0.0}"

python3 tools/brain.py index >/dev/null

start_ui() {
  [ -d ui/dist ] || { echo "ui/dist missing — build the UI first"; return 0; }
  python3 -m http.server "$1" --directory ui/dist --bind "$HOST" &
  echo "ui        → http://$HOST:$1"
}
start_mcp() {
  python3 tools/brain-mcp.py --http --host "$HOST" --port "$1" &
  echo "mcp       → http://$HOST:$1/mcp   [serving mode: $BRAIN_SERVING]"
}
start_datasette() {
  command -v datasette >/dev/null || { echo "datasette not installed — surface skipped"; return 0; }
  datasette serve -i wiki/_views/index.db \
    --metadata tools/datasette/metadata.yml \
    --host "$HOST" --port "$1" --setting default_page_size 50 &
  echo "datasette → http://$HOST:$1"
}

case "$SURFACE" in
  ui)        start_ui "$PORT";        start_mcp "$MCP_PORT"; start_datasette "$DS_PORT" ;;
  mcp)       start_mcp "$PORT";       start_ui "$UI_PORT";   start_datasette "$DS_PORT" ;;
  datasette) start_datasette "$PORT"; start_ui "$UI_PORT";   start_mcp "$MCP_PORT" ;;
  *) echo "unknown BRAIN_SURFACE=$SURFACE (ui|mcp|datasette)"; exit 1 ;;
esac

# First surface to die takes the container down (restart policy heals).
wait -n
