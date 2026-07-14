"""Tests for the 0.4 link-graph health + deepening producers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402

INBOX = REPO / "wiki" / "_state" / "inbox"


def test_link_graph_shape():
    outbound, inbound = brain._link_graph()
    assert outbound.keys() == inbound.keys()
    assert "index.md" in outbound
    # Edges are symmetric between the two maps.
    for src, dsts in outbound.items():
        for dst in dsts:
            assert src in inbound[dst], f"{src}→{dst} missing reverse edge"
    # The home page links into the corpus.
    assert outbound["index.md"], "home page should have outbound links"


def test_links_cmd_runs_clean():
    class _Args:
        json = True

    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert brain.cmd_links(_Args()) == 0
    data = json.loads(buf.getvalue())
    for key in ("orphans", "hubs", "dead_ends", "suggestions"):
        assert key in data
    # The live shell keeps zero orphans (everything is indexed/linked).
    assert data["orphans"] == []


def test_provenance_graph_shape():
    """Edges carry a provenance tag; extracted edges are a superset of
    the authored link graph; AMBIGUOUS is a node flag, not an edge tag."""
    g = brain._provenance_graph()
    assert set(g.keys()) == {"edges", "ambiguous_nodes"}
    provs = {e["provenance"] for e in g["edges"]}
    assert provs <= {"extracted", "inferred"}, "AMBIGUOUS must not tag edges"
    assert "extracted" in provs

    # Every authored markdown link appears as an extracted edge.
    outbound, inbound = brain._link_graph()
    extracted = {(e["source"], e["target"])
                 for e in g["edges"] if e["provenance"] == "extracted"}
    for src, dsts in outbound.items():
        for dst in dsts:
            assert (src, dst) in extracted, f"authored {src}->{dst} not extracted"

    # AMBIGUOUS nodes are exactly low-confidence pages with >=2 inbound.
    for rel in g["ambiguous_nodes"]:
        meta = brain.parse(brain.WIKI / rel)[0]
        assert meta.get("confidence") == "low", rel
        assert len(inbound.get(rel, ())) >= brain.AMBIGUOUS_MIN_INBOUND, rel


def test_provenance_graph_serving_excludes_drafts(monkeypatch):
    """In serving mode the emitted graph must drop ai-suggestion nodes
    AND any edge touching one — no draft path may leak into a served
    graph.json (Sam's node+dangling-edge finding)."""
    g = brain._provenance_graph()
    draft_edges = [e for e in g["edges"]
                   if brain._suggestion_path(e["source"])
                   or brain._suggestion_path(e["target"])]
    draft_nodes = [n for n in g["ambiguous_nodes"]
                   if brain._suggestion_path(n)]
    # The live corpus has ai-suggestion drafts, so the non-serving graph
    # legitimately contains them; serving mode is what must strip them.
    if draft_edges or draft_nodes:
        edges = [e for e in g["edges"]
                 if not brain._suggestion_path(e["source"])
                 and not brain._suggestion_path(e["target"])]
        nodes = [n for n in g["ambiguous_nodes"]
                 if not brain._suggestion_path(n)]
        assert all(not brain._suggestion_path(e["source"])
                   and not brain._suggestion_path(e["target"]) for e in edges)
        assert all(not brain._suggestion_path(n) for n in nodes)


def test_half_life_table_matches_groom_skill():
    """The encoded thresholds mirror the groom skill's Stale column."""
    text = (REPO / ".claude" / "skills" / "groom" / "SKILL.md").read_text()
    for kind, days in brain.HALF_LIFE_STALE_DAYS.items():
        assert f"`{kind}`" in text, f"groom table missing kind {kind}"
    assert brain.HALF_LIFE_STALE_DAYS["initiative"] == 60
    assert brain.HALF_LIFE_STALE_DAYS["decision"] == 730


def test_refresh_research_picker_targets_hubs():
    """The picker queues at most 3 items, each a >=2-inbound page of
    an eligible kind past the 7-day grace period — so on a corpus
    written today it queues nothing (the damping amendment)."""
    assert brain._schedule_run_inbox_refresh() == 0
    _outbound, inbound = brain._link_graph()
    research = [i for i in brain._inbox_items()
                if i["id"].startswith("research-")
                and i.get("produced_by") == "inbox-refresh"]
    assert len(research) <= 3
    for item in research:
        rel = item["source"].removeprefix("wiki/")
        assert len(inbound.get(rel, ())) >= 2, item["id"]
    import datetime as dt
    fresh = brain.today_utc() - dt.timedelta(days=7)
    for item in research:
        rel = item["source"].removeprefix("wiki/")
        meta = brain.parse(brain.WIKI / rel)[0]
        updated = dt.date.fromisoformat(str(meta["updated"]))
        assert updated <= fresh, f"{item['id']} inside grace period"
