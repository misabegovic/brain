"""Tests for the queue-and-tend inbox (brain.py inbox + inbox-refresh).

Per wiki/brain/adrs/queue-and-tend-inbox.md: per-item JSON files,
producer-chosen dedup ids (idempotent re-adds), refresh-op
reconciliation limited to its own items, one-line summary that never
fails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402

INBOX = REPO / "wiki" / "_state" / "inbox"


def _cleanup(*ids):
    for id in ids:
        (INBOX / f"{id}.json").unlink(missing_ok=True)


def test_inbox_add_is_idempotent_on_id():
    try:
        assert brain.inbox_add(id="t-dup", kind="custom", summary="first") is True
        assert brain.inbox_add(id="t-dup", kind="custom", summary="second") is False
        item = json.loads((INBOX / "t-dup.json").read_text())
        assert item["summary"] == "first"
    finally:
        _cleanup("t-dup")


def test_inbox_add_update_preserves_arrival_date():
    try:
        brain.inbox_add(id="t-up", kind="groom", summary="v1")
        original = json.loads((INBOX / "t-up.json").read_text())["produced_at"]
        assert brain.inbox_add(id="t-up", kind="groom", summary="v2",
                               update=True) is True
        item = json.loads((INBOX / "t-up.json").read_text())
        assert item["summary"] == "v2"
        assert item["produced_at"] == original
    finally:
        _cleanup("t-up")


def test_inbox_add_rejects_bad_input():
    import pytest
    with pytest.raises(ValueError):
        brain.inbox_add(id="Bad Id!", kind="custom", summary="x")
    with pytest.raises(ValueError):
        brain.inbox_add(id="t-kind", kind="nonsense", summary="x")
    with pytest.raises(ValueError):
        brain.inbox_add(id="t-prio", kind="custom", summary="x",
                        priority="urgent")


def test_inbox_refresh_reconciles_only_its_own_items():
    """A stale refresh-produced item is cleared on the next run;
    operator items survive untouched."""
    try:
        brain.inbox_add(id="cursor-diff-ghost", kind="ingest",
                        summary="stale machine item",
                        produced_by="inbox-refresh")
        brain.inbox_add(id="t-operator", kind="custom",
                        summary="operator item", produced_by="operator")
        assert brain._schedule_run_inbox_refresh() == 0
        assert not (INBOX / "cursor-diff-ghost.json").exists(), (
            "refresh must clear its own items whose trigger no longer holds"
        )
        assert (INBOX / "t-operator.json").exists(), (
            "refresh must never touch non-refresh items"
        )
    finally:
        _cleanup("cursor-diff-ghost", "t-operator")


def test_inbox_refresh_clean_on_empty_shell():
    before = {f.name for f in INBOX.glob("*.json")} if INBOX.exists() else set()
    assert brain._schedule_run_inbox_refresh() == 0
    after = {f.name for f in INBOX.glob("*.json")} if INBOX.exists() else set()
    # On a clean corpus with no cursors, refresh adds nothing new.
    assert after - before == set()


def test_inbox_summary_never_fails():
    class _Args:
        op = "summary"

    assert brain.cmd_inbox(_Args()) == 0


# ---------- attention judge/grade (presentation-layer ADR) ----------------

def test_inbox_judge_and_grade_round_trip():
    import json as _json
    import subprocess
    import sys as _sys
    iid = "test-judge-item"
    item = REPO / "wiki" / "_state" / "inbox" / f"{iid}.json"
    grades_path = REPO / "wiki" / "_state" / "attention-grades.json"
    grades_before = grades_path.read_text() if grades_path.exists() else None
    try:
        run = lambda *a: subprocess.run(
            [_sys.executable, str(REPO / "tools" / "brain.py"), "inbox", *a],
            capture_output=True, text=True, timeout=30)
        assert run("add", "--id", iid, "--kind", "custom",
                   "--summary", "test").returncode == 0
        out = run("judge", iid, "--attention", "needs-operator",
                  "--reason", "novel error class in prod")
        assert out.returncode == 0, out.stderr
        data = _json.loads(item.read_text())
        assert data["attention"] == "needs-operator"
        assert data["attention_reason"] == "novel error class in prod"
        assert data["judged"]
        out = run("grade", iid, "--grade", "noise", "--note", "not worth it")
        assert out.returncode == 0, out.stderr
        grades = _json.loads(grades_path.read_text())["grades"]
        rec = [g for g in grades if g["id"] == iid][-1]
        assert rec["grade"] == "noise"
        assert rec["verdict"] == "needs-operator"
        # Bad verdict is rejected at the parser.
        assert run("judge", iid, "--attention", "panic",
                   "--reason", "x").returncode == 2
    finally:
        item.unlink(missing_ok=True)
        if grades_before is not None:
            grades_path.write_text(grades_before)
        else:
            grades_path.unlink(missing_ok=True)
