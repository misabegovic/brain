#!/usr/bin/env python3
"""drift-reconciler — a specialized spoke agent.

Subscribes to repo structure-drift events. On wake it does deterministic
prep — identifies the repo whose code shape moved — and emits a
`reconcile:<repo>` note, so a tend session in a harness updates that
repo's architecture.md against the snapshot. It never reasons itself;
it turns a drift event into queued, attributable reconciliation work.

Run as: brain-agent listen --on-wake "python3 tools/agents/drift_reconciler.py"
(with the agent's BRAIN_URL / BRAIN_AGENT_ID / BRAIN_AGENT_SECRET set).
"""

from __future__ import annotations

import sys

from _lib import spoke, wake_event

SUBSCRIBE_PATTERN = "repo:*"


def main() -> int:
    ev = wake_event()
    if not ev or ev.get("kind") != "drift":
        return 0
    repo = ev.get("ref", "").split(":", 1)[-1] or "unknown"
    spoke().emit("note", f"reconcile:{repo}")
    print(f"drift-reconciler: {repo} drifted (event seq {ev.get('seq')}) — "
          f"queued reconcile:{repo} for the next tend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
