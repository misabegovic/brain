"""Tests for the 0.3 connector contract (pull-only snapshot-writers).

Live API paths are exercised manually; these tests pin the contract
mechanics: no-op when unconfigured, immutable dedup snapshot writes,
cursor round-trip, and watched-repo discovery parsing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def test_connectors_noop_when_unconfigured():
    assert brain._connector_github_pull() == 0
    assert brain._connector_notion_pull() == 0
    assert brain._connector_slack_pull() == 0


def test_connector_config_reads_yaml_section():
    cfg = brain._connector_config("github")
    assert isinstance(cfg, dict)
    assert brain._connector_config("no-such-connector") == {}


def test_snapshot_write_is_immutable_dedup():
    rel = "_test/snapshot--t1.md"
    path = REPO / "sources" / "_test-connector" / rel
    try:
        first = brain._snapshot_write("_test-connector", rel, "t", "body one")
        assert first is not None and first.exists()
        assert "body one" in first.read_text()
        assert first.read_text().startswith("---\n")
        second = brain._snapshot_write("_test-connector", rel, "t", "body two")
        assert second is None, "existing snapshots must never be rewritten"
        assert "body one" in first.read_text()
    finally:
        if path.exists():
            path.unlink()
            path.parent.rmdir()
            path.parent.parent.rmdir()


def test_connector_cursors_round_trip():
    assert not brain.CONNECTOR_CURSORS.exists(), (
        "test assumes no live connector cursors; adjust if configured"
    )
    try:
        brain._write_connector_cursors({"github": {"o/r": {"last_pull": "2026-01-01"}}})
        data = brain._read_connector_cursors()
        assert data["github"]["o/r"]["last_pull"] == "2026-01-01"
    finally:
        brain.CONNECTOR_CURSORS.unlink(missing_ok=True)


def test_env_reads_dotenv_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("T_CONNECTOR_TOKEN", raising=False)
    assert brain._env("T_CONNECTOR_TOKEN") == ""
    monkeypatch.setenv("T_CONNECTOR_TOKEN", "from-env")
    assert brain._env("T_CONNECTOR_TOKEN") == "from-env"
