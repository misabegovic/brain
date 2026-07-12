#!/usr/bin/env bash
# install-timer — wire the deterministic accumulation loop to a local
# schedule. Installs a systemd *user* timer running
# `brain.py schedule run-due` daily; prints a crontab line as the
# fallback for machines without systemd. Idempotent; --uninstall to
# remove.
#
# Unit names are PER INSTANCE (brain-<dirname>-schedule) so several
# brains on one machine never collide; a legacy shared-name unit
# (brain-schedule.timer) pointing at this repo is migrated.
#
# This is the queue-and-tend runner: it must run on the machine that
# has the sibling repos, so it is a local timer, never CI.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# dirname + short path hash: distinct even for same-named dirs
# (e.g. ~/projects/brain vs a second checkout elsewhere).
PATH_HASH="$(printf '%s' "$REPO_ROOT" | sha1sum | cut -c1-6)"
INSTANCE="$(basename "$REPO_ROOT" | tr -cd 'a-zA-Z0-9-')-${PATH_HASH}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE="brain-${INSTANCE}-schedule.service"
TIMER="brain-${INSTANCE}-schedule.timer"

if [ "${1:-}" = "--uninstall" ]; then
  systemctl --user disable --now "$TIMER" 2>/dev/null || true
  rm -f "$UNIT_DIR/$SERVICE" "$UNIT_DIR/$TIMER"
  systemctl --user daemon-reload 2>/dev/null || true
  echo "removed $TIMER"
  exit 0
fi

if ! command -v systemctl >/dev/null || ! systemctl --user show-environment >/dev/null 2>&1; then
  echo "systemd user session unavailable — add this crontab line instead:"
  echo "  15 6 * * * cd $REPO_ROOT && python3 tools/brain.py schedule run-due >> log/schedule.log 2>&1"
  exit 0
fi

# Migrate the legacy shared-name unit when it points at this repo.
LEGACY="$UNIT_DIR/brain-schedule.service"
if [ -f "$LEGACY" ] && grep -q "WorkingDirectory=$REPO_ROOT" "$LEGACY"; then
  systemctl --user disable --now brain-schedule.timer 2>/dev/null || true
  rm -f "$UNIT_DIR/brain-schedule.service" "$UNIT_DIR/brain-schedule.timer"
  echo "migrated legacy brain-schedule.timer → $TIMER"
fi

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/$SERVICE" <<UNIT
[Unit]
Description=brain ($INSTANCE) — deterministic accumulation loop (schedule run-due)

[Service]
Type=oneshot
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/env python3 tools/brain.py schedule run-due
UNIT

cat > "$UNIT_DIR/$TIMER" <<UNIT
[Unit]
Description=brain ($INSTANCE) — daily accumulation timer

[Timer]
OnCalendar=*-*-* 06:15:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now "$TIMER"
echo "installed $TIMER (daily 06:15, catch-up on wake) for $REPO_ROOT"
systemctl --user list-timers "$TIMER" --no-pager | head -3
