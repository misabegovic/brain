#!/usr/bin/env python3
"""observability-triage — a specialized spoke agent for alert events.

Subscribes to alerts from observability producers (Sentry, Datadog,
Langfuse — emulated locally, real ones would be connectors). On wake it
triages deterministically: parses the source and level, assigns a
severity by a simple heuristic, and emits a `triage:<source>:<severity>`
note for a tend session to act on. No LLM — deterministic prep only; the
severity call is a lookup, and the reasoning is queued for a harness.

Alert ref shape: alert:<source>:<level>:<id>
  e.g. alert:sentry:error:issue-4821 · alert:datadog:warning:mon-77

Run as: brain-agent listen --on-wake "python3 tools/agents/observability_triage.py"
"""

from __future__ import annotations

import sys

from _lib import spoke, wake_event

SUBSCRIBE_PATTERN = "alert:*"

SEVERITY = {
    "fatal": "high", "error": "high", "critical": "high",
    "warning": "medium", "warn": "medium",
    "info": "low", "debug": "low",
}


def main() -> int:
    ev = wake_event()
    if not ev or ev.get("kind") != "alert":
        return 0
    parts = ev.get("ref", "").split(":")
    source = parts[1] if len(parts) > 1 else "unknown"
    level = parts[2] if len(parts) > 2 else "info"
    ident = ":".join(parts[3:]) or "na"
    severity = SEVERITY.get(level.lower(), "low")
    spoke().emit("note", f"triage:{source}:{severity}:{ident}")
    print(f"observability-triage: {source} {level} ({ident}) → "
          f"severity {severity} — queued triage note")
    return 0


if __name__ == "__main__":
    sys.exit(main())
