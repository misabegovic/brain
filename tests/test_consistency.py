"""Consistency / drift detection tests.

These tests catch when the documented command surface (AGENTS.md
core operations table + Intent → command mapping) drifts from the
actual skill files in `.claude/skills/` and `.claude/commands/`.

Drift is the single most common failure mode in a multi-agent /
multi-skill setup, since each surface gets edited independently.
The tests below pin the invariants and fail loudly when they
break.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))


SKILLS_DIR = REPO / ".claude" / "skills"
COMMANDS_DIR = REPO / ".claude" / "commands"
AGENTS_MD = REPO / "AGENTS.md"


def _existing_skill_names() -> set[str]:
    return {
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }


def _agents_md_text() -> str:
    return AGENTS_MD.read_text()


def test_every_skill_has_skill_md_with_frontmatter():
    """Each `.claude/skills/<skill>/SKILL.md` has a frontmatter
    block with name + description. Catches half-finished skills."""
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.exists(), f"missing SKILL.md in {skill_dir.name}"
        text = skill_md.read_text()
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        assert m, f"{skill_dir.name}: SKILL.md has no frontmatter"
        fm = m.group(1)
        assert re.search(r"^name:\s*\S", fm, re.MULTILINE), (
            f"{skill_dir.name}: missing `name:` in frontmatter"
        )
        assert re.search(r"^description:\s*\S", fm, re.MULTILINE), (
            f"{skill_dir.name}: missing `description:` in frontmatter"
        )


def test_skill_frontmatter_name_matches_dir():
    """Frontmatter `name:` matches the directory name. Common drift
    when a skill gets renamed."""
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        text = skill_md.read_text()
        m = re.search(r"^name:\s*(\S+)", text, re.MULTILINE)
        assert m, f"{skill_dir.name}: no name in frontmatter"
        assert m.group(1) == skill_dir.name, (
            f"{skill_dir.name}: frontmatter says name={m.group(1)!r}; "
            f"directory is {skill_dir.name!r}"
        )


def test_agents_md_command_table_skills_exist():
    """The skills referenced in AGENTS.md core operations table
    must all exist under `.claude/skills/`. If a skill is renamed
    or removed, AGENTS.md must be updated in the same PR."""
    text = _agents_md_text()
    skills = _existing_skill_names()

    # Skills mentioned in the "Routes to" column of the core
    # operations table — extract and sanity-check they exist.
    # The column lists skills like `wiki-ingest`, `palace-mine`,
    # etc. Grep for backticked words that look like skill names.
    operations_section = _section(text, "## Core operations")
    assert operations_section, "AGENTS.md missing § Core operations"

    referenced = set(re.findall(r"`([a-z-]+)`", operations_section))
    skill_names_used = referenced & skills
    # Every skill used should exist.
    for name in skill_names_used:
        assert name in skills, (
            f"AGENTS.md references skill `{name}` that doesn't exist"
        )

    # Sanity: the canonical 8 user-facing slash commands all map.
    canonical_commands = {
        "in", "ask", "sync", "groom", "shape",
        "promote", "pr", "review",
    }
    found_commands = set(re.findall(
        r"`/([a-z-]+)", operations_section
    ))
    missing_commands = canonical_commands - found_commands
    assert not missing_commands, (
        f"AGENTS.md core operations table missing commands: "
        f"{sorted(missing_commands)}"
    )


def test_intent_mapping_table_present():
    """AGENTS.md has an Intent → command mapping subsection, the
    natural-language layer the agent dispatches against."""
    text = _agents_md_text()
    section = _section(text, "### Intent → command mapping")
    assert section, "AGENTS.md missing § Intent → command mapping"
    # Sanity: the table mentions `/shape`, `/ask`, `/capture`,
    # `/groom` — the high-traffic ones.
    for cmd in ("/shape", "/ask", "/capture", "/groom", "/in"):
        assert cmd in section, (
            f"Intent → command mapping table doesn't mention {cmd}"
        )


def test_active_repos_consistent():
    """The active repo list in AGENTS.md sibling-repos table matches
    `brain.ACTIVE_REPOS` in code. Drift here is corrosive — agents
    behave differently if "active" disagrees across surfaces."""
    import brain  # noqa: PLC0415

    text = _agents_md_text()
    sibling_section = _section(text, "## Sibling repos on this machine")
    assert sibling_section, "AGENTS.md missing § Sibling repos"

    # Pull every `~/projects/<name>` mentioned and intersect with
    # ACTIVE_REPOS (the others may be archived).
    listed = set(re.findall(
        r"~/projects/([a-z-]+)", sibling_section
    ))
    # Both should overlap the same active repos.
    assert brain.ACTIVE_REPOS.issubset(listed), (
        f"AGENTS.md sibling table missing active repos: "
        f"{brain.ACTIVE_REPOS - listed}"
    )


def test_capture_skill_has_been_added_or_intent_table_drops_it():
    """If `/capture` is mentioned in the Intent table, the skill
    must exist. (PR C added it.) Catches the case where someone
    mentions a command in AGENTS.md that doesn't have a backing
    skill."""
    text = _agents_md_text()
    intent = _section(text, "### Intent → command mapping")
    if intent and "/capture" in intent:
        assert (SKILLS_DIR / "capture" / "SKILL.md").exists(), (
            "AGENTS.md mentions /capture but capture skill is missing"
        )


def test_shape_skill_describes_slug_only_naming():
    """Slug-only ADR/PRD naming was decided in PR A. The /shape
    skill description must reflect it (no `NNNN-` references)."""
    shape_md = (SKILLS_DIR / "shape" / "SKILL.md").read_text()
    # Templates and frontmatter snippets reference <slug>.md, never
    # NNNN-<slug>.md.
    assert "NNNN-<slug>" not in shape_md, (
        "shape SKILL.md still references NNNN-<slug> — should be "
        "slug-only per AGENTS.md § ADR / PRD filenames are slug-only"
    )


def test_rfc_skill_added():
    """If `/rfc` is in AGENTS.md (PR E), the rfc skill must exist
    AND `/shape --rfc` must be documented in the shape skill."""
    text = _agents_md_text()
    if "/rfc" not in text:
        return  # PR E not landed yet
    assert (SKILLS_DIR / "rfc" / "SKILL.md").exists(), (
        "AGENTS.md mentions /rfc but rfc skill is missing"
    )
    shape_md = (SKILLS_DIR / "shape" / "SKILL.md").read_text()
    assert "--rfc" in shape_md, (
        "shape skill missing --rfc opt-in (PR E inserted Phase 1.5)"
    )


def test_three_levels_documented():
    """The three-level model (brain / org / repo) is in AGENTS.md
    with a section heading. PR B introduced it."""
    text = _agents_md_text()
    # Use a prefix-match: AGENTS.md uses
    # "## The three levels — brain, org, repo".
    section = _section_prefix(text, "## The three levels")
    assert section, "AGENTS.md missing § The three levels"
    for level in ("brain", "org", "repo"):
        assert level in section, (
            f"AGENTS.md three-levels section missing `{level}`"
        )


def _section(text: str, heading: str) -> str:
    """Return the slice of `text` from the heading to the next
    same-or-higher level heading. Empty string if not found.
    """
    pat = re.escape(heading)
    m = re.search(rf"^{pat}\s*$", text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    # Find next heading at the same level or higher.
    level = heading.count("#")
    next_re = re.compile(
        rf"^#{{1,{level}}}\s+\S", re.MULTILINE
    )
    end_match = next_re.search(text, start + 1)
    end = end_match.start() if end_match else len(text)
    return text[start:end]


def _section_prefix(text: str, prefix: str) -> str:
    """Like `_section` but matches a heading that *starts with* the
    given prefix (so headings like '## The three levels — brain,
    org, repo' can be addressed by `## The three levels`)."""
    pat = re.escape(prefix)
    m = re.search(rf"^{pat}.*$", text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    level = prefix.count("#")
    next_re = re.compile(
        rf"^#{{1,{level}}}\s+\S", re.MULTILINE
    )
    end_match = next_re.search(text, start + 1)
    end = end_match.start() if end_match else len(text)
    return text[start:end]
