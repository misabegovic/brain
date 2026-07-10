#!/usr/bin/env bash
# install-timer — wire the deterministic accumulation loop to a local
# schedule. Installs a systemd *user* timer running
# `brain.py schedule run-due` daily; prints a crontab line as the
# fallback for machines without systemd. Idempotent; --uninstall to
# remove.
#
# This is the 0.2 queue-and-tend runner: it must run on the machine
# that has the sibling repos, so it is a local timer, never CI.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE="brain-schedule.service"
TIMER="brain-schedule.timer"

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

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/$SERVICE" <<UNIT
[Unit]
Description=brain — deterministic accumulation loop (schedule run-due)

[Service]
Type=oneshot
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/env python3 tools/brain.py schedule run-due
UNIT

cat > "$UNIT_DIR/$TIMER" <<UNIT
[Unit]
Description=brain — daily accumulation timer

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
