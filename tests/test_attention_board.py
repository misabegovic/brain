"""The attention board's invariants, executable.

The board is the surface most able to rot quietly: a ranking nobody
can explain still renders, and a board that has quietly become a
backlog looks identical to one that is working. So the tests here are
mostly about the properties the ADR names rather than the plumbing —
that cards can leave without being done, that a dismissal is
permanent, that a score without its components is called out, and that
"nothing found" never renders like "nothing asked".

Everything runs against synthetic state or degrades-when-absent,
because a configured connector exists only on an operator's machine —
a test needing one would pass locally and fail in CI for the wrong
reason.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRAIN_PY = REPO / "tools" / "brain.py"
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def run(*args):
    return subprocess.run(
        [sys.executable, str(BRAIN_PY), *args],
        capture_output=True, text=True, cwd=REPO,
    )


# --- configuration is the operator's, mechanism is the kernel's -------


def test_categories_always_offer_an_off_surface_escape():
    # Signal outside the remit must have somewhere honest to go;
    # dropping it silently is how a board starts lying.
    assert brain.ATTENTION_OFF_SURFACE in brain._attention_categories()


def test_shipped_categories_name_no_organisation():
    # The kernel ships mechanism, never somebody's remit.
    text = (REPO / "brain.config.yml").read_text().lower()
    start = text.index("attention:")
    block = text[start:]
    for leaked in ("teamtailor", "copilot", "recruiter", "candidate"):
        assert leaked not in block, f"organisation term in config: {leaked}"


def test_category_weights_are_numeric():
    for name, weight in brain._attention_categories().items():
        assert isinstance(weight, float), f"{name} weight is not numeric"


def test_board_caps_are_configured_not_hardcoded():
    config = brain._attention_config()
    assert config["now_tier_size"] >= 1
    assert config["max_active"] >= config["now_tier_size"]


# --- the readers emit one shape ---------------------------------------


def test_every_reader_emits_the_same_candidate_shape(tmp_path):
    """The containment the ADR names: readers normalise, nothing more.

    If a reader ever returns a different shape, the board has started
    learning connector formats and the coupling is no longer bounded.
    """
    snap = tmp_path / "snap.md"
    snap.write_text("---\ntitle: T\nconnector: c\npulled: 2026-08-04\n"
                    "repo: o/r\ncount: 3\n---\n\nbody\n")
    fm = brain._attention_snapshot_frontmatter(snap)
    assert fm["title"] == "T"
    expected = set(brain._attention_candidate("i", "o", "s", "src"))
    for name, reader in brain.ATTENTION_READERS.items():
        cand = reader(name, snap, fm)
        assert set(cand) == expected, f"{name} reader widened the shape"
        assert isinstance(cand["signals"], dict)


def test_generic_reader_handles_a_connector_it_has_never_seen(tmp_path):
    snap = tmp_path / "unknown.md"
    snap.write_text("---\ntitle: X\nconnector: brand-new\n"
                    "pulled: 2026-08-04\n---\n\nb\n")
    fm = brain._attention_snapshot_frontmatter(snap)
    cand = brain._attention_reader_generic("brand-new", snap, fm)
    assert cand["origin"] == "connector:brand-new"
    assert cand["summary"] == "X"


def test_unparseable_snapshot_yields_nothing_rather_than_crashing(tmp_path):
    junk = tmp_path / "junk.md"
    junk.write_text("not a snapshot at all\n")
    assert brain._attention_snapshot_frontmatter(junk) == {}


# --- the invariants that keep it a board and not a backlog ------------


def test_a_card_can_leave_without_being_done():
    # The whole distinction from the inbox: dismissal is an exit.
    assert "dismissed" in brain.ATTENTION_STATUSES
    assert "done" in brain.ATTENTION_STATUSES


def test_dismissal_is_permanent_in_the_collector():
    # A tombstone is a decision; a collector that resurrects it turns
    # the board back into a queue.
    src = BRAIN_PY.read_text()
    assert "the collector never resurrects" in src


def test_untriaged_is_a_collector_default_not_a_resting_state():
    assert "untriaged" in brain.ATTENTION_TIERS
    skill = (REPO / ".claude" / "skills" / "attention" / "SKILL.md").read_text()
    assert "Zero `untriaged` cards remain" in skill


def test_now_tier_is_capped_and_the_skill_refuses_to_widen_it():
    skill = (REPO / ".claude" / "skills" / "attention" / "SKILL.md").read_text()
    assert "Never widen the tier" in skill


def test_committed_cards_carry_no_pending_state():
    if not brain.ATTENTION_CARDS.exists():
        return
    store = json.loads(brain.ATTENTION_CARDS.read_text())
    for card in store.get("cards", []):
        assert card.get("status") in brain.ATTENTION_STATUSES
        assert card.get("tier") in brain.ATTENTION_TIERS
        assert not set(card) & {"pending", "todo", "due"}


def test_committed_cards_explain_any_score_they_carry():
    """A rank nobody can explain is a rank nobody will trust."""
    if not brain.ATTENTION_CARDS.exists():
        return
    store = json.loads(brain.ATTENTION_CARDS.read_text())
    for card in store.get("cards", []):
        if card.get("score") is not None:
            assert card.get("components"), (
                f"{card['id']} has a score with no components")


# --- honesty about coverage -------------------------------------------


def test_channel_line_distinguishes_quiet_from_unasked():
    store = {"cards": [], "channels": {
        "a": {"answered": True, "candidates": 0},
        "b": {"answered": False, "reason": "no snapshots pulled yet"}}}
    line = brain._attention_channel_line(store)
    assert "1 of 2" in line


def test_empty_board_still_renders_with_its_coverage_line():
    # A missing file and an empty board must not be the same artifact.
    view = brain.WIKI / "_views" / "attention.md"
    assert view.exists()
    assert "connector(s) answered" in view.read_text()


def test_ops_exit_zero_and_say_something_on_an_unconfigured_brain():
    for op in (["attention", "summary"], ["attention", "list"]):
        result = run(*op)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), f"{op} said nothing — a silent skip"


def test_set_rejects_a_category_outside_the_declared_set():
    result = run("attention", "set", "no-such-card", "--category", "nonsense")
    assert result.returncode == 1


def test_dismiss_requires_a_reason():
    result = run("attention", "dismiss", "no-such-card")
    assert result.returncode != 0
    assert "--reason" in (result.stderr + result.stdout)


# --- the board is documented where agents look ------------------------


def test_the_contract_names_the_board_and_its_split_from_tend():
    agents = (REPO / "AGENTS.md").read_text()
    assert "/attention" in agents
    skill = (REPO / ".claude" / "skills" / "attention" / "SKILL.md").read_text()
    assert "Not `/tend`" in skill


def test_relevance_model_ships_into_a_new_instance():
    # A board without its metric is unusable, so the page is kernel,
    # not dogfood.
    assert "wiki/brain/attention-relevance-model.md" in brain.KERNEL_COPY_PATHS


def test_relevance_model_admits_it_is_uncalibrated():
    """The weights were argued, not measured. Saying so is the point."""
    page = (REPO / "wiki" / "brain" / "attention-relevance-model.md").read_text()
    assert "not been calibrated" in page
    assert "## Revisions" in page


def test_the_committed_board_is_a_function_of_the_repo_not_one_machine():
    """A render built from untracked local state cannot survive a
    clean-room rebuild — the same rule the derived index follows."""
    src = BRAIN_PY.read_text()
    start = src.index("def _attention_inbox_candidates")
    end = src.index("def _attention_refresh")
    assert "tracked_only=True" in src[start:end]
