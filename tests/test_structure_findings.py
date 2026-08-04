"""Findings + verdict ledger over the structure connector's facts.

The connector extracts code-shape *facts*; these tests cover the layer
that turns them into *findings* and records judgments about them.

Everything here runs on synthetic facts or degrades-when-absent, because
a configured target and a written snapshot exist only on an operator's
machine — a test that needed either would pass locally and fail in CI
for the wrong reason.

The ledger invariants are the load-bearing half: they encode the
no-pending-state rule that keeps the ledger a memory rather than a
backlog.
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


def _facts(modules, packages=None, symbols=None):
    return {"modules": modules,
            "packages": packages or {},
            "symbols": symbols or {}}


def test_oversized_package_fires_on_share_and_size():
    facts = _facts([f"big/m{i}.py" for i in range(30)]
                   + [f"small/m{i}.py" for i in range(5)],
                   packages={"big": 30, "small": 5})
    kinds = {f["explainer"] for f in brain._structure_findings(facts, "r")}
    assert "oversized-package" in kinds


def test_oversized_package_ignores_small_repos():
    # A package can be 100% of a five-file repo without meaning anything.
    facts = _facts([f"only/m{i}.py" for i in range(5)],
                   packages={"only": 5})
    kinds = {f["explainer"] for f in brain._structure_findings(facts, "r")}
    assert "oversized-package" not in kinds


def test_god_file_is_relative_to_the_repo_median():
    symbols = {f"m{i}.py": ["a"] * 2 for i in range(10)}
    symbols["huge.py"] = ["s"] * 40
    facts = _facts(list(symbols), packages={".": 11}, symbols=symbols)
    hits = [f for f in brain._structure_findings(facts, "r")
            if f["explainer"] == "god-file"]
    assert [h["signature"] for h in hits] == ["god-file:r:huge.py"]


def test_symbol_blindness_reports_what_the_substrate_cannot_see():
    facts = _facts([f"a{i}.go" for i in range(8)] + ["b.py"],
                   packages={".": 9}, symbols={"b.py": ["x"]})
    hits = [f for f in brain._structure_findings(facts, "r")
            if f["explainer"] == "symbol-blindness"]
    assert hits and hits[0]["confidence"] == 1.0


def test_no_findings_from_no_modules():
    assert brain._structure_findings(_facts([]), "r") == []


def test_verdict_matches_exact_signature_before_rule():
    ledger = {"entries": [
        {"match": {"explainer": "god-file"}, "verdict": "noise", "why": "cls"},
        {"signature": "god-file:r:x.py", "verdict": "accepted", "why": "spec"},
    ]}
    finding = {"signature": "god-file:r:x.py", "explainer": "god-file",
               "repo": "r"}
    assert brain._structure_verdict_for(finding, ledger)["why"] == "spec"


def test_verdict_rule_matches_a_whole_class():
    ledger = {"entries": [{"match": {"explainer": "symbol-blindness"},
                           "verdict": "noise", "why": "structural"}]}
    finding = {"signature": "symbol-blindness:r:*",
               "explainer": "symbol-blindness", "repo": "r"}
    assert brain._structure_verdict_for(finding, ledger)["verdict"] == "noise"


def test_unjudged_finding_has_no_verdict():
    finding = {"signature": "god-file:r:y.py", "explainer": "god-file",
               "repo": "r"}
    assert brain._structure_verdict_for(finding, {"entries": []}) is None


def test_committed_ledger_holds_only_closed_set_verdicts():
    if not brain.STRUCTURE_VERDICTS.exists():
        return
    ledger = json.loads(brain.STRUCTURE_VERDICTS.read_text())
    for entry in ledger["entries"]:
        assert entry["verdict"] in brain.STRUCTURE_VERDICT_KINDS
        assert entry.get("why"), f"verdict without a reason: {entry}"
        assert entry.get("signature") or entry.get("match")


def test_committed_ledger_has_no_pending_state():
    # The invariant that keeps this a memory and not a backlog.
    if not brain.STRUCTURE_VERDICTS.exists():
        return
    ledger = json.loads(brain.STRUCTURE_VERDICTS.read_text())
    for entry in ledger["entries"]:
        assert entry["verdict"] != "pending"
        assert not set(entry) & {"pending", "status", "todo", "due", "state"}


def test_findings_exits_zero_with_or_without_configured_targets():
    result = run("structure", "findings")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_judge_rejects_a_verdict_outside_the_closed_set():
    result = run("structure", "judge", "god-file:r:x.py", "maybe",
                 "--why", "n/a")
    assert result.returncode == 1
    assert "verdict must be one of" in result.stderr


def test_status_reports_no_unjudged_count():
    # An "N unjudged" row would be the enumeration the ledger rules out.
    result = run("status")
    assert result.returncode == 0
    for line in result.stdout.splitlines():
        if line.startswith("schedule:"):
            assert "unjudged" not in line and "pending" not in line


# --- enola: the binary-backed substrate beside the structure connector ---
#
# Everything here must hold on a machine with no binary and no cluster,
# which is the condition CI runs under and the default for a fresh clone.


def test_enola_cluster_config_is_generated_from_brain_config():
    # The kernel is org-agnostic: the cluster cannot be a hand-written
    # file listing somebody's repos.
    src = (REPO / "tools" / "brain.py").read_text()
    assert "_enola_write_cluster_config" in src
    assert "brain.config.yml" in src


def test_enola_cluster_file_is_not_committed():
    # It is derived from brain.config.yml; committing it would give a
    # cloned shell another operator's absolute paths.
    assert not (REPO / "mcp-arch.yaml").exists() or \
        "mcp-arch.yaml" in (REPO / ".gitignore").read_text()


def test_enola_ops_exit_zero_without_a_binary_or_cluster():
    for op in (["enola", "diff"], ["enola", "findings"],
               ["enola", "impact", "NoSuchSymbol"],
               ["enola", "baseline", "show"], ["enola", "check"],
               ["enola", "coverage"], ["enola", "explain"],
               ["enola", "doctor"], ["enola", "history", "log"]):
        result = run(*op)
        assert result.returncode == 0, f"{op}: {result.stderr}"
        assert result.stdout.strip(), f"{op} said nothing — a silent skip"


def test_enola_check_is_reported_not_propagated():
    """`check` exits 1 on a regression; the brain must not become a gate.

    The graph is the ceiling and never the floor, so no caller may be
    able to fail on its verdict. This asserts the wrapper's exit code
    rather than the tool's, which is the whole of the guarantee.
    """
    result = run("enola", "check")
    assert result.returncode == 0, result.stderr


def test_enola_check_never_reports_a_declined_verdict_as_a_pass():
    """Exit 3 means the snapshots were not comparable — not that it passed.

    "The graph agreed" and "the graph was not asked" must never look the
    same, which is the same rule the skip lines carry everywhere else.
    """
    src = (REPO / "tools" / "brain.py").read_text()
    assert "declined — snapshots not comparable" in src
    assert "treat as NOT ASKED, never as a pass" in src


def test_enola_judge_rejects_a_verdict_outside_the_closed_set():
    result = run("enola", "judge", "sig:r:x", "maybe", "--why", "n/a")
    assert result.returncode == 1
    assert "verdict must be one of" in result.stderr


def test_enola_signature_survives_a_changing_title():
    evidence = [{"symbol": "Thing", "file": "r/app/thing.py"}]
    before = {"source": "god-class", "evidence": evidence,
              "title": "High fan-in symbol: Thing (100 dependents)"}
    after = {"source": "god-class", "evidence": evidence,
             "title": "High fan-in symbol: Thing (140 dependents)"}
    assert (brain._enola_finding_signature(before, "r")
            == brain._enola_finding_signature(after, "r"))


def test_enola_ledger_has_no_pending_state():
    if not brain.ENOLA_VERDICTS.exists():
        return
    ledger = json.loads(brain.ENOLA_VERDICTS.read_text())
    for entry in ledger["entries"]:
        assert entry["verdict"] in brain.ENOLA_VERDICT_KINDS
        assert not set(entry) & {"pending", "status", "todo", "due", "state"}


def test_both_substrates_are_documented_in_the_contract():
    agents = (REPO / "AGENTS.md").read_text().lower()
    assert "structure" in agents
    assert "enola" in agents, (
        "the graph substrate ships in brain.py but AGENTS.md never names it"
    )


def test_symbol_blindness_fires_on_the_case_it_exists_for():
    """A polyglot repo the substrate mostly cannot see past file level.

    The kernel is Python-heavy, so this explainer never fires against its
    own corpus — it was shipped untested against its actual purpose. A
    Go-dominant repo is the shape it was written for: 93% of modules get
    file-level drift only, and a findings layer that stayed silent about
    that would be reporting on 7% of a repo while implying it covered it.
    """
    facts = _facts([f"src/a{i}.go" for i in range(40)]
                   + [f"tools/b{i}.py" for i in range(3)],
                   packages={"src": 40, "tools": 3},
                   symbols={f"tools/b{i}.py": ["x", "y"] for i in range(3)})
    hits = [f for f in brain._structure_findings(facts, "polyglot")
            if f["explainer"] == "symbol-blindness"]
    assert len(hits) == 1
    assert hits[0]["confidence"] == 1.0
    assert "93%" in hits[0]["title"]


def test_symbol_blindness_stays_quiet_when_the_substrate_can_see_most_of_it():
    facts = _facts([f"m{i}.py" for i in range(9)] + ["one.go"],
                   packages={".": 10},
                   symbols={f"m{i}.py": ["x"] for i in range(9)})
    kinds = {f["explainer"] for f in brain._structure_findings(facts, "r")}
    assert "symbol-blindness" not in kinds
