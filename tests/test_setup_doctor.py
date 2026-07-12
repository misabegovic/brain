"""Tests for the hands-off surface: brain.py setup / doctor / the
/dash renderer."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def test_doctor_checks_shape():
    checks = brain._doctor_checks()
    assert len(checks) >= 8
    for c in checks:
        assert c["status"] in ("ok", "warn", "fail"), c
        assert c["label"] and c["detail"]
        if c["status"] != "ok":
            assert c["hint"], f"{c['id']}: non-ok check needs a fix hint"
    # The live shell must never be in a failing state.
    assert not [c for c in checks if c["status"] == "fail"]


def test_doctor_exit_code_tracks_failures():
    class _Args:
        json = False

    assert brain.cmd_doctor(_Args()) == 0


def test_setup_dry_run_changes_nothing():
    config_before = (REPO / "brain.config.yml").read_text()

    class _Args:
        org = "Dry Run Org"
        repos = "app,api"
        yes = False
        dry_run = True

    assert brain.cmd_setup(_Args()) == 0
    assert (REPO / "brain.config.yml").read_text() == config_before


def test_dash_renders_core_sections():
    html = brain._render_dash(page_count=22)
    for needle in ("Health", "Tend queue", "Quick start", "doctor",
                   "/tend", "22 pages"):
        assert needle in html, f"dash missing {needle!r}"
    # Escaping sanity: no raw template braces or python reprs leak.
    assert "{esc(" not in html


def test_local_first_detection_is_anchored(tmp_path):
    """LOCAL_FIRST must be read anchored — a substring scan also
    matches the commented .env.example boilerplate, which made
    doctor report local-first after the operator removed the flag
    (Viktor playthrough, 2026-07-12)."""
    import brain
    commented = tmp_path / "env-commented"
    commented.write_text(
        "# LOCAL_FIRST=true suspends the PR ritual\n"
        "# LOCAL_FIRST=true\nBRAIN_PORT=8765\n")
    assert brain._local_first(commented) is False
    active = tmp_path / "env-active"
    active.write_text("LOCAL_FIRST=true\n")
    assert brain._local_first(active) is True
    absent = tmp_path / "env-none"
    active.write_text("BRAIN_PORT=8765\n")
    assert brain._local_first(tmp_path / "nope") is False


def test_producer_health_states(tmp_path, monkeypatch):
    """Producer freshness is distinct from timer-installed: a stalled
    heartbeat is a fail (empty queue = silence, not calm)."""
    import brain
    import time
    monkeypatch.setattr(brain, "PRODUCER_HEARTBEAT", tmp_path / "hb.json")
    assert brain._producer_health()["state"] == "never"
    brain._producer_touch()
    assert brain._producer_health()["state"] == "current"
    (tmp_path / "hb.json").write_text(
        '{"last_run":"old","epoch":%d}' % (int(time.time()) - 48 * 3600))
    assert brain._producer_health()["state"] == "stalled"


def test_check_no_personal_data_rejects_session_url(tmp_path):
    """The commit-msg guard rejects session URLs but passes clean
    messages (incl. Co-Authored-By model attribution)."""
    import subprocess
    import sys
    from pathlib import Path
    repo = Path(__file__).resolve().parent.parent
    def run(text):
        return subprocess.run(
            [sys.executable, str(repo / "tools" / "brain.py"),
             "check-no-personal-data"],
            input=text, capture_output=True, text=True).returncode
    assert run("fix\n\nClaude-Session: https://claude.ai/code/session_ABC") == 1
    assert run("fix\n\nCo-Authored-By: Claude <noreply@anthropic.com>") == 0
    assert run("a normal message") == 0
