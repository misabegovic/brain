"""Shared helpers for specialized spoke agents.

A specialized agent is a `brain-agent` subscription plus a handler run
per new event (via `brain-agent listen --on-wake`). The handler reads
the event from `BRAIN_EVENT`, does DETERMINISTIC prep, and emits a
result event under its own identity — it never invokes an LLM. The wake
never invokes the agent; the emitted result is what a tend session (in a
harness) reasons over. That keeps the no-scheduled-LLM invariant.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


def spoke():
    """Load the stdlib spoke client (tools/brain-agent.py) as a module."""
    path = Path(__file__).resolve().parent.parent / "brain-agent.py"
    spec = importlib.util.spec_from_file_location("brain_agent", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def wake_event() -> dict | None:
    """The event that woke this handler (set by `listen --on-wake`)."""
    raw = os.environ.get("BRAIN_EVENT", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
