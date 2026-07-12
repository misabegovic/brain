#!/usr/bin/env bash
# example-producer — template for operator-defined inbox producers.
#
# A producer is any script that queues work for /tend by calling
# `brain.py inbox add`. The contract:
#   --id       stable dedup key — re-running the producer is a no-op
#              while the item is pending (add --update to refresh the
#              summary instead of skipping)
#   --kind     ingest | groom | research | custom
#   --summary  one line: what needs tending and why
#   --route    optional suggested skill invocation for /tend
#
# Register it in brain-schedule.yml (handler: bash tools/producers/<name>.sh)
# and the cron/timer that runs `brain.py schedule run-due` picks it up.
# Producers must be deterministic and read-only against the world:
# they observe and queue; /tend synthesises.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# --- replace from here with your own observation ---------------------
# Example: queue a reminder when the corpus grows past 100 pages.
pages=$(find "$REPO_ROOT/wiki" -name '*.md' -not -path '*/_*' | wc -l)
if [ "$pages" -gt 100 ]; then
  python3 "$REPO_ROOT/tools/brain.py" inbox add \
    --id "corpus-size-review" --kind groom --priority low \
    --summary "corpus crossed ${pages} pages — review page-size discipline and folder promotion" \
    --route "/groom" --produced-by "example-producer"
fi
# ---------------------------------------------------------------------
