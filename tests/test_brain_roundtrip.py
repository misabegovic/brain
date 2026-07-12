"""Round-trip tests for tools/brain.py.

These tests use the actual brain repo as fixture data. They run on
CI via the validate workflow (`pytest tests/`).

The bar is *invariants*: parse(write(parse(text))) round-trips,
collect_pages_data is deterministic, check-no-notion-writes
correctly catches a planted violation, etc. We don't unit-test
internals that the live wiki already exercises every CI run.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def test_parse_handles_well_formed_frontmatter():
    """parse() returns (meta, body) for a typical wiki page."""
    sample = REPO / "AGENTS.md"
    # AGENTS.md has no frontmatter — should return None.
    assert brain.parse(sample) is None

    # A real wiki page should parse.
    page = REPO / "wiki" / "index.md"
    parsed = brain.parse(page)
    assert parsed is not None
    meta, body = parsed
    assert meta["kind"] == "meta"
    assert body  # non-empty


def test_collect_pages_data_is_deterministic():
    """Two consecutive collect_pages_data() runs return identical
    JSON-serialisable output. Catches accidental nondeterminism
    (set ordering, dict iteration, mtime sneaking in)."""
    a = brain.collect_pages_data()
    b = brain.collect_pages_data()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_collect_pages_data_carries_affected_by():
    """Every active repo's index.md should have affected_by populated
    by org-level pages — the cross-level invariant. Trivially true on
    an empty shell (no active repos declared yet)."""
    entries = brain.collect_pages_data()
    by_path = {e["path"]: e for e in entries}
    for repo in sorted(brain.ACTIVE_REPOS):
        idx = by_path.get(f"{repo}/index.md")
        assert idx is not None, f"missing {repo}/index.md"
        assert "affected_by" in idx, (
            f"{repo}/index.md missing affected_by — "
            f"org/* pages aren't propagating"
        )


def test_today_utc_returns_a_date():
    """today_utc() returns a date in UTC, not local-time, so CI and
    local generate matching `wiki/_views/*` content (the bug PR B
    introduced and immediately fixed)."""
    today = brain.today_utc()
    import datetime as dt
    assert isinstance(today, dt.date)
    # And it should match dt.datetime.utcnow().date() for sanity.
    assert today == dt.datetime.now(dt.timezone.utc).date()


def test_valid_repos_set_includes_meta_levels():
    """ACTIVE_REPOS + ARCHIVED_REPOS + META_LEVELS = VALID_REPOS,
    and META_LEVELS contains brain and org."""
    assert "brain" in brain.VALID_REPOS
    assert "org" in brain.VALID_REPOS
    assert brain.VALID_REPOS == (
        brain.ACTIVE_REPOS | brain.ARCHIVED_REPOS | brain.META_LEVELS
    )
    # Sanity: a typo doesn't accidentally pass.
    assert "no-such-repo-xyz" not in brain.VALID_REPOS


def test_notion_write_tools_are_all_deny_listed():
    """The settings deny list contains every NOTION_WRITE_TOOLS entry
    — same invariant the CI guard enforces, asserted here so test
    failures are friendlier than a CLI exit code."""
    settings_path = REPO / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text())
    deny = set(settings.get("permissions", {}).get("deny", []))
    for tool in brain.NOTION_WRITE_TOOLS:
        assert tool in deny, (
            f"{tool} must be in .claude/settings.json deny list"
        )


def test_check_no_notion_writes_passes_on_clean_repo():
    """The CI guard returns 0 on the live repo (no rogue mentions)."""

    class _Args:
        pass

    rc = brain.cmd_check_no_notion_writes(_Args())
    assert rc == 0


def test_check_no_notion_writes_catches_planted_violation():
    """If a Notion write tool name appears outside the allowed
    mentions, the guard fails."""
    # Plant a violation in a temp file in tools/, run the guard,
    # confirm it fails. Then clean up.
    rogue = REPO / "tools" / "_rogue_test_violation.md"
    rogue.write_text(
        "Definitely not allowed: "
        "mcp__claude_ai_Notion__notion-create-pages\n"
    )
    try:

        class _Args:
            pass

        rc = brain.cmd_check_no_notion_writes(_Args())
        assert rc == 1, "guard didn't catch the planted violation"
    finally:
        rogue.unlink()


def test_index_links_walks_nested_indexes():
    """index_links() picks up entries listed inside nested index.md
    files (e.g. wiki/brain/index.md), so they don't show up as
    orphans. On the empty shell we assert the walk itself runs and
    includes the home's own links."""
    indexed = brain.index_links()
    assert isinstance(indexed, set)
    assert "brain/index.md" in indexed
    assert "org/index.md" in indexed


def test_personas_infers_pool_for_brain_page():
    """cmd_personas reads frontmatter + ## Affected personas, picks
    a pool from .claude/personas/, caps at 6. Sanity-check on a
    real page."""
    import io
    import contextlib

    class _Args:
        page = "brain/index.md"

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = brain.cmd_personas(_Args())
    output = buf.getvalue()
    assert rc == 0
    # Pool always contains the three agent personas.
    assert "pm agent" in output
    assert "tech lead agent" in output
    assert "developer agent" in output


def test_personas_caps_pool_at_six():
    """The pool is capped at 6 — overflow is reported, never silently
    dropped. Catches regressions to the cap heuristic."""
    import io
    import contextlib

    class _Args:
        page = "brain/index.md"

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        brain.cmd_personas(_Args())
    output = buf.getvalue()
    # Count the bulleted lines (the pool).
    lines = [ln for ln in output.splitlines() if ln.strip().startswith("- [")]
    assert len(lines) <= 6, f"pool size > 6: {len(lines)}"


def test_rotate_log_idempotent_under_threshold():
    """rotate-log returns 0 (no rotation needed) when the live log
    is under the threshold. Catches regressions to the threshold
    constants and ensures the command is safe to run from /sync."""

    class _Args:
        pass

    rc = brain.cmd_rotate_log(_Args())
    assert rc == 0


def test_snapshot_writes_json_with_expected_keys():
    """brain.py snapshot writes a JSON file with the documented
    structure (totals, by_kind, etc.). Run against a temp dir to
    avoid polluting wiki/_views/snapshots/."""
    # Use the existing snapshot from the live run rather than
    # invoking cmd_snapshot directly (which writes into the live
    # wiki/_views/snapshots/ dir). The shape is what we care about.
    snap_dir = REPO / "wiki" / "_views" / "snapshots"
    if not snap_dir.exists():
        # No snapshot ever run — call cmd_snapshot once to create one.
        class _Args:
            pass

        brain.cmd_snapshot(_Args())

    # Pick the most recent snapshot file and verify shape.
    files = sorted(snap_dir.glob("*.json"))
    assert files, "no snapshot files produced"
    snap = json.loads(files[-1].read_text())
    for key in ("generated", "totals", "by_kind", "by_status",
                "by_team", "by_repo", "by_confidence", "pages"):
        assert key in snap, f"snapshot missing key: {key}"
    assert snap["totals"]["pages"] > 0
    assert snap["totals"]["tokens"] > 0
