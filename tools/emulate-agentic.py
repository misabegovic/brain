#!/usr/bin/env python3
"""emulate-agentic — run the whole hub-and-spoke agentic loop locally.

No deployment, no external services: this spins up a hosted brain hub on
this machine, issues keys, starts specialized spoke agents as listeners,
fires emulated producers (a structure-drift event and Sentry / Datadog /
Langfuse alerts), and shows each agent get woken and emit its result —
the complete loop end to end. Everything is torn down and the runtime
state (git-ignored) is cleaned up on exit.

    python3 tools/emulate-agentic.py

It is a demonstration and a smoke test of the real code paths, not a
mock: the hub is `brain.py serve --BRAIN_HOSTED`, the agents are the real
`tools/brain-agent.py` client running the real `tools/agents/` handlers,
and every event is genuinely signed and verified.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import brain  # noqa: E402

PORT = 8820
HUB = f"http://127.0.0.1:{PORT}"


def _spoke():
    spec = importlib.util.spec_from_file_location(
        "brain_agent", HERE / "brain-agent.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _as(agent, secret):
    os.environ.update(BRAIN_URL=HUB, BRAIN_AGENT_ID=agent,
                      BRAIN_AGENT_SECRET=secret)


def _banner(msg):
    print(f"\n\033[1m{msg}\033[0m")


def main() -> int:
    ba = _spoke()
    tmp_cursors = REPO / "wiki" / "_state" / ".emulate-cursors.json"
    os.environ["BRAIN_AGENT_CURSORS"] = str(tmp_cursors)

    # Clean any prior emulation state.
    brain.AGENT_KEYS.unlink(missing_ok=True)
    brain.EVENT_CURSORS.unlink(missing_ok=True)
    shutil.rmtree(brain.EVENTS_DIR, ignore_errors=True)
    tmp_cursors.unlink(missing_ok=True)

    _banner("1. issue keys — producers + specialized agents")
    keys = {name: brain.agent_key_issue(name) for name in (
        "structure-connector", "sentry", "datadog", "langfuse",
        "drift-reconciler", "observability-triage")}
    for name in keys:
        print(f"   • {name}")

    _banner("2. start the hosted hub locally (BRAIN_HOSTED, loopback wakes)")
    hub = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"), "serve",
         "--port", str(PORT)],
        env={**os.environ, "BRAIN_HOSTED": "1",
             "BRAIN_WAKE_ALLOW_LOOPBACK": "1"},
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    listeners = []
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"{HUB}/api", timeout=3)
                break
            except OSError:
                if hub.poll() is not None:
                    print("hub failed to start", file=sys.stderr)
                    return 1
                time.sleep(0.3)
        print(f"   hub up at {HUB}")

        _banner("3. start specialized spoke agents (real brain-agent listeners)")
        agents = [
            ("drift-reconciler", 9101, "repo:*",
             "agents/drift_reconciler.py"),
            ("observability-triage", 9102, "alert:*",
             "agents/observability_triage.py"),
        ]
        for agent, port, pattern, handler in agents:
            env = {**os.environ, "BRAIN_URL": HUB, "BRAIN_AGENT_ID": agent,
                   "BRAIN_AGENT_SECRET": keys[agent]}
            p = subprocess.Popen(
                [sys.executable, str(HERE / "brain-agent.py"), "listen",
                 "--port", str(port),
                 "--on-wake", f"{sys.executable} {HERE / handler}"],
                env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True)
            listeners.append(p)
            # subscribe the agent to its pattern, wake URL = its listener
            _as(agent, keys[agent])
            ba.emit("subscribe", '{"p":"%s","u":"http://127.0.0.1:%d/wake"}'
                    % (pattern, port))
            print(f"   • {agent} listening on :{port}, subscribed to "
                  f"{pattern!r} → {handler}")
        time.sleep(0.6)

        _banner("4. fire emulated producers (no external services)")
        _as("structure-connector", keys["structure-connector"])
        ba.emit("drift", "repo:brain")
        print("   • structure-connector: drift on repo:brain")
        for src, level, ident in [("sentry", "error", "issue-4821"),
                                  ("datadog", "warning", "mon-77"),
                                  ("langfuse", "error", "trace-9f")]:
            _as(src, keys[src])
            ba.emit("alert", f"alert:{src}:{level}:{ident}")
            print(f"   • {src}: {level} {ident}")

        _banner("5. agents wake and react (their output)")
        time.sleep(1.2)
        for p in listeners:
            p.terminate()
        for agent, p in zip([a[0] for a in agents], listeners):
            try:
                out, _ = p.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                out = ""
            for line in (out or "").splitlines():
                if "reconciler" in line or "triage" in line or "woken" in line:
                    print(f"   [{agent}] {line}")

        _banner("6. the resulting event stream (producers → agents → results)")
        for e in brain.event_read(0):
            if e["kind"] == "subscribe":
                continue
            print(f"   seq={e['seq']:<2} {e['kind']:6} by {e['agent']:22} "
                  f"→ {e['ref']}")

        _banner("loop demonstrated: an action → a wake → an agent's "
                "reaction, all local, all signed.")
        return 0
    finally:
        for p in listeners:
            p.terminate()
        hub.terminate()
        try:
            hub.wait(timeout=5)
        except subprocess.TimeoutExpired:
            hub.kill()
        brain.AGENT_KEYS.unlink(missing_ok=True)
        brain.EVENT_CURSORS.unlink(missing_ok=True)
        shutil.rmtree(brain.EVENTS_DIR, ignore_errors=True)
        tmp_cursors.unlink(missing_ok=True)
        for k in ("BRAIN_URL", "BRAIN_AGENT_ID", "BRAIN_AGENT_SECRET",
                  "BRAIN_AGENT_CURSORS"):
            os.environ.pop(k, None)
        print("\n(emulation state cleaned up)")


if __name__ == "__main__":
    sys.exit(main())
