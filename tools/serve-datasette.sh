#!/usr/bin/env bash
# serve-datasette — the serving-slice pilot: read-only faceted browse
# + SQL + JSON API over the derived index. Localhost by default; put
# an identity-aware proxy in front for anything wider.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="$REPO_ROOT/wiki/_views/index.db"
if ! command -v datasette >/dev/null; then
  echo "datasette not installed — pip install datasette (or pipx install datasette)" >&2
  exit 1
fi
[ -f "$DB" ] || python3 "$REPO_ROOT/tools/brain.py" index
exec datasette serve -i "$DB" \
  --metadata "$REPO_ROOT/tools/datasette/metadata.yml" \
  --setting default_page_size 50 "$@"
