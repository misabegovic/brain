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
