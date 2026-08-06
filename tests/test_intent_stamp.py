"""Intent stamping — the derived `enola_intent.page` block.

The whole wiki compiles into the architecture graph: `brain.py intent
stamp` derives each page's declaration from the frontmatter it already
carries, and the `intent-page-block` reflection detector re-derives and
compares. These tests pin the derivation shapes and the idempotence
invariant over the live wiki, so a drifted stamp fails the suite
instead of compiling a lie.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def derive(meta, rel="brain/topics/x.md"):
    block, errors = brain._derive_page_block(Path(rel), meta)
    return block, errors


def test_kind_and_repos_become_type_and_scope():
    block, _ = derive({"kind": "decision", "status": "accepted",
                       "repos": ["backend"]})
    assert block["type"] == "decision"
    assert block["status"] == "accepted"
    assert block["scope"] == ["backend"]


def test_sibling_citations_become_sorted_anchors():
    block, _ = derive({
        "kind": "decision",
        "sources": [
            "~/projects/backend/app/services/formatter.rb",
            "~/projects/cli/package.json",
            "~/projects/backend/app/services/formatter.rb",
        ],
    })
    assert block["anchors"] == [
        {"repo": "backend", "path": "app/services/formatter.rb"},
        {"repo": "cli", "path": "package.json"},
    ]


def test_annotated_and_repo_only_citations_do_not_anchor():
    block, _ = derive({
        "kind": "decision",
        "sources": [
            "~/projects/backend",
            "~/projects/backend/app/old.rb (removed; page needs re-ingest)",
            "https://example.com/spec",
        ],
    })
    assert "anchors" not in block


def test_stamp_is_idempotent_over_the_live_wiki():
    """Re-deriving every stamped page must reproduce its stamped block —
    the invariant the intent-page-block detector enforces."""
    checked = 0
    for page in sorted((REPO / "wiki").rglob("*.md")):
        rel = page.relative_to(REPO / "wiki")
        if rel.parts[0] in ("_views", "_archive"):
            continue
        parsed = brain.parse(page)
        if not parsed:
            continue
        meta, _ = parsed
        stamped = (meta.get("enola_intent") or {}).get("page")
        if stamped is None:
            continue
        derived, _ = brain._derive_page_block(rel, meta)
        assert derived == stamped, f"{rel}: stamped block drifted from derivation"
        checked += 1
    assert checked > 50, "the whole wiki is expected to compile"
