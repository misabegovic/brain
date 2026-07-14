"""Tests for the derived index + composable view layer
(per wiki/brain/adrs/sql-views-over-derived-index.md)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


@pytest.fixture(scope="module")
def index():
    stats = brain._build_index()
    yield stats


def test_index_builds_with_all_tables(index):
    assert index["pages"] > 0
    db = brain._index_connect()
    tables = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    for t in ("pages", "links", "inbox", "state", "snapshots",
              "pages_fts", "snapshots_fts"):
        assert t in tables, f"missing table {t}"


def test_index_is_read_only_for_consumers(index):
    db = brain._index_connect()
    with pytest.raises(sqlite3.OperationalError):
        db.execute("INSERT INTO pages(path) VALUES('rogue.md')")


def test_fts_search_ranks_relevant_page_first(index):
    db = brain._index_connect()
    rows = db.execute(
        "SELECT p.path FROM pages_fts JOIN pages p "
        "ON p.rowid = pages_fts.rowid "
        "WHERE pages_fts MATCH ? ORDER BY rank LIMIT 3",
        (brain._fts_quote("connector snapshot contract"),)).fetchall()
    # The ADR surfaces prominently. Assert top-3 rather than rank-0:
    # a genuinely-relevant new page (e.g. a connector suggestion) can
    # legitimately out-rank it as the corpus grows.
    assert any("connector-snapshot-contract" in r[0] for r in rows)


def test_fts_quote_neutralises_match_syntax():
    quoted = brain._fts_quote('drop AND table" OR x*')
    assert '"drop"' in quoted and '"AND"' in quoted
    assert '""' in quoted  # embedded quote doubled
    db = brain._index_connect() or sqlite3.connect(":memory:")
    # Must not raise FTS5 syntax errors.
    db.execute("SELECT * FROM pages_fts WHERE pages_fts MATCH ? LIMIT 1",
               (brain._fts_quote('NEAR( OR "unbalanced'),))


def test_compile_block_shorthands():
    sql, params, style = brain._compile_block(
        {"pages": {"kind": "decision", "status": "accepted"}})
    assert "kind = ?" in sql and params == ["decision", "accepted"]
    assert style == "pages"
    sql, params, style = brain._compile_block({"state": "deadlines"})
    assert "surface = ?" in sql and params == ["deadlines"] and style == "state"
    sql, params, style = brain._compile_block({"inbox": {"kind": "research"}})
    assert "kind = ?" in sql and params == ["research"] and style == "inbox"
    with pytest.raises(ValueError):
        brain._compile_block({"title": "no block type"})


def test_pages_brief_links_by_title_not_path():
    rows = [("brain/adrs/foo.md", "The Foo Decision", "superseded", "low",
             "2026-07-12")]
    out = brain._render_pages_brief(rows, "*(empty)*")
    assert "[The Foo Decision](/brain/adrs/foo/)" in out
    assert "**superseded**" in out  # non-current status is emphasised
    assert ".md" not in out, "raw path must not appear in the brief"
    assert brain._render_pages_brief([], "*None here*") == "*None here*\n"


def test_custom_views_render_from_specs(index):
    rendered = brain._render_custom_views()
    assert set(rendered) >= {"engineer", "pm", "operator"}
    engineer = (REPO / "wiki" / "_views" / "custom" / "engineer.md").read_text()
    assert "## Recent decisions" in engineer
    assert "block error" not in engineer, "a spec block failed to execute"
    # Reader-first: the generation note is a footer, not the lead.
    assert "*(no rows)*" not in engineer, "bare empty state leaked to reader"
    assert engineer.rstrip().endswith("*") and "Generated from" in engineer
    pm = (REPO / "wiki" / "_views" / "custom" / "pm.md").read_text()
    assert "block error" not in pm
    operator = (REPO / "wiki" / "_views" / "custom" / "operator.md").read_text()
    assert "block error" not in operator


def test_custom_views_are_deterministic(index):
    out = REPO / "wiki" / "_views" / "custom" / "engineer.md"
    brain._render_custom_views()
    first = out.read_text()
    brain._render_custom_views()
    assert out.read_text() == first


def test_new_connectors_noop_when_unconfigured():
    assert brain._connector_datadog_pull() == 0
    assert brain._connector_langfuse_pull() == 0
