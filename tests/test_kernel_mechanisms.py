"""Tests for the kernel mechanisms added after the shell extraction.

Covers the brain.config.yml-driven repo registry, the generic
deadline-countdown schedule op, the config-driven no-op behaviour of
the state-refresh ops, and the internal-refs reflection detector (the
standalone guarantee).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


# ---------- brain.config.yml registry ------------------------------------

def test_load_repo_config_reads_declared_repos(tmp_path):
    cfg = tmp_path / "brain.config.yml"
    cfg.write_text(
        "org: Example\n"
        "active_repos:\n  - app\n  - api\n"
        "archived_repos:\n  - legacy\n"
    )
    active, archived = brain._load_repo_config(cfg)
    assert active == {"app", "api"}
    assert archived == {"legacy"}


def test_load_repo_config_missing_file_is_empty(tmp_path):
    active, archived = brain._load_repo_config(tmp_path / "nope.yml")
    assert active == set()
    assert archived == set()


def test_load_repo_config_malformed_yaml_is_empty(tmp_path):
    cfg = tmp_path / "brain.config.yml"
    cfg.write_text("active_repos: [unclosed\n  - ]broken")
    active, archived = brain._load_repo_config(cfg)
    assert active == set()
    assert archived == set()


def test_valid_repos_is_registry_plus_meta_levels():
    assert brain.VALID_REPOS == (
        brain.ACTIVE_REPOS | brain.ARCHIVED_REPOS | brain.META_LEVELS
    )


# ---------- deadline-countdown -------------------------------------------

DEADLINES_PATH = REPO / "wiki" / "_state" / "deadlines.json"


def test_deadline_countdown_noop_when_untracked():
    assert not DEADLINES_PATH.exists(), (
        "test assumes the shell tracks no deadlines; "
        "adjust if wiki/_state/deadlines.json is now real"
    )
    assert brain._schedule_run_deadline_countdown() == 0
    assert not DEADLINES_PATH.exists(), "no-op must not create the file"


def test_deadline_countdown_refreshes_days_left():
    DEADLINES_PATH.write_text(json.dumps({
        "deadlines": [
            {"name": "cert-renewal", "date": "2099-01-01"},
            {"name": "past-date", "date": "2000-01-01", "readiness": "high"},
        ]
    }))
    try:
        assert brain._schedule_run_deadline_countdown() == 0
        state = json.loads(DEADLINES_PATH.read_text())
        assert state["last_assessment"] == brain.today_utc().isoformat()
        by_name = {d["name"]: d for d in state["deadlines"]}
        assert by_name["cert-renewal"]["_days_left"] > 0
        assert by_name["past-date"]["_days_left"] < 0
        # Operator-maintained fields are untouched.
        assert by_name["past-date"]["readiness"] == "high"
    finally:
        DEADLINES_PATH.unlink()


# ---------- state-refresh ops no-op without registry entries -------------

def test_security_scan_noop_without_active_repos():
    if brain.ACTIVE_REPOS:
        return  # only meaningful on an empty-registry shell
    state_path = REPO / "wiki" / "_state" / "security.json"
    existed_before = state_path.exists()
    assert brain._schedule_run_security_scan() == 0
    assert state_path.exists() == existed_before, (
        "no-op must not create the state file"
    )


def test_issues_pull_noop_without_active_repos():
    if brain.ACTIVE_REPOS:
        return
    state_path = REPO / "wiki" / "_state" / "issues.json"
    existed_before = state_path.exists()
    assert brain._schedule_run_issues_pull() == 0
    assert state_path.exists() == existed_before


def test_notion_walk_noop_without_snapshots():
    if (REPO / "sources" / "notion").exists():
        return  # only meaningful before the first snapshot lands
    assert brain._schedule_run_notion_walk() == 0


# ---------- internal-refs detector ---------------------------------------

def _run_reflection(which: str) -> int:
    class _Args:
        pass

    args = _Args()
    args.which = which
    return brain.cmd_reflection_check(args)


def test_internal_refs_clean_on_live_repo():
    assert _run_reflection("internal-refs") == 0


def test_internal_refs_catches_planted_violation():
    rogue = REPO / ".claude" / "_rogue_internal_ref_test.md"
    rogue.write_text(
        "This doc cites [a missing page](../wiki/brain/adrs/no-such-adr.md) "
        "and the path `tools/definitely-missing.py` in prose.\n"
    )
    try:
        assert _run_reflection("internal-refs") == 1, (
            "detector missed a planted dangling reference"
        )
    finally:
        rogue.unlink()


def test_topic_kind_validates():
    assert "topic" in brain.VALID_KINDS
    assert brain.REQUIRED_SECTIONS_BY_KIND["topic"] == [
        "Question", "Discussion", "Outcome"]
    assert (REPO / "tools" / "templates" / "topic.md").exists()


def test_instance_birth(tmp_path):
    """The first 1.0 criterion, executable: init --full births an
    instance whose own gates pass and which carries no dogfood."""
    import subprocess
    target = tmp_path / "instance"
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "brain.py"), "init",
         str(target), "--full", "--org", "T"],
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr[:800]
    # Mechanism crossed.
    for rel in ("tools/brain.py",
                ".claude/skills/tend/SKILL.md", "views/engineer.yml",
                "wiki/brain/adrs/queue-and-tend-inbox.md",
                "wiki/org/methodology/superpowers.md"):
        assert (target / rel).exists(), f"kernel path missing: {rel}"
    # Dogfood did not.
    for rel in ("wiki/brain/roadmap.md", "wiki/brain/topics",
                "wiki/brain/pitches", "sources/research",
                "sources/conversations", "wiki/org/competitors"):
        assert not (target / rel).exists(), f"dogfood leaked: {rel}"
    # The instance's own detectors run clean.
    import os
    env = {**os.environ, "BRAIN_DIR": str(target)}
    check = subprocess.run(
        [sys.executable, str(target / "tools" / "brain.py"),
         "reflection-check"],
        cwd=target, env=env, capture_output=True, text=True, timeout=60)
    assert check.returncode == 0, check.stdout[:800]


# ---------- playthrough version-cursor producer ---------------------------

PLAYTHROUGH_CURSOR = REPO / "wiki" / "_state" / "playthrough-cursor.json"


def test_playthrough_cursor_initialises_silently(tmp_path):
    """First run writes the cursor without queueing — a fresh shell
    or newborn instance owes no sweep."""
    existed = PLAYTHROUGH_CURSOR.read_text() if PLAYTHROUGH_CURSOR.exists() \
        else None
    if PLAYTHROUGH_CURSOR.exists():
        PLAYTHROUGH_CURSOR.unlink()
    try:
        brain._playthrough_queue_slice()
        state = json.loads(PLAYTHROUGH_CURSOR.read_text())
        assert state["version"] == (REPO / "VERSION").read_text().strip()
        item = REPO / "wiki" / "_state" / "inbox" / (
            "playthrough-" + state["version"].replace(".", "-") + ".json")
        assert not item.exists(), "first run must not queue a sweep"
    finally:
        if existed is not None:
            PLAYTHROUGH_CURSOR.write_text(existed)
        elif PLAYTHROUGH_CURSOR.exists():
            PLAYTHROUGH_CURSOR.unlink()


def test_playthrough_cursor_queues_once_per_bump():
    existed = PLAYTHROUGH_CURSOR.read_text() if PLAYTHROUGH_CURSOR.exists() \
        else None
    version = (REPO / "VERSION").read_text().strip()
    slug = version.replace(".", "-")
    item = REPO / "wiki" / "_state" / "inbox" / f"playthrough-{slug}.json"
    item_existed = item.exists()
    PLAYTHROUGH_CURSOR.write_text(json.dumps({"version": "0.0.0"}))
    try:
        brain._playthrough_queue_slice()
        assert item.exists(), "version bump must queue a sweep item"
        data = json.loads(item.read_text())
        assert data["produced_by"] == "playthrough-cursor"
        assert data["route"] == "/playthrough"
        # Cursor advanced at queue time: a second run is a no-op,
        # and a tended (done) item is never re-queued.
        item.unlink()
        brain._playthrough_queue_slice()
        assert not item.exists(), "swept item must not be re-queued"
    finally:
        if not item_existed:
            item.unlink(missing_ok=True)
        if existed is not None:
            PLAYTHROUGH_CURSOR.write_text(existed)
        else:
            PLAYTHROUGH_CURSOR.unlink(missing_ok=True)


def test_playthrough_surfaces_ship():
    assert (REPO / ".claude" / "skills" / "playthrough" / "SKILL.md").exists()
    assert (REPO / ".claude" / "commands" / "playthrough.md").exists()
    personas = list((REPO / ".claude" / "personas" / "users").glob("*.md"))
    assert len(personas) >= 4, "the brain's own user personas must ship"
