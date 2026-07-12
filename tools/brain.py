#!/usr/bin/env python3
"""brain — small CLI for keeping the brain wiki coherent at scale.

Subcommands:
  validate    — check frontmatter conformance across all wiki pages
  check       — verify every wiki page's `sources:` citations resolve
                (file paths exist, URLs return 2xx). --no-net skips URL
                checks.
  stats       — counts by kind / status / team / repo / confidence;
                orphans; stale pages
  views       — emit auto-generated index pages under wiki/_views/
                (also computes consumed_by reverse edges and token
                counts in pages.json)
  coverage    — for a sibling repo, show top-level dirs covered vs not
                by pages claiming that repo
  serve       — read-only HTTP API over the brain (pages, views,
                search proxy to mempalace). localhost only.
  promote     — scaffold an initiative page from an insight; set
                supersedes / superseded_by both ways.
  cluster     — TF-IDF + HDBSCAN clustering across wiki bodies.
  check-home-fresh — CI guard: any wiki/ edit on the current branch
                must be paired with a wiki/index.md edit (the home
                page dashboard). See wiki/brain/adrs/home-content-shape.md.
  sync-cursor — get/set/diff per-sibling-repo sync cursors at
                wiki/_state/sync-cursors.json. wiki-ingest consults
                these to do incremental ingests instead of re-walking
                whole sibling trees on every pass.

Run with the mempalace venv:
  ~/.local/share/mempalace-venv/bin/python3 tools/brain.py <cmd>
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

# Locate the brain repo root. Default: the parent of tools/ relative to
# this script. `$BRAIN_DIR` overrides — set it when running tools/brain.py
# against a brain shell scaffolded by `brain.py init` at a different
# location (per the extractable-brain-shell PRD).
REPO = Path(
    os.environ.get("BRAIN_DIR")
    or Path(__file__).resolve().parent.parent
).resolve()
WIKI = REPO / "wiki"
INDEX = WIKI / "index.md"
TEMPLATES = REPO / "tools" / "templates"
PROJECTS = Path(
    os.environ.get("BRAIN_PROJECTS_ROOT", str(Path.home() / "projects"))
).expanduser()
SYNC_CURSORS = WIKI / "_state" / "sync-cursors.json"
EFFORTS_DIR = WIKI / "_state" / "efforts"
INBOX_DIR = WIKI / "_state" / "inbox"
SUMMARY_EXPECTED_KINDS = {"pitch", "initiative", "decision", "epic",
                          "topic", "insight", "idea"}
ATTENTION_VERDICTS = ("needs-operator", "fyi", "routine")
ATTENTION_GRADES_PATH = WIKI / "_state" / "attention-grades.json"


def _local_first(env_path) -> bool:
    """True only when .env declares LOCAL_FIRST=true on its own line.

    Anchored to match AGENTS.md's canonical test
    (`grep -q '^LOCAL_FIRST=true$'`) — a substring scan also matches
    the commented boilerplate in .env.example, which made doctor and
    /dash report local-first after the operator removed the flag
    (found by the Viktor daily-operator playthrough, 2026-07-12).
    """
    try:
        for line in env_path.read_text().splitlines():
            if line.strip() == "LOCAL_FIRST=true":
                return True
    except OSError:
        pass
    return False


def today_utc() -> dt.date:
    """Today's date in UTC.

    Used everywhere `views`, `validate`, and `cmd_*` need a "today"
    so the result is invariant across local timezones — otherwise
    the CI runner (UTC) and a developer's machine (e.g. CEST) can
    write different dates into auto-generated `wiki/_views/*` files,
    failing the "views are up to date" gate.
    """
    return dt.datetime.now(dt.timezone.utc).date()

VALID_KINDS = {
    "reference", "initiative", "decision", "entity", "meta", "overlap",
    "insight", "epic", "idea", "pitch", "topic",
}
# `draft | living | superseded | archived` is the brain's general
# lifecycle. `proposed | accepted | deprecated` is Nygard's canonical
# ADR lifecycle, accepted alongside for `kind: decision`. `suggested`
# is the AI-suggestion shape (used with `ai_suggestion: true`) and
# graduates to `accepted` when a human approves.
VALID_STATUSES = {
    "draft", "living", "superseded", "archived",
    "proposed", "accepted", "deprecated", "suggested",
}
VALID_CONFIDENCES = {"high", "medium", "low"}
REQUIRED_FIELDS = {"title", "kind", "status", "updated", "sources"}

# Names valid in `repos:` and `affects:` lists. `brain` and `org` are
# meta levels (the brain itself / the organisation as a whole), used
# by org-level pages and brain self-tracking. The per-organisation
# repo registry lives in `brain.config.yml` at the repo root so the
# kernel stays content-agnostic; an absent or empty config means no
# sibling repos are registered yet.


def _load_repo_config(config_path: Path | None = None) -> tuple[set, set]:
    if config_path is None:
        config_path = REPO / "brain.config.yml"
    if not config_path.exists():
        return set(), set()
    try:
        config = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError:
        return set(), set()
    return (set(config.get("active_repos") or []),
            set(config.get("archived_repos") or []))


ACTIVE_REPOS, ARCHIVED_REPOS = _load_repo_config()
META_LEVELS = {"brain", "org"}
VALID_REPOS = ACTIVE_REPOS | ARCHIVED_REPOS | META_LEVELS

# Each list is the *minimum* set of `## ` headings the validator
# requires. For `kind: decision`, two valid section sets coexist —
# the brain's legacy What/Why/How/Alternatives/Consequences and
# Nygard's canonical Context/Alternatives/Consequences (the "Decision"
# is implicit in the page title under MADR conventions). The
# validator accepts either; new ADRs should follow the Nygard set
# per `tools/templates/adr.md`.
REQUIRED_SECTIONS_BY_KIND = {
    "overlap": ["Items", "Overlap", "Recommendation"],
    "insight": ["Pattern", "Evidence", "Affected personas", "Implications",
                "Status"],
    "epic": ["Objective", "Background", "Affected personas", "Scope",
             "No-gos", "Children", "Success metrics"],
    # `kind: pitch` — pre-bet Shape Up pitch. Per
    # `wiki/brain/adrs/shape-up-pitches.md`.
    "pitch": ["Problem", "Appetite", "Solution", "Rabbit holes", "No-gos"],
    # `kind: idea` — raw scratchpad / "potentially useful" content
    # distinct from the formal AI-suggestion ADR/PRD pipeline. Per
    # `wiki/brain/ai-suggestions/adrs/ideas-vs-suggestions-vs-permanent-separation.md`.
    "idea": ["What", "Why interesting", "Maturity"],
    # `kind: topic` — a running discussion thread on one question,
    # below the ADR ceremony threshold. Provenance-over-diffs (per
    # the Fowler ingest): the discussion trail IS the record; the
    # Outcome section links the decision it graduates into.
    "topic": ["Question", "Discussion", "Outcome"],
}
DECISION_SECTION_SETS = [
    # Legacy (pre-2026-05-03 templates).
    ["What", "Why", "How", "Alternatives", "Consequences"],
    # Nygard / MADR / AWS prescriptive guidance — the research-grounded
    # canonical shape, used by `tools/templates/adr.md` from 2026-05-03.
    ["Context", "Alternatives", "Consequences"],
    # AI-suggestion variant — `tools/templates/adr-ai-suggestion.md`.
    ["Context", "Inferred decision", "Considered options (agent surfacing)",
     "Inferred consequences"],
]
# `kind: initiative` accepts any of three valid section shapes
# (legacy / new PRD / AI-suggestion PRD). Validation passes if any
# of the listed shapes is fully present.
INITIATIVE_SECTION_SETS = [
    # Legacy What/How/Why/Now/Perceived/Target (pre-2026-05-03).
    ["What", "How", "Why", "Now", "Perceived", "Target"],
    # 2026-05-03 PRD template — Aha! / ProductPlan-grounded sections.
    ["Objective", "Background", "Affected personas", "Scope",
     "No-gos", "Rabbit holes", "Appetite", "Decision needed"],
    # AI-suggestion PRD variant — `tools/templates/prd-ai-suggestion.md`.
    ["Why the agent suggests this", "Inferred objective",
     "Affected personas (agent-inferred)", "Scope (suggested)",
     "Suggested next step"],
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# The brain UI's home page (wiki/index.md) is an agent-maintained
# dashboard with a fixed section list — the agents' contract per
# wiki/brain/adrs/home-content-shape.md. Section anchor + name +
# owning skill are constants; `empty` is computed per call by
# parsing the home file. Adding a section here is a deliberate
# schema change (PRD-level decision).
HOME_SECTIONS = [
    {"anchor": "what-changed",        "name": "What changed",        "maintained_by": "/in"},
    {"anchor": "drift-surface",       "name": "Drift surface",       "maintained_by": "/groom"},
    {"anchor": "open-initiatives",    "name": "Open initiatives",    "maintained_by": "/shape"},
    {"anchor": "recent-decisions",    "name": "Recent decisions",    "maintained_by": "/shape"},
    {"anchor": "insights-now",        "name": "Insights now",        "maintained_by": "/feedback"},
    {"anchor": "brain-trajectory",    "name": "Brain trajectory",    "maintained_by": "/sync"},
    {"anchor": "curated-picks",       "name": "Curated picks",       "maintained_by": "/in"},
    {"anchor": "where-to-find-things", "name": "Where to find things", "maintained_by": "/in"},
]


def home_sections_state() -> list[dict]:
    """Read wiki/index.md and return per-section metadata for pages.json.

    Each entry: {anchor, name, maintained_by, empty}. `empty` is True
    when the section's body contains the empty marker
    `<!-- home-section: empty ... -->` or when the section heading
    is absent.

    See wiki/brain/adrs/home-content-shape.md § How for the
    convention.
    """
    out: list[dict] = []
    if not INDEX.exists():
        for s in HOME_SECTIONS:
            out.append({**s, "empty": True})
        return out
    text = INDEX.read_text()
    for s in HOME_SECTIONS:
        heading = re.compile(r"^## " + re.escape(s["name"]) + r"\s*$", re.MULTILINE)
        m = heading.search(text)
        if not m:
            out.append({**s, "empty": True})
            continue
        rest = text[m.end():]
        next_h = re.search(r"^## ", rest, re.MULTILINE)
        body = rest[:next_h.start()] if next_h else rest
        empty = "<!-- home-section: empty" in body
        out.append({**s, "empty": empty})
    return out

REPO_SKIP_DIRS = {
    ".git", "node_modules", "vendor", "tmp", "log", "coverage",
    ".bundle", ".cache", "dist", "build", "target", "__pycache__",
}


def wiki_pages() -> list[Path]:
    """All wiki pages except index.md and anything under wiki/_*/."""
    out = []
    for p in WIKI.rglob("*.md"):
        rel = p.relative_to(WIKI)
        if rel == Path("index.md"):
            continue
        if any(part.startswith("_") for part in rel.parts):
            continue
        out.append(p)
    return sorted(out)


def parse(path: Path) -> tuple[dict, str] | None:
    text = path.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None
    return meta, m.group(2)


def index_links() -> set[str]:
    """Return set of hrefs (wiki-relative) referenced from any index.md.

    Walks `wiki/index.md` plus every nested `wiki/<dir>/index.md`
    (excluding `wiki/_*/`). Per-repo nested structure — where a repo's
    ADRs and PRDs are listed in `wiki/<repo>/index.md` rather than the
    top-level index — should not produce orphans.
    """
    out: set[str] = set()
    for index_file in WIKI.rglob("index.md"):
        rel = index_file.relative_to(WIKI)
        if any(part.startswith("_") for part in rel.parts):
            continue
        text = index_file.read_text()
        index_dir = index_file.parent
        for href in re.findall(r"\]\(([^)]+\.md)\)", text):
            target = (index_dir / href).resolve()
            try:
                rel_target = target.relative_to(WIKI)
                out.add(str(rel_target))
            except ValueError:
                continue
    return out


_TIKTOKEN_ENC = None


def approx_tokens(body: str) -> int:
    """Token count via tiktoken cl100k_base when available; chars/4 fallback.

    cl100k_base is OpenAI's tokenizer; close enough to Anthropic's for
    load-planning heuristics. Falling back to chars/4 keeps the function
    cheap and pure when the dep is missing.
    """
    global _TIKTOKEN_ENC
    if _TIKTOKEN_ENC is None:
        try:
            import tiktoken  # type: ignore
            _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _TIKTOKEN_ENC = False  # sentinel: missing
    if _TIKTOKEN_ENC:
        return len(_TIKTOKEN_ENC.encode(body))
    return max(1, len(body) // 4)


def cmd_validate(_args) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    pages = wiki_pages()
    on_disk = {str(p.relative_to(WIKI)) for p in pages}

    for p in pages:
        rel = p.relative_to(REPO)
        parsed = parse(p)
        if parsed is None:
            errors.append(f"{rel}: missing or unparseable frontmatter")
            continue
        meta, body = parsed

        missing = REQUIRED_FIELDS - set(meta or {})
        if missing:
            errors.append(f"{rel}: missing fields: {sorted(missing)}")

        kind = meta.get("kind")
        if kind not in VALID_KINDS:
            errors.append(f"{rel}: invalid kind {kind!r}")

        status = meta.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{rel}: invalid status {status!r}")

        conf = meta.get("confidence")
        if conf is not None and conf not in VALID_CONFIDENCES:
            errors.append(f"{rel}: invalid confidence {conf!r}")

        upd = meta.get("updated")
        if isinstance(upd, str):
            try:
                dt.date.fromisoformat(upd)
            except ValueError:
                errors.append(f"{rel}: updated is not ISO date: {upd!r}")
        elif not isinstance(upd, dt.date):
            errors.append(f"{rel}: updated is not a date: {upd!r}")

        srcs = meta.get("sources") or []
        if status != "draft" and not srcs:
            errors.append(f"{rel}: non-draft page has empty sources")

        summary = meta.get("summary")
        if summary is not None:
            if not isinstance(summary, str) or not summary.strip():
                errors.append(f"{rel}: summary must be a non-empty string")
            elif len(summary) > 600:
                errors.append(f"{rel}: summary too long "
                              f"({len(summary)} chars > 600)")
        elif kind in SUMMARY_EXPECTED_KINDS and status in (
                "living", "accepted"):
            warnings.append(f"{rel}: no summary: — the briefing renders "
                            f"this kind as a card")

        for dep in meta.get("depends_on") or []:
            if dep not in on_disk:
                errors.append(f"{rel}: depends_on points at unknown page: {dep}")

        for r in meta.get("repos") or []:
            if r not in VALID_REPOS:
                errors.append(f"{rel}: repos contains unknown repo: {r}")
        for r in meta.get("affects") or []:
            if r not in VALID_REPOS:
                errors.append(f"{rel}: affects contains unknown repo: {r}")

        for field in ("supersedes", "superseded_by"):
            ref = meta.get(field)
            if ref and ref not in on_disk:
                errors.append(f"{rel}: {field} points at unknown page: {ref}")

        rel_to_wiki = p.relative_to(WIKI)
        parts = rel_to_wiki.parts
        if kind == "epic":
            if len(parts) >= 3 and parts[1] == "epics":
                scope = parts[0]
                slug_with_ext = parts[-1]
                expected_adr = f"{scope}/adrs/{slug_with_ext}"
                if expected_adr in on_disk:
                    errors.append(
                        f"{rel}: kind=epic must not have a matching ADR "
                        f"at wiki/{expected_adr} — epics have no umbrella "
                        f"ADR pair (decisions live in children)"
                    )
            else:
                errors.append(
                    f"{rel}: kind=epic must live at "
                    f"wiki/<scope>/epics/<slug>.md"
                )

        parent_epic = meta.get("parent_epic")
        if parent_epic and parts:
            scope = parts[0]
            expected = f"{scope}/epics/{parent_epic}.md"
            if expected not in on_disk:
                errors.append(
                    f"{rel}: parent_epic={parent_epic!r} does not resolve "
                    f"— expected wiki/{expected} to exist"
                )

        present = set(HEADING_RE.findall(body))
        if kind == "decision":
            # `kind: decision` accepts any of several section shapes
            # (legacy / Nygard / AI-suggestion). Validation passes if
            # *any* of the listed shapes is fully present.
            if not any(all(s in present for s in shape)
                       for shape in DECISION_SECTION_SETS):
                errors.append(
                    f"{rel}: kind=decision missing required sections; "
                    f"need one of {DECISION_SECTION_SETS}"
                )
        elif kind == "initiative":
            # Same shape-flexibility for `kind: initiative` —
            # legacy / new PRD / AI-suggestion variants all valid.
            if not any(all(s in present for s in shape)
                       for shape in INITIATIVE_SECTION_SETS):
                errors.append(
                    f"{rel}: kind=initiative missing required sections; "
                    f"need one of {INITIATIVE_SECTION_SETS}"
                )
        else:
            required_sections = REQUIRED_SECTIONS_BY_KIND.get(kind, [])
            if required_sections:
                missing_sections = [s for s in required_sections
                                    if s not in present]
                if missing_sections:
                    errors.append(
                        f"{rel}: kind={kind} missing required sections: "
                        f"{missing_sections}"
                    )

    indexed = index_links()
    orphan = sorted(on_disk - indexed)
    if orphan:
        for o in orphan:
            errors.append(f"orphan (not in index.md): wiki/{o}")
    dead = sorted(indexed - on_disk)
    for d in dead:
        if not (WIKI / d).exists():
            errors.append(f"dead index link: wiki/{d}")

    if errors:
        for e in errors:
            print(f"ERROR  {e}")
        print(f"\n{len(errors)} error(s) across {len(pages)} page(s)")
        return 1

    for w in warnings:
        print(f"warn  {w}")
    print(f"OK  {len(pages)} page(s) valid")
    return 0


def _classify_source(src: str) -> str:
    if src.startswith(("http://", "https://")):
        return "url"
    if src.startswith("~"):
        return "home-path"
    if src.startswith("/"):
        return "abs-path"
    if src.startswith(("sources/", "tools/", "wiki/", "log/", ".claude/",
                       "../")):
        return "repo-path"
    return "unknown"


def _check_path(p: str, page: Path | None = None) -> tuple[str, str]:
    """Resolve a cited path. Returns (status, detail) where status is
    one of 'ok' / 'broken' / 'skipped'. 'skipped' is used when the path
    points into a sibling repo that doesn't exist on this machine (e.g.
    the CI runner does not have the sibling checkout) — that's not a
    broken citation, just unverifiable here.
    """
    candidate = Path(os.path.expanduser(p))

    # Legacy-path remap: brain pages were authored assuming
    # `~/projects/<repo>/...` but the operator may have configured
    # `$BRAIN_PROJECTS_ROOT` to point elsewhere (e.g. `~/work/`).
    # If the literal path doesn't exist but `PROJECTS/<repo>/<rest>`
    # does, prefer that. Mirrors the per-skill sibling-repo handling.
    if candidate.is_absolute() and not candidate.exists():
        try:
            home_projects = Path(os.path.expanduser("~/projects"))
            rel = candidate.relative_to(home_projects)
            if rel.parts and PROJECTS != home_projects:
                remapped = PROJECTS / rel
                if remapped.exists():
                    return "ok", str(remapped)
        except ValueError:
            pass

    # Detect "sibling repo not on this machine" — a path under the
    # configured PROJECTS root where <repo> doesn't exist locally.
    if candidate.is_absolute():
        try:
            rel_to_projects = candidate.relative_to(PROJECTS)
            if rel_to_projects.parts:
                sibling = PROJECTS / rel_to_projects.parts[0]
                if not sibling.exists():
                    return "skipped", (
                        f"sibling repo not on this machine: {sibling}"
                    )
        except ValueError:
            pass
        # Also check legacy ~/projects/ root for the skip-when-absent
        try:
            home_projects = Path(os.path.expanduser("~/projects"))
            rel_to_home = candidate.relative_to(home_projects)
            if rel_to_home.parts:
                # Sibling not at PROJECTS root → skip rather than fail
                sibling_at_projects = PROJECTS / rel_to_home.parts[0]
                if not sibling_at_projects.exists():
                    return "skipped", (
                        f"sibling repo not on this machine: {sibling_at_projects}"
                    )
        except ValueError:
            pass

    if candidate.is_absolute() and candidate.exists():
        return "ok", str(candidate)
    if page is not None and not candidate.is_absolute():
        page_rel = (page.parent / candidate).resolve()
        if page_rel.exists():
            return "ok", str(page_rel)
    repo_rel = (REPO / candidate).resolve()
    if repo_rel.exists():
        return "ok", str(repo_rel)
    return "broken", f"missing: {repo_rel}"


def _check_url(url: str, timeout: int = 6) -> tuple[bool, str]:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "brain-check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 400:
                return True, str(resp.status)
            return False, str(resp.status)
    except urllib.error.HTTPError as e:
        if e.code in (403, 405, 501):
            try:
                req2 = urllib.request.Request(url, headers={
                    "User-Agent": "brain-check",
                    "Range": "bytes=0-0",
                })
                with urllib.request.urlopen(req2, timeout=timeout) as resp2:
                    return (200 <= resp2.status < 400), str(resp2.status)
            except Exception as e2:
                return False, f"GET failed: {e2}"
        return False, f"{e.code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def cmd_check(args) -> int:
    """Verify every wiki page's sources: frontmatter resolves."""
    pages = wiki_pages()
    if args.page:
        target = WIKI / args.page
        if not target.exists():
            print(f"page not found: {target}")
            return 2
        pages = [target]

    broken: list[tuple[Path, str, str, str]] = []
    suspicious: list[tuple[Path, str]] = []
    skipped: list[tuple[Path, str, str]] = []
    checked = 0

    for p in pages:
        parsed = parse(p)
        if parsed is None:
            continue
        meta, _ = parsed
        for src in (meta.get("sources") or []):
            if not isinstance(src, str):
                continue
            checked += 1
            kind = _classify_source(src)
            if kind == "url":
                if args.no_net:
                    continue
                ok, reason = _check_url(src)
                if not ok:
                    broken.append((p, src, kind, reason))
            elif kind in ("home-path", "abs-path", "repo-path"):
                status, detail = _check_path(src, page=p)
                if status == "broken":
                    broken.append((p, src, kind, detail))
                elif status == "skipped":
                    skipped.append((p, src, detail))
            else:
                suspicious.append((p, src))

    if broken:
        print(f"BROKEN ({len(broken)}):")
        for page, src, kind, reason in broken:
            print(f"  {page.relative_to(REPO)}")
            print(f"    {kind}: {src}  →  {reason}")
    if suspicious:
        print(f"\nSUSPICIOUS ({len(suspicious)}):")
        for page, src in suspicious:
            print(f"  {page.relative_to(REPO)}: {src}")
    if skipped and args.verbose:
        print(f"\nSKIPPED ({len(skipped)}, sibling repos not on this machine):")
        for page, src, _ in skipped:
            print(f"  {page.relative_to(REPO)}: {src}")

    print(f"\n{checked} sources checked across {len(pages)} pages")
    if broken:
        print(f"  {len(broken)} broken")
    if suspicious:
        print(f"  {len(suspicious)} suspicious (couldn't classify)")
    if skipped:
        print(f"  {len(skipped)} skipped (sibling repos not on this machine; "
              f"use --verbose to list)")

    return 1 if broken else 0


def cmd_stats(_args) -> int:
    pages = wiki_pages()
    by_kind: dict[str, int] = collections.Counter()
    by_status: dict[str, int] = collections.Counter()
    by_conf: dict[str, int] = collections.Counter()
    by_team: dict[str, int] = collections.Counter()
    by_repo: dict[str, int] = collections.Counter()
    stale: list[tuple[Path, int]] = []
    today = today_utc()

    for p in pages:
        parsed = parse(p)
        if parsed is None:
            continue
        meta, _ = parsed
        by_kind[meta.get("kind", "?")] += 1
        by_status[meta.get("status", "?")] += 1
        by_conf[meta.get("confidence", "?")] += 1
        if t := meta.get("team"):
            by_team[t] += 1
        for r in meta.get("repos") or []:
            by_repo[r] += 1
        upd = meta.get("updated")
        if isinstance(upd, str):
            try:
                upd = dt.date.fromisoformat(upd)
            except ValueError:
                continue
        if isinstance(upd, dt.date):
            age = (today - upd).days
            if age > 90:
                stale.append((p, age))

    def show(label: str, counter):
        print(f"\n{label}:")
        for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {k:<14} {v}")

    print(f"pages: {len(pages)}")
    show("by kind", by_kind)
    show("by status", by_status)
    show("by confidence", by_conf)
    if by_team:
        show("by team", by_team)
    if by_repo:
        show("by repo", by_repo)

    indexed = index_links()
    on_disk = {str(p.relative_to(WIKI)) for p in pages}
    orphan = sorted(on_disk - indexed)
    if orphan:
        print("\norphans (not in index.md):")
        for o in orphan:
            print(f"  wiki/{o}")
    if stale:
        print(f"\nstale (>90 days): {len(stale)}")
        for p, age in sorted(stale, key=lambda x: -x[1]):
            print(f"  {p.relative_to(REPO)}  ({age} days)")
    return 0


def collect_pages_data() -> list[dict]:
    """Build the structured per-page list used by views and serve."""
    pages = wiki_pages()
    out = []
    for p in pages:
        parsed = parse(p)
        if parsed is None:
            continue
        meta, body = parsed
        entry = {"path": str(p.relative_to(WIKI)), **meta}
        u = entry.get("updated")
        if isinstance(u, dt.date):
            entry["updated"] = u.isoformat()
        entry["tokens"] = approx_tokens(body)
        out.append(entry)

    # Compute reverse edges for depends_on → consumed_by.
    consumed_by: dict[str, list[str]] = collections.defaultdict(list)
    for entry in out:
        for dep in entry.get("depends_on") or []:
            consumed_by[dep].append(entry["path"])
    for entry in out:
        rev = sorted(consumed_by.get(entry["path"], []))
        if rev:
            entry["consumed_by"] = rev

    # Compute reverse edges for affects → affected_by.
    # `affects:` is a list of repo names. For each page X with
    # affects=[r1, r2, ...], the repo's index page (`<r>/index.md`)
    # gets X listed under `affected_by:`. This surfaces cross-level
    # propagation from the repo side.
    by_repo_affected: dict[str, list[str]] = collections.defaultdict(list)
    for entry in out:
        for r in entry.get("affects") or []:
            by_repo_affected[r].append(entry["path"])
    for entry in out:
        path = entry["path"]
        # Only repo index pages collect affected_by.
        # Match `<repo>/index.md` exactly (no nested folders).
        parts = path.split("/")
        if len(parts) == 2 and parts[1] == "index.md":
            repo = parts[0]
            affecting = sorted(
                p for p in by_repo_affected.get(repo, []) if p != path
            )
            if affecting:
                entry["affected_by"] = affecting

    # Compute reverse edges for parent_epic → child_prds + child_adrs.
    # parent_epic: <slug> on a page (PRD or ADR) names the epic this
    # work belongs to. The epic page (kind: epic) collects child_prds
    # and child_adrs separately, so readers can see PRD vs ADR
    # membership at a glance without filtering by kind.
    epic_children_prds: dict[str, list[str]] = collections.defaultdict(list)
    epic_children_adrs: dict[str, list[str]] = collections.defaultdict(list)
    for entry in out:
        parent = entry.get("parent_epic")
        if not parent:
            continue
        path = entry["path"]
        path_parts = path.split("/")
        if not path_parts:
            continue
        scope = path_parts[0]
        epic_path = f"{scope}/epics/{parent}.md"
        if entry.get("kind") == "decision":
            epic_children_adrs[epic_path].append(path)
        else:
            epic_children_prds[epic_path].append(path)
    for entry in out:
        if entry.get("kind") != "epic":
            continue
        path = entry["path"]
        cp = sorted(epic_children_prds.get(path, []))
        ca = sorted(epic_children_adrs.get(path, []))
        if cp:
            entry["child_prds"] = cp
        if ca:
            entry["child_adrs"] = ca
    return out


def cmd_views(_args) -> int:
    views_dir = WIKI / "_views"
    views_dir.mkdir(exist_ok=True)

    entries = collect_pages_data()

    by_kind: dict[str, list[tuple[str, str, str]]] = collections.defaultdict(list)
    by_team: dict[str, list[tuple[str, str, str]]] = collections.defaultdict(list)
    by_repo: dict[str, list[tuple[str, str, str]]] = collections.defaultdict(list)

    for entry in entries:
        title = entry.get("title", entry["path"])
        status = entry.get("status", "?")
        rec = (title, entry["path"], status)
        by_kind[entry.get("kind", "?")].append(rec)
        if t := entry.get("team"):
            by_team[t].append(rec)
        for r in entry.get("repos") or []:
            by_repo[r].append(rec)

    today = today_utc().isoformat()

    def write_view(name: str, title: str, groups: dict):
        lines = [
            "---",
            f"title: {title}",
            "kind: meta",
            "status: living",
            f"updated: {today}",
            "confidence: high",
            "sources:",
            "  - tools/brain.py",
            "---",
            "",
            f"# {title}",
            "",
            "Auto-generated by `python tools/brain.py views`. Do not edit "
            "by hand.",
            "",
        ]
        for key in sorted(groups):
            lines.append(f"## {key}")
            lines.append("")
            for ttl, rel, status in sorted(groups[key]):
                lines.append(f"- [{ttl}](../{rel}) — *{status}*")
            lines.append("")
        (views_dir / name).write_text("\n".join(lines))

    write_view("by-kind.md", "Index — by kind", by_kind)
    write_view("by-team.md", "Index — by team", by_team)
    write_view("by-repo.md", "Index — by repo", by_repo)
    write_ai_suggestions_view(views_dir, entries, today)
    write_by_epic_view(views_dir, entries, today)

    json_out = {
        "generated": today,
        "home_sections": home_sections_state(),
        "pages": entries,
    }
    (views_dir / "pages.json").write_text(json.dumps(json_out, indent=2))

    print(f"wrote {views_dir.relative_to(REPO)}/by-kind.md, by-team.md, "
          f"by-repo.md, by-epic.md, ai-suggestions.md, pages.json")
    print(f"  {len(entries)} pages indexed; "
          f"{sum(1 for e in entries if 'consumed_by' in e)} carry "
          f"computed consumed_by edges; "
          f"{sum(1 for e in entries if 'affected_by' in e)} repos "
          f"carry computed affected_by edges; "
          f"{sum(1 for e in entries if e.get('ai_suggestion'))} "
          f"AI-suggestion drafts cataloged")

    # Derived index + custom views ride the same regeneration, per
    # the sql-views-over-derived-index ADR.
    stats = _build_index()
    custom = _render_custom_views()
    print(f"  index: {stats['pages']} pages + {stats['snapshots']} "
          f"snapshots ({stats['size_kb']} KB)"
          + (f"; custom views: {', '.join(custom)}" if custom else ""))
    return 0


def scope_for_path(path: str) -> tuple[str, str]:
    """Return (scope_label, scope_slug) for a wiki-relative path.

    `scope_slug` matches a directory name under `wiki/`:
    - "brain" for `brain/...`
    - "org" for `org/...`
    - "<repo>" for any active or archived repo (e.g. "api",
      "app")
    - "(other)" for paths that don't fit (e.g. wiki-root pages)

    `scope_label` is the human-friendly version with parenthetical
    qualifier — "api (per-repo)", "org (cross-organisation)",
    "brain (meta)", "(other)".
    """
    parts = path.split("/")
    if len(parts) < 2:
        return ("(other)", "(other)")
    head = parts[0]
    if head == "brain":
        return ("brain (meta)", "brain")
    if head == "org":
        return ("org (cross-organisation)", "org")
    if head in VALID_REPOS - META_LEVELS:
        return (f"{head} (per-repo)", head)
    return ("(other)", head)


def write_ai_suggestions_view(views_dir, entries, today):
    """Emit `wiki/_views/ai-suggestions.md` cataloging every page with
    `ai_suggestion: true` across all scopes (per-repo / org / brain).

    The view is the input both to the Starlight UI surface and to
    human review — humans navigating to it should see at a glance
    which suggestions are awaiting review, grouped by scope, with
    enough context to decide whether to dig in.
    """
    suggestions = [e for e in entries if e.get("ai_suggestion")]
    by_scope: dict[str, list[dict]] = collections.defaultdict(list)
    for s in suggestions:
        label, _slug = scope_for_path(s["path"])
        by_scope[label].append(s)

    total = len(suggestions)
    scope_count = len([k for k, v in by_scope.items() if v])

    lines = [
        "---",
        "title: AI suggestions — drafts for human review",
        "kind: meta",
        "status: living",
        f"updated: {today}",
        "confidence: high",
        "sources:",
        "  - tools/brain.py",
        "---",
        "",
        "# AI suggestions — drafts for human review",
        "",
        "Auto-generated by `python tools/brain.py views`. Do not edit "
        "by hand.",
        "",
        "Aggregates every page with `ai_suggestion: true` across the "
        "brain's three scopes: per-repo, org (cross-organisation), and "
        "brain (meta). See `AGENTS.md` § Governance > "
        "`ai_suggestion` for what these are and how they graduate.",
        "",
        f"**{total}** suggestion(s) in **{scope_count}** scope(s) "
        f"awaiting human review.",
        "",
    ]

    if total == 0:
        lines.extend([
            "No AI-suggestion drafts at the moment. The brain is in "
            "a clean human-approved state.",
            "",
        ])
    else:
        # Stable scope ordering: brain → org → per-repo (alphabetical) → other.
        def scope_sort_key(label: str) -> tuple:
            if label.startswith("brain"):
                return (0, label)
            if label.startswith("org"):
                return (1, label)
            if label == "(other)":
                return (3, label)
            return (2, label)

        for scope_label in sorted(by_scope, key=scope_sort_key):
            scope_entries = by_scope[scope_label]
            adrs = [e for e in scope_entries
                    if e.get("kind") == "decision"]
            prds = [e for e in scope_entries
                    if e.get("kind") == "initiative"]
            other = [e for e in scope_entries
                     if e.get("kind") not in ("decision", "initiative")]

            lines.append(f"## {scope_label} — {len(scope_entries)} suggestion(s)")
            lines.append("")

            def emit_kind_block(kind_label: str, items: list[dict]):
                if not items:
                    return
                lines.append(f"### {kind_label}")
                lines.append("")
                for e in sorted(items, key=lambda x: x["path"]):
                    title = e.get("title", e["path"])
                    status = e.get("status", "?")
                    rel = e["path"]
                    lines.append(
                        f"- [{title}](../{rel}) — *{status}* — "
                        f"`{rel}`"
                    )
                lines.append("")

            emit_kind_block("ADRs", adrs)
            emit_kind_block("PRDs", prds)
            emit_kind_block("Other", other)

    lines.extend([
        "## How to graduate a suggestion",
        "",
        "Per `AGENTS.md` § Governance > `ai_suggestion` > Graduation, "
        "a graduation PR:",
        "",
        "1. Drops `ai_suggestion: true` from frontmatter.",
        "2. Removes the AI-suggestion banner.",
        "3. Bumps `confidence:` (typically `low` → `medium`).",
        "4. Changes `status:` from `suggested` to `accepted` (ADR) "
        "or `living` (PRD).",
        "5. Moves the file from `<scope>/ai-suggestions/{adrs,prds}/` "
        "to `<scope>/{adrs,prds}/`.",
        "6. Reshapes inference-mode language to direct-mode and "
        "fixes any factual errors the human reviewer catches.",
        "",
        "Re-scoping is allowed during graduation if the human "
        "decides the suggestion belongs at a different scope.",
        "",
    ])

    (views_dir / "ai-suggestions.md").write_text("\n".join(lines))


def write_by_epic_view(views_dir, entries, today):
    """Emit `wiki/_views/by-epic.md` listing every kind:epic page
    with its children (PRDs + ADRs split, with status inline).

    Per the multi-prd-epic-shape ADR, the view is the brain's
    aggregated index of umbrella-scale work and lets a reader
    answer "what big initiatives are in flight, and how much of
    each has shipped" at a glance. When no epics exist (the v1
    baseline), the view is written as an empty stub so the
    views-up-to-date CI gate has a stable baseline to diff
    against.
    """
    epics = [e for e in entries if e.get("kind") == "epic"]
    by_path = {e["path"]: e for e in entries}

    lines = [
        "---",
        "title: Index — by epic",
        "kind: meta",
        "status: living",
        f"updated: {today}",
        "confidence: high",
        "sources:",
        "  - tools/brain.py",
        "---",
        "",
        "# Index — by epic",
        "",
        "Auto-generated by `python tools/brain.py views`. Do not edit "
        "by hand.",
        "",
        "Aggregates every `kind: epic` umbrella with its children "
        "(`parent_epic:` reverse-edges, split into PRD and ADR "
        "membership). Per `wiki/brain/adrs/multi-prd-epic-shape.md`.",
        "",
        f"**{len(epics)}** epic(s) in flight.",
        "",
    ]

    if not epics:
        lines.extend([
            "No epics yet. The first `/shape <scope> --epic <pitch>` "
            "invocation creates the first one.",
            "",
        ])
    else:
        for epic in sorted(epics, key=lambda e: e["path"]):
            title = epic.get("title", epic["path"])
            status = epic.get("status", "?")
            rel = epic["path"]
            lines.append(f"## [{title}](../{rel}) — *{status}*")
            lines.append("")

            def emit_children(label: str, paths: list[str]):
                if not paths:
                    return
                lines.append(f"### {label}")
                lines.append("")
                for cp in sorted(paths):
                    child = by_path.get(cp, {})
                    ctitle = child.get("title", cp)
                    cstatus = child.get("status", "?")
                    lines.append(
                        f"- [{ctitle}](../{cp}) — *{cstatus}*"
                    )
                lines.append("")

            emit_children("PRDs", epic.get("child_prds") or [])
            emit_children("ADRs", epic.get("child_adrs") or [])

            if not (epic.get("child_prds") or epic.get("child_adrs")):
                lines.append("*(no children yet)*")
                lines.append("")

    (views_dir / "by-epic.md").write_text("\n".join(lines))


def cmd_coverage(args) -> int:
    repo_name = args.repo
    repo_path = PROJECTS / repo_name
    if not repo_path.exists():
        print(_missing_sibling_msg(repo_path))
        return 1

    pages = wiki_pages()
    relevant: list[tuple[Path, dict, str]] = []
    for p in pages:
        parsed = parse(p)
        if parsed is None:
            continue
        meta, body = parsed
        if repo_name in (meta.get("repos") or []):
            relevant.append((p, meta, body))

    repo_dirs = sorted(
        d.name for d in repo_path.iterdir()
        if d.is_dir() and d.name not in REPO_SKIP_DIRS
        and not d.name.startswith(".")
    )

    covered: set[str] = set()
    coverage_by_dir: dict[str, list[str]] = collections.defaultdict(list)
    for d in repo_dirs:
        for p, meta, body in relevant:
            srcs_str = " ".join(str(s) for s in (meta.get("sources") or []))
            if d in body or d in srcs_str:
                covered.add(d)
                coverage_by_dir[d].append(str(p.relative_to(REPO)))

    uncovered = [d for d in repo_dirs if d not in covered]

    print(f"coverage for {repo_name} (top-level dirs):")
    print(f"  pages claiming this repo: {len(relevant)}")
    print(f"  dirs covered: {len(covered)}/{len(repo_dirs)}")

    if covered:
        print("\ncovered:")
        for d in sorted(covered):
            pages_for_d = coverage_by_dir[d]
            print(f"  {d:<20} {pages_for_d[0]}"
                  f"{' (+' + str(len(pages_for_d)-1) + ' more)' if len(pages_for_d) > 1 else ''}")

    if uncovered:
        print("\nuncovered:")
        for d in uncovered:
            print(f"  {d}")

    return 0 if not uncovered else 2


def _render_dash(page_count: int) -> str:
    """Server-rendered ops dashboard for `serve` at /dash.

    Everything is computed per-request from live state — the page is
    the human-friendly face of `doctor` + `status` + `inbox`, so a
    non-terminal user can see whether the brain is healthy and what
    it wants tended without learning the CLI.
    """
    import html as _html

    def esc(s) -> str:
        return _html.escape(str(s))

    config_path = REPO / "brain.config.yml"
    org = ""
    try:
        org = (yaml.safe_load(config_path.read_text()) or {}).get("org") or ""
    except Exception:
        pass
    env_path = REPO / ".env"
    mode = ("local-first" if env_path.exists()
            and _local_first(env_path) else "PR-gated")

    icon = {"ok": "✓", "warn": "−", "fail": "✗"}
    check_rows = ""
    for c in _doctor_checks():
        hint = (f'<div class="hint">fix: <code>{esc(c["hint"])}</code></div>'
                if c["hint"] and c["status"] != "ok" else "")
        check_rows += (
            f'<tr class="{c["status"]}"><td>{icon[c["status"]]}</td>'
            f'<td>{esc(c["label"])}</td>'
            f'<td>{esc(c["detail"])}{hint}</td></tr>\n')

    items = _inbox_items()
    if items:
        order = {"high": 0, "normal": 1, "low": 2}
        items.sort(key=lambda i: (order.get(i.get("priority"), 1),
                                  i.get("produced_at", "")))
        inbox_rows = "".join(
            f'<tr><td><code>{esc(i["id"])}</code></td>'
            f'<td>{esc(i.get("kind", "?"))}</td>'
            f'<td>{esc(i.get("priority", "normal"))}</td>'
            f'<td>{esc(i.get("summary", ""))}</td></tr>\n'
            for i in items)
        inbox_html = (f'<table><tr><th>id</th><th>kind</th><th>priority'
                      f'</th><th>summary</th></tr>{inbox_rows}</table>'
                      f'<p>Digest in your agent session: <code>/tend</code>'
                      f' (or <code>brain tend</code> from any shell).</p>')
    else:
        inbox_html = "<p>Empty — nothing pending. The timer refills it.</p>"

    title = f"brain — {org}" if org else "brain"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · ops</title>
<style>
 :root {{ color-scheme: light dark; }}
 body {{ font: 15px/1.5 system-ui, sans-serif; max-width: 52rem;
        margin: 2rem auto; padding: 0 1rem; }}
 h1 {{ font-size: 1.3rem; }} h2 {{ font-size: 1.05rem; margin-top: 2rem; }}
 table {{ border-collapse: collapse; width: 100%; }}
 td, th {{ padding: .35rem .6rem; text-align: left; vertical-align: top;
          border-bottom: 1px solid color-mix(in srgb, currentColor 15%, transparent); }}
 tr.warn td:first-child {{ color: #c80; }} tr.fail td:first-child {{ color: #c33; }}
 tr.ok td:first-child {{ color: #2a2; }}
 code {{ background: color-mix(in srgb, currentColor 8%, transparent);
        padding: .1rem .3rem; border-radius: 3px; }}
 .hint {{ opacity: .75; font-size: .9em; }}
 .meta {{ opacity: .75; }}
</style></head><body>
<h1>{esc(title)}</h1>
<p class="meta">{page_count} pages · {mode} mode · {esc(today_utc().isoformat())}
 · <a href="/pages.json">pages.json</a> · <a href="/search?q=">search API</a></p>
<h2>Health</h2>
<table>{check_rows}</table>
<p class="meta">Same as <code>brain doctor</code>; one-command fix-up:
<code>brain setup</code>.</p>
<h2>Tend queue</h2>
{inbox_html}
<h2>Quick start</h2>
<ol>
 <li><code>python3 tools/brain.py setup</code> — configure org, repos,
     hook, timer (idempotent).</li>
 <li>Open your agent in the repo — the inbox summary greets you.</li>
 <li><code>/tend</code> to digest, <code>/in &lt;source&gt;</code> to feed,
     <code>/ask</code> to query.</li>
</ol>
</body></html>"""


def render_app_page(views: list | None = None) -> str:
    """The app shell: rendered knowledge full-width under an ambient
    strip (health + tend queue + auto-reload). The operator's harness
    runs in their own terminal beside this window."""
    view_links = "".join(
        f'<button onclick="nav(\'/_views/custom/{v}/\')">{v}</button>'
        for v in (views or []))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>brain</title>
<style>
 :root {{ color-scheme: light dark; }}
 body {{ margin: 0; font: 14px/1.45 system-ui, sans-serif;
        display: flex; flex-direction: column; height: 100vh; }}
 button {{ font: inherit; }}
 #nav {{ padding: .35rem .6rem; display: flex; gap: .4rem;
        align-items: center; border-bottom: 1px solid #8884; }}
 #nav button {{ padding: .15rem .6rem; cursor: pointer; }}
 #strip {{ margin-left: auto; opacity: .75; font-size: .85em; }}
 #page {{ flex: 1; border: 0; }}
</style></head><body>
<div id="nav">
  <button onclick="nav('/')">briefing</button>
  <button onclick="nav('/home/')">corpus</button>
  <button onclick="nav('/dash')">status</button>
  {view_links}
  <span id="strip">…</span>
</div>
<iframe id="page" src="/"></iframe>
<script>
 function nav(url) {{ document.getElementById('page').src = url; }}
 let last = 0;
 async function tick() {{
   try {{
     const r = await fetch('/workbench/status');
     const s = await r.json();
     document.getElementById('strip').textContent =
       (s.fails ? '✗ ' + s.fails + ' failing · ' :
        s.warns ? '− ' + s.warns + ' notice · ' : '✓ healthy · ')
       + (s.inbox ? s.inbox + ' to tend' : 'queue clear');
     if (last && s.mtime > last) nav(document.getElementById('page').src);
     last = s.mtime;
   }} catch (e) {{}}
 }}
 tick(); setInterval(tick, 8000);
</script></body></html>"""


def cmd_serve(args) -> int:
    """Read-only HTTP API for the brain. localhost only by default.

    Outside serving mode (BRAIN_SERVING=1) it also mounts the app
    page at /workbench — the rendered knowledge with an ambient
    health strip. No shell, no websocket: the operator's harness
    runs in their own terminal (per 
    wiki/brain/adrs/mcp-cli-surface.md).
    """
    port = args.port
    host = args.host
    workbench = os.environ.get("BRAIN_SERVING") != "1"

    rebuild_lock = threading.Lock()
    entries_cache: list[dict] = []

    def refresh_cache():
        entries_cache.clear()
        entries_cache.extend(collect_pages_data())

    refresh_cache()

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send_json(self, code: int, body) -> None:
            data = json.dumps(body, indent=2).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_text(self, code: int, body: str,
                       ctype: str = "text/markdown; charset=utf-8") -> None:
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")

        def do_GET(self):  # noqa: N802
            url = urllib.parse.urlparse(self.path)
            path = url.path.rstrip("/") or "/"
            qs = urllib.parse.parse_qs(url.query)

            if path == "/api":
                self._send_json(200, {
                    "endpoints": [
                        "/dash",
                        "/pages.json",
                        "/pages/<wiki-relative-path>",
                        "/views/by-kind",
                        "/views/by-team",
                        "/views/by-repo",
                        "/search?q=<query>",
                        "/refresh",
                    ],
                    "page_count": len(entries_cache),
                })
                return

            if path == "/dash":
                self._send_text(200, _render_dash(len(entries_cache)),
                                "text/html; charset=utf-8")
                return

            # The rendered wiki serves at ROOT as the fallback for any
            # path the JSON API doesn't own — the Astro build links
            # assets and pages absolutely (/_astro/…, /brain/…), so a
            # prefix mount breaks styling and navigation. /ui redirects
            # for the older bookmark shape. Stress-test finding,
            # 2026-07-10.
            if path == "/ui" or path.startswith("/ui/"):
                self.send_response(302)
                self.send_header("Location", path[len("/ui"):] or "/")
                self.end_headers()
                return

            def serve_static(rel_path: str) -> bool:
                site = None
                for candidate in (REPO / "ui" / ".build-cache",
                                  REPO / "ui" / "dist"):
                    if (candidate / "index.html").exists():
                        site = candidate
                        break
                if site is None:
                    return False
                rel = rel_path.lstrip("/")
                target = (site / rel).resolve() if rel else site / "index.html"
                try:
                    target.relative_to(site)
                except ValueError:
                    return False
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists() and not target.suffix:
                    target = target / "index.html"
                code = 200
                if not target.exists():
                    target = site / "404.html"
                    code = 404
                    if not target.exists():
                        return False
                ctypes = {".html": "text/html; charset=utf-8",
                          ".css": "text/css",
                          ".js": "application/javascript",
                          ".mjs": "application/javascript",
                          ".json": "application/json",
                          ".svg": "image/svg+xml", ".png": "image/png",
                          ".ico": "image/x-icon", ".woff2": "font/woff2",
                          ".txt": "text/plain"}
                data = target.read_bytes()
                self.send_response(code)
                self.send_header("Content-Type", ctypes.get(
                    target.suffix, "application/octet-stream"))
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data)
                return True


            if workbench and path.startswith("/workbench"):
                host_hdr = (self.headers.get("Host") or "").split(":")[0]
                if host_hdr not in ("localhost", "127.0.0.1", "::1", ""):
                    self._send_json(403, {"error": "host not allowed"})
                    return
                if path == "/workbench":
                    view_names = sorted(
                        s.stem for s in VIEWS_SPEC_DIR.glob("*.yml")
                    ) if VIEWS_SPEC_DIR.exists() else []
                    self._send_text(
                        200, render_app_page(view_names),
                        "text/html; charset=utf-8")
                    return
                if path == "/workbench/status":
                    checks = _doctor_checks()
                    latest = max(
                        (pp.stat().st_mtime for pp in WIKI.rglob("*.md")),
                        default=0)
                    # Self-healing rebuild rides the poll the page
                    # actually makes (0.12 moved the poll here and
                    # orphaned the kick on /changed — found via a
                    # stale screenshot, 2026-07-12).
                    built = REPO / "ui" / ".build-cache" / "index.html"
                    build_mtime = (built.stat().st_mtime
                                   if built.exists() else 0)
                    if latest > build_mtime and rebuild_lock.acquire(
                            blocking=False):
                        def _rebuild():
                            try:
                                subprocess.run(
                                    ["bash",
                                     str(REPO / "tools/ui-build.sh")],
                                    capture_output=True, timeout=120)
                            finally:
                                rebuild_lock.release()
                        threading.Thread(target=_rebuild,
                                         daemon=True).start()
                    self._send_json(200, {
                        "inbox": len(_inbox_items()),
                        "fails": sum(1 for c in checks
                                     if c["status"] == "fail"),
                        "warns": sum(1 for c in checks
                                     if c["status"] == "warn"),
                        "mtime": latest,
                    })
                    return
                self._send_json(404, {"error": "unknown workbench route"})
                return

            if path == "/pages.json":
                self._send_json(200, {
                    "generated": today_utc().isoformat(),
                    "pages": entries_cache,
                })
                return

            if path.startswith("/pages/"):
                rel = path[len("/pages/"):]
                target = WIKI / rel
                if not target.exists() or ".." in rel:
                    self._send_json(404, {"error": "not found"})
                    return
                parsed = parse(target)
                if parsed is None:
                    self._send_json(500, {"error": "unparseable"})
                    return
                meta, body = parsed
                u = meta.get("updated")
                if isinstance(u, dt.date):
                    meta["updated"] = u.isoformat()
                self._send_json(200, {
                    "path": rel,
                    "meta": meta,
                    "body": body,
                    "tokens": approx_tokens(body),
                })
                return

            if path.startswith("/views/"):
                axis = path[len("/views/"):]
                if axis not in {"by-kind", "by-team", "by-repo"}:
                    self._send_json(404, {"error": "unknown view"})
                    return
                groups: dict[str, list[dict]] = collections.defaultdict(list)
                for entry in entries_cache:
                    keys: list[str] = []
                    if axis == "by-kind":
                        keys = [entry.get("kind", "?")]
                    elif axis == "by-team":
                        if t := entry.get("team"):
                            keys = [t]
                    elif axis == "by-repo":
                        keys = list(entry.get("repos") or [])
                    for k in keys:
                        groups[k].append({
                            "path": entry["path"],
                            "title": entry.get("title", entry["path"]),
                            "status": entry.get("status", "?"),
                        })
                self._send_json(200, {"axis": axis, "groups": dict(groups)})
                return

            # Without ?q= the path belongs to the UI's search page
            # (static fallback below); with it, the JSON API answers.
            if path == "/search" and qs.get("q"):
                q = (qs.get("q") or [""])[0]
                if not q:
                    self._send_json(400, {"error": "missing q"})
                    return
                try:
                    out = subprocess.run(
                        ["mempalace", "search", q],
                        check=False, capture_output=True, text=True, timeout=30,
                    )
                    self._send_json(200, {
                        "query": q,
                        "stdout": out.stdout,
                        "stderr": out.stderr,
                        "returncode": out.returncode,
                    })
                except FileNotFoundError:
                    self._send_json(503, {"error": "mempalace not on PATH"})
                except subprocess.TimeoutExpired:
                    self._send_json(504, {"error": "mempalace search timed out"})
                return

            if path == "/refresh":
                refresh_cache()
                self._send_json(200, {"refreshed": len(entries_cache)})
                return

            # Everything the API doesn't own falls through to the
            # rendered wiki — including "/" (the home dashboard page).
            if serve_static(url.path):
                return
            if workbench:
                # First run: no build exists yet. The status poll has
                # already kicked one; a raw JSON error here was the
                # Noor cold-start playthrough's give-up point
                # (2026-07-12) — show a self-refreshing placeholder
                # until the build lands.
                self._send_text(200, (
                    "<!doctype html><html><head><meta charset='utf-8'>"
                    "<meta http-equiv='refresh' content='5'>"
                    "<title>brain</title>"
                    "<style>:root{color-scheme:light dark}"
                    "body{font:15px/1.5 system-ui,sans-serif;display:grid;"
                    "place-items:center;height:100vh;margin:0}</style>"
                    "</head><body><p>Building the knowledge site for the "
                    "first time&hellip; this page refreshes itself "
                    "(usually under a minute).</p></body></html>"),
                    "text/html; charset=utf-8")
                return
            self._send_json(404, {"error": "unknown endpoint "
                                           "(and no UI build to serve — "
                                           "run tools/ui-build.sh)"})

        def do_POST(self):  # noqa: N802
            url = urllib.parse.urlparse(self.path)
            # The UI's single write surface (presentation-layer ADR,
            # 2026-07-12 amendment): an action becomes an inbox item
            # the next tend session digests. Never mounted in serving
            # mode; the custom-header requirement forces a CORS
            # preflight this server never grants, so a hostile web
            # page cannot fire it cross-origin.
            if workbench and url.path == "/api/act":
                host_hdr = (self.headers.get("Host") or "").split(":")[0]
                if host_hdr not in ("localhost", "127.0.0.1", "::1", ""):
                    self._send_json(403, {"error": "host not allowed"})
                    return
                if self.headers.get("X-Brain-Act") != "1":
                    self._send_json(403, {"error": "missing action header"})
                    return
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    body = json.loads(self.rfile.read(min(n, 65536)))
                    action = str(body["action"])
                    target = str(body.get("target", ""))[:300]
                    note = str(body.get("note", ""))[:2000]
                except (KeyError, ValueError, json.JSONDecodeError):
                    self._send_json(400, {"error": "bad action body"})
                    return
                if action not in ("execute", "comment"):
                    self._send_json(400, {"error": "unknown action"})
                    return
                stamp = _dt_now_compact()
                item_id = f"ui-{action}-{stamp}"
                if action == "execute":
                    summary = (f"operator queued {target or 'work'} for "
                               f"execution from the briefing"
                               + (f' — "{note}"' if note else ""))
                    priority = "high"
                else:
                    summary = (f'operator comment on {target or "the brain"}:'
                               f' "{note}"')
                    priority = "normal"
                try:
                    inbox_add(id=item_id, kind="custom", summary=summary,
                              route="/tend " + item_id, priority=priority,
                              source=target, produced_by="ui-action")
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                self._send_json(200, {"queued": item_id})
                return
            self._send_json(405, {"error": "read-only"})

    class Server(socketserver.ThreadingTCPServer):
        # Reuse-addr: restarts must not trip over TIME_WAIT sockets.
        # Threading: a background UI rebuild kicked from the status
        # poll must not block the JSON API.
        allow_reuse_address = True
        daemon_threads = True

    with Server((host, port), Handler) as httpd:
        print(f"brain serving on http://{host}:{port}"
              + ("  (+ /workbench)" if workbench else ""))
        print(f"  {len(entries_cache)} pages cached; GET /refresh to reload")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nshutting down")
    return 0


def cmd_cluster(args) -> int:
    """TF-IDF + HDBSCAN over wiki page bodies.

    Surfaces clusters of related pages — especially clusters that span
    multiple teams or repos, which are overlap candidates `/overlap`
    might want to follow up on. This is the at-scale path for Goal 2;
    when the corpus is small (< ~10 pages) it just reports that.
    """
    pages = wiki_pages()
    parsed_pages = []
    for p in pages:
        parsed = parse(p)
        if parsed is None:
            continue
        meta, body = parsed
        parsed_pages.append((p, meta, body))

    n = len(parsed_pages)
    if n < args.min_corpus:
        print(f"corpus too small for clustering: {n} pages "
              f"(need ≥ {args.min_corpus}). Run /overlap pair-wise instead.")
        return 0

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import HDBSCAN
    except ImportError as e:
        print(f"missing dep: {e}. install scikit-learn into the mempalace venv.")
        return 1

    docs = [body for _, _, body in parsed_pages]
    vec = TfidfVectorizer(stop_words="english", max_features=4096,
                          ngram_range=(1, 2), min_df=1)
    X = vec.fit_transform(docs).toarray()

    min_cluster = max(2, args.min_cluster)
    hdb = HDBSCAN(min_cluster_size=min_cluster, metric="euclidean", copy=True)
    labels = hdb.fit_predict(X)

    clusters: dict[int, list[int]] = collections.defaultdict(list)
    for idx, lbl in enumerate(labels):
        clusters[int(lbl)].append(idx)

    noise = clusters.pop(-1, [])
    print(f"clustered {n} pages into {len(clusters)} clusters; "
          f"{len(noise)} pages classified as noise (no cluster).")

    overlap_candidates = []
    for lbl, idxs in sorted(clusters.items()):
        page_metas = [parsed_pages[i][1] for i in idxs]
        teams = sorted({m.get("team") for m in page_metas if m.get("team")})
        all_repos = set()
        for m in page_metas:
            for r in m.get("repos") or []:
                all_repos.add(r)
        is_candidate = len(teams) > 1 or len(all_repos) > 1
        marker = "★ overlap candidate" if is_candidate else ""
        print(f"\ncluster {lbl} ({len(idxs)} pages) "
              f"{marker}")
        if teams:
            print(f"  teams: {', '.join(teams)}")
        if all_repos:
            print(f"  repos: {', '.join(sorted(all_repos))}")
        for i in idxs:
            p, meta, _ = parsed_pages[i]
            print(f"  - {p.relative_to(WIKI)}  "
                  f"({meta.get('kind', '?')}, {meta.get('status', '?')})")
        if is_candidate:
            overlap_candidates.append((lbl, idxs))

    if overlap_candidates:
        print(f"\n{len(overlap_candidates)} overlap-candidate cluster(s) "
              f"flagged. Run `/overlap` on each to investigate.")

    return 0


def cmd_promote(args) -> int:
    insight_rel = args.insight
    insight_path = (WIKI / insight_rel).resolve()
    if not insight_path.exists() or WIKI not in insight_path.parents:
        print(f"insight not found under wiki/: {insight_rel}")
        return 1

    parsed = parse(insight_path)
    if parsed is None:
        print(f"unparseable: {insight_path}")
        return 1
    meta, _body = parsed
    if meta.get("kind") != "insight":
        print(f"not a kind: insight page (got kind={meta.get('kind')!r})")
        return 1
    if meta.get("status") == "superseded":
        print(f"already superseded: {insight_path.relative_to(REPO)}")
        return 1

    insight_name = insight_path.name
    insight_slug = insight_path.stem
    initiative_slug = args.slug or f"{insight_slug}-initiative"
    initiative_path = WIKI / f"{initiative_slug}.md"
    if initiative_path.exists():
        print(f"target already exists: {initiative_path.relative_to(REPO)}")
        return 1

    today = today_utc().isoformat()
    title = meta.get("title", insight_slug)

    init_fm: dict = {
        "title": f"{title} — initiative",
        "kind": "initiative",
        "status": "draft",
        "updated": today,
        "confidence": "low",
        "supersedes": insight_name,
    }
    if t := meta.get("team"):
        init_fm["team"] = t
    if d := meta.get("division"):
        init_fm["division"] = d
    if r := meta.get("repos"):
        init_fm["repos"] = r
    init_fm["sources"] = list(meta.get("sources") or [])

    fm_yaml = yaml.safe_dump(init_fm, sort_keys=False).strip()
    body = f"""# {init_fm['title']}

Promoted from [{insight_name}](./{insight_name}). The insight remains
the evidence record; this initiative is what we plan to do about it.

## What
TODO — define the work, derived from the insight's `## Pattern`.

## How
TODO — implementation approach, sequencing, dependencies.

## Why
TODO — extract from the insight's `## Implications`.

## Now
TODO — current state once work begins.

## Perceived
TODO — what the org currently believes about this area.

## Target
TODO — desired end state.
"""
    initiative_path.write_text(f"---\n{fm_yaml}\n---\n\n{body}")

    text = insight_path.read_text()
    parts = text.split("---", 2)
    if len(parts) < 3:
        print("could not re-split insight frontmatter; aborting in-place edit")
        return 1
    fm_text = parts[1]
    fm_text = re.sub(r"^status:.*$", "status: superseded", fm_text,
                     count=1, flags=re.MULTILINE)
    if "superseded_by:" not in fm_text:
        fm_text = fm_text.rstrip() + f"\nsuperseded_by: {initiative_slug}.md\n"
    insight_path.write_text(f"---{fm_text}---{parts[2]}")

    print(f"promoted {insight_path.relative_to(REPO)} → "
          f"{initiative_path.relative_to(REPO)}")
    print(f"next: edit {initiative_path.relative_to(REPO)} to fill the TODOs")
    print("then: update wiki/index.md and run `brain.py validate views`")
    return 0


def cmd_personas(args) -> int:
    """Infer the RFC persona pool for a wiki page.

    Reads `wiki/<path>` frontmatter, walks `.claude/personas/{team,
    users,agents}/`, and prints the pool the `rfc` skill would
    consult. Sole purpose: deterministic pool inference visible to
    the operator before the LLM-driven `rfc` skill runs.
    """
    page_rel = args.page
    page_path = (WIKI / page_rel).resolve()
    if not page_path.exists() or WIKI not in page_path.parents:
        print(f"page not found under wiki/: {page_rel}")
        return 1

    parsed = parse(page_path)
    if parsed is None:
        print(f"unparseable frontmatter: {page_rel}")
        return 1
    meta, body = parsed

    personas_dir = REPO / ".claude" / "personas"
    pool: list[tuple[str, str, str]] = []  # (level, slug, frontmatter dict label)
    seen: set[str] = set()

    def add(level: str, slug: str, label: str):
        key = f"{level}/{slug}"
        if key in seen:
            return
        seen.add(key)
        pool.append((level, slug, label))

    # Always: agent personas (PM / Tech Lead / Developer).
    for slug in ("pm-agent", "tech-lead-agent", "developer-agent"):
        if (personas_dir / "agents" / f"{slug}.md").exists():
            add("agents", slug, slug.replace("-", " "))

    # Team personas matching `team:` or relevant to `repos:` /
    # `affects:`.
    page_team = meta.get("team")
    page_repos = set(meta.get("repos") or [])
    page_affects = set(meta.get("affects") or [])
    repo_set = page_repos | page_affects

    team_dir = personas_dir / "team"
    if team_dir.exists():
        for f in sorted(team_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            p_parsed = parse(f)
            if p_parsed is None:
                continue
            p_meta, _ = p_parsed
            persona_team = p_meta.get("team")
            label_name = p_meta.get("name", f.stem)
            label_role = p_meta.get("role", "")
            label = f"{label_name} — {label_role}".strip(" —")
            # Match team directly.
            if page_team and persona_team and page_team == persona_team:
                add("team", f.stem, label)
                continue
            # Platform / Architect / Engineering Manager / VP roles
            # are cross-repo by nature — include if any repo is set.
            cross_repo_roles = (
                "Platform", "Engineering", "Architect", "Autonomous",
            )
            persona_div = p_meta.get("division", "")
            if repo_set and any(
                r in label_role or r in persona_div
                for r in cross_repo_roles
            ):
                add("team", f.stem, label)

    # User personas explicitly named under `## Affected personas`.
    affected_section = ""
    in_section = False
    for line in body.splitlines():
        if re.match(r"^##\s+Affected personas\b", line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            affected_section += line + "\n"

    if affected_section:
        users_dir = personas_dir / "users"
        if users_dir.exists():
            for f in sorted(users_dir.glob("*.md")):
                if f.name == "README.md":
                    continue
                slug = f.stem
                # Match by slug or by display name in the section.
                if slug in affected_section:
                    p_parsed = parse(f)
                    if p_parsed:
                        p_meta, _ = p_parsed
                        label = (
                            f"{p_meta.get('name', slug)} — "
                            f"{p_meta.get('role', 'user persona')}"
                        )
                    else:
                        label = slug
                    add("users", slug, label)

    # Cap at 6 to keep RFC bounded.
    capped = pool[:6]
    overflow = pool[6:]

    print(f"RFC pool for wiki/{page_rel}:")
    for level, slug, label in capped:
        print(f"  - [{level}] {label}")
    if overflow:
        print(f"  ({len(overflow)} more inferred but capped: "
              f"{', '.join(s for _, s, _ in overflow)})")
    return 0


def cmd_rotate_log(_args) -> int:
    """Rotate `log/log.md` if it exceeds the size threshold.

    Per AGENTS.md § Audit log § Rotation policy:
    - Threshold: 2,000 lines OR ~200 KB.
    - On rotation: move current log/log.md → log/archive/log-<UTC>.md
      and create a fresh log/log.md with a one-line pointer back.
    - Mechanical, no judgement.

    Idempotent: if the threshold isn't reached, returns 0 with a
    "no rotation needed" message.
    """
    log_dir = REPO / "log"
    log_path = log_dir / "log.md"
    if not log_path.exists():
        print("no log/log.md to rotate")
        return 0

    text = log_path.read_text()
    lines = text.splitlines()
    size_bytes = len(text.encode())

    THRESH_LINES = 2000
    THRESH_BYTES = 200 * 1024  # 200 KB

    if len(lines) < THRESH_LINES and size_bytes < THRESH_BYTES:
        print(
            f"no rotation needed: {len(lines)} lines, "
            f"{size_bytes} bytes "
            f"(threshold: {THRESH_LINES} lines / "
            f"{THRESH_BYTES} bytes)"
        )
        return 0

    archive_dir = log_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    today = today_utc().isoformat()
    archive_path = archive_dir / f"log-{today}.md"

    if archive_path.exists():
        print(f"refusing to overwrite existing archive: "
              f"{archive_path.relative_to(REPO)}")
        return 1

    archive_path.write_text(text)
    fresh = (
        "# Log\n\n"
        "Append-only. Newest entries at the bottom. One line per "
        "operation:\n"
        "`YYYY-MM-DD <ingest|query|lint|meta> — <summary>`.\n\n"
        f"Previous: log/archive/log-{today}.md\n"
    )
    log_path.write_text(fresh)

    print(
        f"rotated log/log.md → {archive_path.relative_to(REPO)} "
        f"({len(lines)} lines, {size_bytes} bytes)"
    )
    return 0


def cmd_snapshot(_args) -> int:
    """Write a brain snapshot — corpus shape at a point in time.

    Drops a JSON file under `wiki/_views/snapshots/<UTC-date>.json`
    summarising:
      - per-kind / per-status / per-team / per-repo counts
      - per-page (path → kind, status, confidence, updated, tokens)
      - aggregate token total
      - count of pages flagged stale per `cmd_stats`'s thresholds

    Snapshots compose: diffing two of them shows brain motion over
    time. Cheap to produce; safe to run as part of /sync.
    """
    entries = collect_pages_data()
    snap_dir = WIKI / "_views" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)

    today = today_utc().isoformat()
    by_kind: dict = collections.Counter()
    by_status: dict = collections.Counter()
    by_team: dict = collections.Counter()
    by_repo: dict = collections.Counter()
    by_conf: dict = collections.Counter()
    total_tokens = 0
    pages_summary = []
    for e in entries:
        by_kind[e.get("kind", "?")] += 1
        by_status[e.get("status", "?")] += 1
        by_team[e.get("team", "(none)")] += 1
        for r in e.get("repos") or []:
            by_repo[r] += 1
        by_conf[e.get("confidence", "(none)")] += 1
        total_tokens += int(e.get("tokens", 0) or 0)
        pages_summary.append({
            "path": e["path"],
            "kind": e.get("kind"),
            "status": e.get("status"),
            "confidence": e.get("confidence"),
            "updated": e.get("updated"),
            "tokens": e.get("tokens"),
        })

    snap = {
        "generated": today,
        "totals": {
            "pages": len(entries),
            "tokens": total_tokens,
        },
        "by_kind": dict(by_kind),
        "by_status": dict(by_status),
        "by_team": dict(by_team),
        "by_repo": dict(by_repo),
        "by_confidence": dict(by_conf),
        "pages": pages_summary,
    }

    out = snap_dir / f"{today}.json"
    out.write_text(json.dumps(snap, indent=2, sort_keys=False))
    print(f"wrote {out.relative_to(REPO)}")
    print(f"  {snap['totals']['pages']} pages, "
          f"{snap['totals']['tokens']} tokens")
    return 0


# Notion write tools that must always be deny-listed in
# .claude/settings.json. The CI guard `check-no-notion-writes`
# enforces both directions: every name here is in `deny`, and
# nothing else under tools/ or .claude/ invokes them.
NOTION_WRITE_TOOLS = (
    "mcp__claude_ai_Notion__notion-create-pages",
    "mcp__claude_ai_Notion__notion-create-database",
    "mcp__claude_ai_Notion__notion-create-comment",
    "mcp__claude_ai_Notion__notion-create-view",
    "mcp__claude_ai_Notion__notion-update-page",
    "mcp__claude_ai_Notion__notion-update-data-source",
    "mcp__claude_ai_Notion__notion-update-view",
    "mcp__claude_ai_Notion__notion-duplicate-page",
    "mcp__claude_ai_Notion__notion-move-pages",
)


def cmd_check_no_notion_writes(_args) -> int:
    """Enforce the read-only Notion doctrine.

    Two checks:
    1. Every NOTION_WRITE_TOOLS entry must appear in the `deny` list
       of .claude/settings.json. Drift from this list is forbidden.
    2. No other tracked file (under .claude/, tools/, .github/) may
       *use* a Notion write tool name. Settings + this file (which
       defines the list) + AGENTS.md (which documents it) are the
       only allowed mentions.
    """
    settings_path = REPO / ".claude" / "settings.json"
    if not settings_path.exists():
        print(f"missing: {settings_path.relative_to(REPO)}")
        return 1

    settings = json.loads(settings_path.read_text())
    deny = set(settings.get("permissions", {}).get("deny", []))
    missing = [t for t in NOTION_WRITE_TOOLS if t not in deny]
    if missing:
        print("ERROR  Notion write tools missing from "
              ".claude/settings.json deny list:")
        for t in missing:
            print(f"  - {t}")
        return 1

    # Allowed mentions: the deny list itself, this enforcement code,
    # and the AGENTS.md doctrine + the seeded ADR.
    allowed_mentions = {
        ".claude/settings.json",
        "tools/brain.py",
        "AGENTS.md",
        "wiki/brain/adrs/notion-is-read-only.md",
    }

    rogue: list[tuple[str, int, str]] = []
    scan_roots = [".claude", "tools", ".github"]
    # Skip transient agent harness state and tool caches.
    skip_dir_names = {
        "__pycache__", "node_modules", ".cache",
        "worktrees",  # .claude/worktrees/ is the subagent harness's workspace
    }
    skip_suffixes = {".pyc", ".pyo"}
    for root in scan_roots:
        root_path = REPO / root
        if not root_path.exists():
            continue
        for p in root_path.rglob("*"):
            if not p.is_file():
                continue
            # Use the path relative to REPO for the skip check, not
            # the absolute path. Otherwise running this inside a
            # worktree (where REPO itself sits under .claude/worktrees/)
            # would skip every file the absolute path traverses through.
            rel_path = p.relative_to(REPO)
            if any(part in skip_dir_names for part in rel_path.parts):
                continue
            if p.suffix in skip_suffixes:
                continue
            rel = str(rel_path)
            if rel in allowed_mentions:
                continue
            try:
                text = p.read_text(errors="ignore")
            except Exception:
                continue
            for tool in NOTION_WRITE_TOOLS:
                for ln, line in enumerate(text.splitlines(), 1):
                    if tool in line:
                        rogue.append((rel, ln, tool))

    if rogue:
        print("ERROR  Notion write tool names found outside the deny "
              "list / doctrine:")
        for rel, ln, tool in rogue:
            print(f"  {rel}:{ln}: {tool}")
        return 1

    print(f"OK  Notion read-only enforcement intact: "
          f"{len(NOTION_WRITE_TOOLS)} write tools deny-listed")
    return 0


def cmd_check_home_fresh(args) -> int:
    """Verify any wiki/ change on this branch is paired with a wiki/index.md change.

    The brain UI's home page (wiki/index.md) is an agent-maintained
    dashboard. Per wiki/brain/adrs/home-content-shape.md, every
    wiki/ edit must update the relevant home-page section in the
    same PR. The local Stop hook (tools/home-staleness.sh) catches
    accidents during a session; this command is the load-bearing
    CI guard that catches whatever the hook missed.

    Triggering paths: wiki/** except wiki/_views/**, wiki/_archive/**,
    and wiki/index.md itself. Modified or added.
    """
    base = getattr(args, "base", "origin/main") or "origin/main"
    diff_cmd = ["git", "diff", "--name-only", f"{base}...HEAD"]
    try:
        diff = subprocess.check_output(diff_cmd, text=True,
                                       stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        # If the base ref doesn't exist (fresh clone, force-pushed
        # main, etc.), be loud — better to fail CI visibly than to
        # silently let a bypass through.
        print(f"ERR: git diff failed against {base}: {e.stderr}", file=sys.stderr)
        return 1

    files = [line for line in diff.splitlines() if line]
    triggers: list[str] = []
    home_touched = False
    for f in files:
        if f == "wiki/index.md":
            home_touched = True
            continue
        if f.startswith("wiki/_views/"):
            continue
        if f.startswith("wiki/_archive/"):
            continue
        if f.startswith("wiki/"):
            triggers.append(f)

    if triggers and not home_touched:
        print("ERROR  this branch modifies wiki/ content but does not "
              "update wiki/index.md (the home page).", file=sys.stderr)
        print("Triggering files:", file=sys.stderr)
        for t in triggers:
            print(f"  - {t}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Per wiki/brain/adrs/home-content-shape.md, every wiki/ "
              "edit must update the relevant section on wiki/index.md.",
              file=sys.stderr)
        return 1

    if triggers:
        print(f"OK  home page touched alongside {len(triggers)} "
              f"wiki/ change(s).")
    else:
        print("OK  no wiki/ changes that require a home-page update.")
    return 0


README_TRIGGER_ALWAYS = {
    "AGENTS.md",
    "tools/brain.py",
    ".claude/settings.json",
}


def _is_readme_trigger(path: str, status: str) -> bool:
    """Return True iff a path+git-status pair counts as a README-staleness trigger.

    Trigger paths (any one suffices) on add or modify:
        - AGENTS.md (schema / governance change)
        - tools/brain.py (validator / view emit / scope rules)
        - tools/templates/** (ADR / PRD template structure)
        - .claude/settings.json (hooks, permissions, slash commands)
        - .claude/skills/** (skill protocol changes)
        - ui/astro.config.mjs / ui/serve.mjs / ui/Dockerfile
          (UI substrate)

    Note: earlier shapes triggered on `wiki/<scope>/ai-suggestions/**`
    and `wiki/_views/*.md` adds, intending to catch "new shelf
    appearing." That heuristic was too broad — every new draft
    fired the check, even within an existing shelf, which doesn't
    affect README content. Removed in favour of the always-trigger
    set; "new shelf" cases will be caught indirectly when AGENTS.md
    or `tools/brain.py` is updated to introduce them.
    """
    if path in README_TRIGGER_ALWAYS:
        return status in {"A", "M"}
    if path.startswith("tools/templates/"):
        return status in {"A", "M"}
    if path.startswith(".claude/skills/"):
        return status in {"A", "M"}
    if path in {"ui/astro.config.mjs", "ui/serve.mjs", "ui/Dockerfile"}:
        return status in {"A", "M"}
    return False


def cmd_check_readme_fresh(args) -> int:
    """CI gate: verify significant changes on this branch are paired with a README.md edit.

    Mirrors check-home-fresh's shape but for README.md instead of
    wiki/index.md. The trigger set is governance/tooling/schema-
    affecting changes (per tools/readme-staleness.sh and AGENTS.md
    governance discussions). README freshness is enforced at PR
    time as a hard gate; in-session reminders are not used (see
    user direction 2026-05-03 question #9).

    Trigger paths: see _is_readme_trigger above.
    """
    base = getattr(args, "base", "origin/main") or "origin/main"
    diff_cmd = ["git", "diff", "--name-status", f"{base}...HEAD"]
    try:
        diff = subprocess.check_output(diff_cmd, text=True,
                                       stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"ERR: git diff failed against {base}: {e.stderr}", file=sys.stderr)
        return 1

    triggers: list[str] = []
    readme_touched = False
    for line in diff.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][0]  # First char (handles R100 etc.)
        path = parts[-1]      # Last entry (handles renames -> dest)
        if path == "README.md":
            readme_touched = True
            continue
        if _is_readme_trigger(path, status):
            triggers.append(f"{status} {path}")

    if triggers and not readme_touched:
        print("ERROR  this branch has significant changes but does not "
              "update README.md.", file=sys.stderr)
        print("Triggering files:", file=sys.stderr)
        for t in triggers:
            print(f"  - {t}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Per the readme-staleness convention (tools/readme-"
              "staleness.sh § Significant-change patterns), changes "
              "to schema / governance / tooling / templates / hooks / "
              "skills / UI substrate / new ai-suggestions shelves / "
              "new auto-generated views must be reflected in README.md.",
              file=sys.stderr)
        print("", file=sys.stderr)
        print("Either:", file=sys.stderr)
        print("  - Edit README.md to reflect the change (recommended), or",
              file=sys.stderr)
        print("  - Make a no-op edit to README.md (e.g. clarify a sentence) "
              "to acknowledge that README.md was reviewed and no "
              "substantive change is needed.", file=sys.stderr)
        return 1

    if triggers:
        print(f"OK  README.md touched alongside {len(triggers)} "
              f"significant change(s).")
    else:
        print("OK  no significant changes that require a README update.")
    return 0


def _missing_sibling_msg(repo_path: Path) -> str:
    """Single source of truth for the 'sibling repo missing' message.

    Bakes in the $BRAIN_PROJECTS_ROOT hint so any operator hitting the
    error sees the override knob inline. Per
    wiki/brain/adrs/configurable-projects-dir.md.
    """
    return (
        f"sibling repo not found at {repo_path} — set "
        f"$BRAIN_PROJECTS_ROOT (currently "
        f"{'set to ' + str(PROJECTS) if 'BRAIN_PROJECTS_ROOT' in os.environ else 'unset; default ' + str(PROJECTS)})"
        " or create the directory"
    )


def _sibling_repo(repo_name: str) -> Path:
    """Resolve a sibling-repo name to its filesystem path."""
    p = PROJECTS / repo_name
    if not p.exists():
        raise SystemExit(_missing_sibling_msg(p))
    if not (p / ".git").exists():
        raise SystemExit(f"{p} is not a git repository")
    return p


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(
        ["git"] + args, cwd=cwd, text=True
    ).strip()


def _read_cursors() -> dict:
    if not SYNC_CURSORS.exists():
        return {"version": 1, "generated": today_utc().isoformat(), "cursors": {}}
    return json.loads(SYNC_CURSORS.read_text())


def _write_cursors(data: dict) -> None:
    SYNC_CURSORS.parent.mkdir(exist_ok=True)
    data["generated"] = today_utc().isoformat()
    SYNC_CURSORS.write_text(json.dumps(data, indent=2) + "\n")


def _doctor_checks() -> list[dict]:
    """The health checklist behind `doctor`, `setup`, and the /dash
    surface. Each check: id, label, status (ok|warn|fail), detail,
    hint (the command that fixes a warn/fail; empty when healthy).
    Warns are missing ergonomics; fails are broken substrate.
    """
    checks: list[dict] = []

    def add(id: str, label: str, status: str, detail: str, hint: str = ""):
        checks.append({"id": id, "label": label, "status": status,
                       "detail": detail, "hint": hint})

    if (REPO / ".git").exists():
        add("git", "git repository", "ok", "initialised")
    else:
        add("git", "git repository", "fail", "no .git — history and the "
            "audit trail need git", "git init")

    venv_python = Path.home() / ".local/share/mempalace-venv/bin/python3"
    try:
        import tiktoken  # noqa: F401
        add("tiktoken", "token counting", "ok", "tiktoken available")
    except ImportError:
        if venv_python.exists() and subprocess.run(
                [str(venv_python), "-c", "import tiktoken"],
                capture_output=True).returncode == 0:
            add("tiktoken", "token counting", "ok",
                f"tiktoken available in the local venv ({venv_python})")
        else:
            add("tiktoken", "token counting", "warn",
                "tiktoken missing — pages.json token counts drift vs CI",
                "tools/setup-local.sh")

    env_path = REPO / ".env"
    if env_path.exists():
        local_first = _local_first(env_path)
        add("env", "operating mode", "ok",
            "local-first (single operator)" if local_first
            else "PR-gated (multi-agent)")
    else:
        add("env", "operating mode", "warn",
            ".env missing — defaults to PR-gated mode",
            "cp .env.example .env")

    config_path = REPO / "brain.config.yml"
    if config_path.exists():
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
        except yaml.YAMLError:
            cfg = None
        if cfg is None:
            add("config", "brain.config.yml", "fail", "unparseable YAML",
                "fix the YAML syntax")
        else:
            org = (cfg.get("org") or "").strip()
            repos = cfg.get("active_repos") or []
            if not org and not repos:
                add("config", "brain.config.yml", "warn",
                    "org and active_repos are empty — the shell is "
                    "unconfigured", "python3 tools/brain.py setup")
            elif not repos:
                add("config", "brain.config.yml", "warn",
                    f"org={org!r}; no active repos declared yet",
                    "add repos to active_repos in brain.config.yml")
            else:
                missing = [r for r in repos if not (PROJECTS / r).exists()]
                if missing:
                    add("config", "brain.config.yml", "warn",
                        f"{len(repos)} repo(s); missing on disk: "
                        f"{', '.join(missing)}",
                        f"clone them under {PROJECTS} or adjust "
                        "BRAIN_PROJECTS_ROOT")
                else:
                    add("config", "brain.config.yml", "ok",
                        f"org={org!r}; {len(repos)} active repo(s), all "
                        "on disk")
    else:
        add("config", "brain.config.yml", "fail", "missing",
            "python3 tools/brain.py setup")

    hook = REPO / ".git" / "hooks" / "pre-commit"
    if hook.is_symlink() or hook.exists():
        add("pre-commit", "pre-commit gate", "ok", "installed")
    else:
        add("pre-commit", "pre-commit gate", "warn",
            "not installed — validate/views run only in CI",
            "ln -s ../../tools/git-hooks/pre-commit .git/hooks/pre-commit")

    import hashlib as _hashlib
    instance = (re.sub(r"[^a-zA-Z0-9-]", "", REPO.name) + "-"
                + _hashlib.sha1(str(REPO).encode()).hexdigest()[:6])
    timer_unit = f"brain-{instance}-schedule.timer"
    timer_state = ""
    if shutil.which("systemctl"):
        res = subprocess.run(
            ["systemctl", "--user", "is-active", timer_unit],
            capture_output=True, text=True)
        timer_state = res.stdout.strip()
    if timer_state == "active":
        add("timer", "accumulation timer", "ok",
            f"{timer_unit} active (daily run-due)")
    else:
        add("timer", "accumulation timer", "warn",
            "no local timer — producers only run when invoked by hand",
            "tools/install-timer.sh")

    if (REPO / "ui" / "node_modules").exists():
        add("ui", "browse UI", "ok", "dependencies installed")
    else:
        add("ui", "browse UI", "warn", "ui/node_modules missing",
            "cd ui && npm install")

    if shutil.which("claude"):
        add("agent", "agent CLI", "ok",
            "claude on PATH — `brain tend` works")
    else:
        add("agent", "agent CLI", "warn",
            "no agent CLI found — the brain still works as a validated "
            "wiki; any MCP-aware agent can connect",
            "install an agent CLI or use the MCP server")

    items = _inbox_items()
    add("inbox", "tend queue", "ok",
        f"{len(items)} pending" if items else "empty")

    leaked = [v for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                          "OPENAI_API_KEY", "CURSOR_API_KEY",
                          "OPENCODE_API_KEY") if os.environ.get(v)]
    if leaked:
        add("billing", "billing check", "warn",
            f"{', '.join(leaked)} set in this environment — harness "
            f"CLIs launched from this shell may bill the metered "
            f"API instead of your logged-in subscription",
            "unset the key(s) in the shell you run your harness from")
    else:
        add("billing", "billing check", "ok",
            "no API-key env vars — harness sessions bill your "
            "logged-in subscription")

    return checks


def cmd_setup(args) -> int:
    """One-command bootstrap for a fresh checkout. Idempotent — every
    step detects "already done" and skips. `--yes` accepts every
    optional step non-interactively; `--dry-run` prints the plan.
    """
    dry = args.dry_run
    yes = args.yes
    interactive = sys.stdin.isatty() and not yes and not dry

    def confirm(question: str, default: bool = True) -> bool:
        if dry:
            return False
        if yes:
            return True
        if not interactive:
            # Piped/CI stdin without --yes must never consent to
            # side-effectful steps (timer, PATH symlink, npm) — the
            # Noor cold-start playthrough caught setup auto-installing
            # through a pipe, 2026-07-12.
            print(f"  − {question} — skipped (non-interactive; "
                  f"re-run with --yes to accept)")
            return False
        answer = input(f"  {question} [{'Y/n' if default else 'y/N'}] ").strip().lower()
        return default if not answer else answer in ("y", "yes")

    def step(label: str, needed: bool, action, hint: str = ""):
        if not needed:
            print(f"  ✓ {label} — already done")
            return
        if dry:
            print(f"  → would: {label}" + (f"  ({hint})" if hint else ""))
            return
        action()
        print(f"  ✓ {label}")

    print("# brain setup\n")

    env_path = REPO / ".env"
    step(".env (local-first mode)", not env_path.exists(),
         lambda: shutil.copy(REPO / ".env.example", env_path))

    config_path = REPO / "brain.config.yml"
    cfg_text = config_path.read_text()
    org = args.org
    if 'org: ""' in cfg_text:
        if not org and interactive:
            org = input("  organisation name (empty to skip): ").strip()
        if org:
            step(f"config: org = {org!r}", True,
                 lambda: config_path.write_text(
                     config_path.read_text().replace(
                         'org: ""', f'org: "{org}"', 1)))
        else:
            print("  − config: org left empty (edit brain.config.yml later)")
    else:
        print("  ✓ config: org — already set")

    repos = [r.strip() for r in (args.repos or "").split(",") if r.strip()]
    if "active_repos: []" in config_path.read_text():
        if not repos and interactive:
            raw = input("  active repos, comma-separated (empty to skip): ")
            repos = [r.strip() for r in raw.split(",") if r.strip()]
        if repos:
            block = "active_repos:\n" + "".join(f"  - {r}\n" for r in repos)
            step(f"config: {len(repos)} active repo(s)", True,
                 lambda: config_path.write_text(
                     config_path.read_text().replace(
                         "active_repos: []\n", block, 1)))
        else:
            print("  − config: active_repos left empty (edit later)")
    else:
        print("  ✓ config: active_repos — already set")

    hook = REPO / ".git" / "hooks" / "pre-commit"
    step("pre-commit gate", (REPO / ".git").exists() and not hook.exists(),
         lambda: hook.symlink_to("../../tools/git-hooks/pre-commit"))

    try:
        import tiktoken  # noqa: F401
        has_tiktoken = True
    except ImportError:
        venv_python = Path.home() / ".local/share/mempalace-venv/bin/python3"
        has_tiktoken = venv_python.exists() and subprocess.run(
            [str(venv_python), "-c", "import tiktoken"],
            capture_output=True).returncode == 0
    if not has_tiktoken and confirm("create the local venv (tiktoken, pytest)?"):
        step("local venv", True, lambda: subprocess.run(
            ["bash", str(REPO / "tools" / "setup-local.sh")], check=False))

    import hashlib as _hashlib
    instance = (re.sub(r"[^a-zA-Z0-9-]", "", REPO.name) + "-"
                + _hashlib.sha1(str(REPO).encode()).hexdigest()[:6])
    timer_active = False
    if shutil.which("systemctl"):
        timer_active = subprocess.run(
            ["systemctl", "--user", "is-active",
             f"brain-{instance}-schedule.timer"],
            capture_output=True, text=True).stdout.strip() == "active"
    if not timer_active and confirm("install the daily accumulation timer?"):
        step("accumulation timer", True, lambda: subprocess.run(
            ["bash", str(REPO / "tools" / "install-timer.sh")], check=False))

    wrapper_dst = Path.home() / ".local" / "bin" / "brain"
    if not shutil.which("brain") and not wrapper_dst.exists() and confirm(
            "put the `brain` command on your PATH (~/.local/bin)?"):
        def _link_wrapper():
            wrapper_dst.parent.mkdir(parents=True, exist_ok=True)
            wrapper_dst.symlink_to(REPO / "tools" / "brain")
        step("`brain` on PATH", True, _link_wrapper)

    ui_deps = REPO / "ui" / "node_modules"
    if not ui_deps.exists() and shutil.which("npm") and confirm(
            "install the browse-UI dependencies (npm install)?"):
        step("browse-UI dependencies", True, lambda: subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund"],
            cwd=REPO / "ui", check=False, capture_output=True))

    if dry:
        print("\n(dry run — nothing changed)")
        return 0
    print("\n# health after setup\n")

    class _DoctorArgs:
        json = False

    rc = cmd_doctor(_DoctorArgs())
    # End with the next command that is KNOWN to work on this
    # machine — the quickstart's third step must never be a guess
    # (insight: quickstart-third-command-fragility).
    next_cmd = "brain" if shutil.which("brain") else "tools/brain"
    print(f"\nnext: {next_cmd}    # opens the app")
    if next_cmd != "brain":
        print("      (`brain` isn't on your PATH — accept the PATH "
              "step next time, or use tools/brain)")
    return rc


# One row per harness: where its MCP registration lives and how it
# nests. Per the mcp-cli-surface ADR: adapters are data
# tables, not per-harness code paths; a new harness is one row here.
AGENT_TARGETS = {
    "claude": {"path": ".mcp.json", "format": "json",
               "nest": ["mcpServers", "brain"],
               "entry": {"command": "python3",
                         "args": ["./tools/brain-mcp.py"],
                         "env": {"BRAIN_DIR": "."}}},
    "cursor": {"path": ".cursor/mcp.json", "format": "json",
               "nest": ["mcpServers", "brain"],
               "entry": {"command": "python3",
                         "args": ["./tools/brain-mcp.py"],
                         "env": {"BRAIN_DIR": "."}}},
    "opencode": {"path": "opencode.json", "format": "json",
                 "nest": ["mcp", "brain"],
                 "entry": {"type": "local",
                           "command": ["python3", "./tools/brain-mcp.py"],
                           "enabled": True}},
    "codex": {"path": ".codex/config.toml", "format": "toml-block",
              "block": ('[mcp_servers.brain]\n'
                        'command = "python3"\n'
                        'args = ["./tools/brain-mcp.py"]\n')},
}

AGENT_SENTINEL_OPEN = "# >>> brain:managed >>>"
AGENT_SENTINEL_CLOSE = "# <<< brain:managed <<<"


def install_agent(harness: str, root: Path) -> str:
    """Idempotently register the brain's MCP server for one harness.

    JSON targets deep-merge the entry under its nesting keys,
    preserving everything else in the file. TOML targets append a
    sentinel-fenced block (stdlib has no TOML writer); content inside
    the fence is ours, everything outside is never touched.
    Returns 'wrote' | 'unchanged'.
    """
    row = AGENT_TARGETS[harness]
    target = root / row["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if row["format"] == "json":
        data = {}
        if target.exists():
            try:
                data = json.loads(target.read_text())
            except json.JSONDecodeError:
                raise ValueError(f"{target} exists but is not valid JSON — "
                                 f"fix or remove it first")
        node = data
        for key in row["nest"][:-1]:
            node = node.setdefault(key, {})
        if node.get(row["nest"][-1]) == row["entry"]:
            return "unchanged"
        node[row["nest"][-1]] = row["entry"]
        target.write_text(json.dumps(data, indent=2) + "\n")
        return "wrote"
    text = target.read_text() if target.exists() else ""
    fenced = (f"{AGENT_SENTINEL_OPEN}\n{row['block']}"
              f"{AGENT_SENTINEL_CLOSE}\n")
    if AGENT_SENTINEL_OPEN in text:
        start = text.index(AGENT_SENTINEL_OPEN)
        end = text.index(AGENT_SENTINEL_CLOSE) + len(AGENT_SENTINEL_CLOSE) + 1
        new = text[:start] + fenced + text[end:]
    else:
        new = text + ("\n" if text and not text.endswith("\n") else "") + fenced
    if new == text:
        return "unchanged"
    target.write_text(new)
    return "wrote"


def cmd_install_agent(args) -> int:
    """Wire harnesses to the brain (MCP registration), one row each."""
    names = sorted(AGENT_TARGETS) if args.all else [args.harness]
    for name in names:
        if name not in AGENT_TARGETS:
            print(f"install-agent: unknown harness {name!r} "
                  f"(known: {', '.join(sorted(AGENT_TARGETS))})",
                  file=sys.stderr)
            return 2
        result = install_agent(name, REPO)
        print(f"  {'✓' if result == 'wrote' else '−'} {name}: "
              f"{AGENT_TARGETS[name]['path']} ({result})")
    print("\nAGENTS.md is the shared schema — every harness reads it "
          "(CLAUDE.md symlinks it for harnesses that want that name).")
    return 0


def cmd_doctor(args) -> int:
    """One-screen health checklist; the setup wizard's exit report."""
    checks = _doctor_checks()
    if getattr(args, "json", False):
        print(json.dumps(checks, indent=2))
    else:
        icon = {"ok": "✓", "warn": "−", "fail": "✗"}
        for c in checks:
            print(f"  {icon[c['status']]} {c['label']:<20} {c['detail']}")
            if c["hint"] and c["status"] != "ok":
                print(f"      fix: {c['hint']}")
        fails = sum(1 for c in checks if c["status"] == "fail")
        warns = sum(1 for c in checks if c["status"] == "warn")
        print(f"\n  {len(checks)} checks — {fails} failing, {warns} warning(s)")
    return 1 if any(c["status"] == "fail" for c in checks) else 0


INBOX_KINDS = {"ingest", "groom", "research", "custom"}
INBOX_PRIORITIES = {"high", "normal", "low"}


def _inbox_items() -> list[dict]:
    if not INBOX_DIR.exists():
        return []
    items = []
    for f in sorted(INBOX_DIR.glob("*.json")):
        try:
            items.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            print(f"inbox: skipping unparseable {f.name}", file=sys.stderr)
    return items


def _inbox_write(item: dict) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    path = INBOX_DIR / f"{item['id']}.json"
    path.write_text(json.dumps(item, indent=2) + "\n")
    return path


def inbox_add(id: str, kind: str, summary: str, route: str = "",
              priority: str = "normal", source: str = "",
              produced_by: str = "operator", update: bool = False) -> bool:
    """Add (or, with update=True, upsert) one inbox item.

    Returns True when the item was written, False when an item with
    the same id already exists and update is False — the dedup
    contract that makes producer re-runs idempotent.
    """
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", id):
        raise ValueError(f"inbox id must be a lowercase slug, got {id!r}")
    if kind not in INBOX_KINDS:
        raise ValueError(f"kind must be one of {sorted(INBOX_KINDS)}")
    if priority not in INBOX_PRIORITIES:
        raise ValueError(f"priority must be one of {sorted(INBOX_PRIORITIES)}")
    path = INBOX_DIR / f"{id}.json"
    if path.exists() and not update:
        return False
    item = {
        "id": id,
        "kind": kind,
        "summary": summary,
        "route": route,
        "priority": priority,
        "source": source,
        "produced_by": produced_by,
        "produced_at": today_utc().isoformat(),
    }
    if path.exists():
        # Preserve the original arrival date on upsert.
        try:
            item["produced_at"] = json.loads(path.read_text()).get(
                "produced_at", item["produced_at"])
        except json.JSONDecodeError:
            pass
    _inbox_write(item)
    return True


def cmd_inbox(args) -> int:
    """The tend queue at wiki/_state/inbox/ — one JSON file per item.

    The inbox is the seam between the deterministic accumulation loop
    (cron-run producers) and in-session digestion (the /tend skill).
    Subcommands:
      add      — queue an item; idempotent on --id unless --update.
      list     — pending items, priority-then-age ordered (--json).
      summary  — one line for session-start surfacing; always exits 0.
      done     — clear an item (the file's removal is git-audited).
    """
    op = args.op

    if op == "add":
        try:
            written = inbox_add(
                id=args.id, kind=args.kind, summary=args.summary,
                route=args.route or "", priority=args.priority,
                source=args.source or "",
                produced_by=args.produced_by or "operator",
                update=args.update,
            )
        except ValueError as exc:
            print(f"inbox add: {exc}", file=sys.stderr)
            return 2
        print(f"inbox: {'wrote' if written else 'exists (skipped)'} {args.id}")
        return 0

    if op == "list":
        items = _inbox_items()
        order = {"high": 0, "normal": 1, "low": 2}
        items.sort(key=lambda i: (order.get(i.get("priority"), 1),
                                  i.get("produced_at", ""), i.get("id", "")))
        if args.json:
            print(json.dumps(items, indent=2))
            return 0
        if not items:
            print("inbox: empty")
            return 0
        for i in items:
            route = f"  → {i['route']}" if i.get("route") else ""
            print(f"[{i.get('priority', 'normal'):>6}] {i.get('kind', '?'):>8}  "
                  f"{i['id']}  ({i.get('produced_at', '?')})\n"
                  f"         {i.get('summary', '')}{route}")
        return 0

    if op == "summary":
        items = _inbox_items()
        if not items:
            print("brain inbox: empty")
            return 0
        by_kind = collections.Counter(i.get("kind", "?") for i in items)
        parts = ", ".join(f"{n} {k}" for k, n in sorted(by_kind.items()))
        print(f"brain inbox: {len(items)} pending ({parts}) — run /tend to digest")
        return 0

    if op == "done":
        path = INBOX_DIR / f"{args.id}.json"
        if not path.exists():
            print(f"inbox done: no item {args.id!r}", file=sys.stderr)
            return 1
        path.unlink()
        print(f"inbox: cleared {args.id}")
        return 0

    if op == "judge":
        path = INBOX_DIR / f"{args.id}.json"
        if not path.exists():
            print(f"inbox judge: no item {args.id!r}", file=sys.stderr)
            return 1
        item = json.loads(path.read_text())
        item["attention"] = args.attention
        item["attention_reason"] = args.reason
        item["judged"] = today_utc().isoformat()
        path.write_text(json.dumps(item, indent=2) + "\n")
        print(f"inbox: judged {args.id} → {args.attention} ({args.reason})")
        return 0

    if op == "grade":
        grades = []
        if ATTENTION_GRADES_PATH.exists():
            grades = json.loads(ATTENTION_GRADES_PATH.read_text()).get(
                "grades", [])
        item_path = INBOX_DIR / f"{args.id}.json"
        verdict = None
        if item_path.exists():
            verdict = json.loads(item_path.read_text()).get("attention")
        grades.append({
            "id": args.id,
            "verdict": verdict,
            "grade": args.grade,
            "note": args.note or "",
            "graded": today_utc().isoformat(),
        })
        ATTENTION_GRADES_PATH.write_text(json.dumps(
            {"grades": grades}, indent=2) + "\n")
        print(f"inbox: graded {args.id} → {args.grade}"
              + (f" (verdict was {verdict})" if verdict else ""))
        return 0

    print(f"unknown inbox op: {op!r}", file=sys.stderr)
    return 2


def cmd_sync_cursor(args) -> int:
    """Manage per-sibling-repo sync cursors at wiki/_state/sync-cursors.json.

    Subcommands (via the `op` argument):
      get [<repo>]   — print the cursor for one repo, or all if omitted.
      set <repo>     — advance the cursor to the sibling repo's current
                       HEAD. Requires the sibling to be on its main branch
                       with a clean tree (per AGENTS.md § Sibling-repo
                       handling). Refuses if either rule is violated.
      diff <repo>    — list paths changed in the sibling repo since the
                       cursor's SHA. Output is one path per line, suitable
                       for piping into `git ls-files | grep -F -f -`.

    The cursor is the brain's record of "what was the last sibling-repo
    state we ingested?" — wiki-ingest skill protocol consults it before
    walking a sibling tree, so subsequent passes only process changed
    files instead of re-walking everything.
    """
    op = args.op
    data = _read_cursors()
    cursors = data.setdefault("cursors", {})

    if op == "get":
        if args.repo:
            entry = cursors.get(args.repo)
            if not entry:
                print(f"no cursor for {args.repo}", file=sys.stderr)
                return 1
            print(json.dumps(entry, indent=2))
        else:
            print(json.dumps(cursors, indent=2))
        return 0

    if op == "set":
        repo_path = _sibling_repo(args.repo)
        branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        if branch not in ("main", "master"):
            print(
                f"refusing to set cursor for {args.repo}: branch={branch!r} "
                "(sibling-repo handling rule requires main/master); use "
                "--force to override",
                file=sys.stderr,
            )
            if not getattr(args, "force", False):
                return 1
        dirty = subprocess.run(
            ["git", "diff", "--quiet"], cwd=repo_path
        ).returncode != 0 or subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=repo_path
        ).returncode != 0
        if dirty and not getattr(args, "force", False):
            print(
                f"refusing to set cursor for {args.repo}: working tree "
                "is dirty; commit/stash or pass --force",
                file=sys.stderr,
            )
            return 1
        sha = _git(["rev-parse", "HEAD"], repo_path)
        cursors[args.repo] = {
            "sha": sha,
            "branch": branch,
            "synced_at": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "tree_state": "dirty" if dirty else "clean",
            "scope": args.scope or "full-tree",
            "synced_by": args.synced_by or "(unspecified)",
        }
        _write_cursors(data)
        print(f"OK  {args.repo} cursor → {sha[:8]} (branch={branch})")
        return 0

    if op == "diff":
        repo_path = _sibling_repo(args.repo)
        entry = cursors.get(args.repo)
        if not entry:
            # No cursor — fall back to "everything", which we represent
            # as printing all tracked files. Caller decides what to do.
            paths = _git(["ls-files"], repo_path).splitlines()
            print(
                f"# no cursor for {args.repo} — first-pass ingest "
                f"({len(paths)} tracked files)",
                file=sys.stderr,
            )
            for p in paths:
                print(p)
            return 0
        cursor_sha = entry["sha"]
        # If the cursor SHA isn't reachable (rebase / force-push), fall
        # back to a full re-ingest with a loud warning.
        try:
            _git(["cat-file", "-e", cursor_sha], repo_path)
        except subprocess.CalledProcessError:
            print(
                f"WARN: cursor {cursor_sha[:8]} for {args.repo} not "
                "reachable in sibling repo (rebased? force-pushed?). "
                "Falling back to full-tree listing.",
                file=sys.stderr,
            )
            for p in _git(["ls-files"], repo_path).splitlines():
                print(p)
            return 0
        head_sha = _git(["rev-parse", "HEAD"], repo_path)
        if cursor_sha == head_sha:
            print(f"# {args.repo} is at cursor (no changes since "
                  f"{cursor_sha[:8]})", file=sys.stderr)
            return 0
        diff = _git(
            ["diff", "--name-only", f"{cursor_sha}..HEAD"], repo_path
        )
        for p in diff.splitlines():
            if p:
                print(p)
        return 0

    print(f"unknown sync-cursor op: {op!r}", file=sys.stderr)
    return 1


def _effort_path(slug: str) -> Path:
    return EFFORTS_DIR / f"{slug}.json"


def _read_effort(slug: str) -> dict | None:
    p = _effort_path(slug)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _write_effort(slug: str, record: dict) -> None:
    EFFORTS_DIR.mkdir(parents=True, exist_ok=True)
    record["updated"] = dt.datetime.now(dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    _effort_path(slug).write_text(json.dumps(record, indent=2) + "\n")


def _list_efforts() -> list[dict]:
    if not EFFORTS_DIR.exists():
        return []
    out = []
    for p in sorted(EFFORTS_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text()))
        except json.JSONDecodeError as e:
            print(f"# malformed effort record at {p}: {e}", file=sys.stderr)
    return out


def cmd_efforts(args) -> int:
    """Manage in-flight effort registry at wiki/_state/efforts/<slug>.json.

    Per-effort JSON files (one per file, never co-mingled) — see
    wiki/brain/adrs/parallel-efforts-on-request.md § Decision for
    the structural rationale.

    Subcommands:
      list                       — all efforts, optionally filtered.
      get <slug>                 — one effort's record as JSON.
      set <slug>                 — create/update a record (used by /spawn).
      mark <slug> <status>       — set status (in-flight | merged |
                                   abandoned | orphaned).
    """
    op = args.op

    if op == "list":
        records = _list_efforts()
        status_filter = getattr(args, "status", None)
        if status_filter:
            records = [r for r in records if r.get("status") == status_filter]
        as_json = getattr(args, "json", False)
        if as_json:
            print(json.dumps(records, indent=2))
            return 0
        if not records:
            print("# no efforts in registry", file=sys.stderr)
            return 0
        # human-readable table
        for r in records:
            slug = r.get("slug", "?")
            status = r.get("status", "?")
            brain_branch = r.get("brain_branch", "?")
            targets = ",".join(r.get("targets", [])) or "-"
            spawn = r.get("spawned_at", "?")
            owner_state = r.get("owner_state")
            owner_id = r.get("owner_agent_id")
            if owner_state == "none-dispatched":
                owner_cell = "none-dispatched"
            elif owner_state and owner_id:
                owner_cell = f"{owner_state}:{owner_id[:8]}"
            elif owner_state:
                owner_cell = owner_state
            else:
                owner_cell = "-"
            print(
                f"{slug}\t{status}\t{brain_branch}\t"
                f"targets={targets}\towner={owner_cell}\tspawned={spawn}"
            )
        return 0

    if op == "get":
        record = _read_effort(args.slug)
        if record is None:
            print(f"no effort record for {args.slug!r}", file=sys.stderr)
            return 1
        print(json.dumps(record, indent=2))
        return 0

    if op == "set":
        existing = _read_effort(args.slug) or {}
        record = dict(existing)
        record["slug"] = args.slug
        if args.brain_branch:
            record["brain_branch"] = args.brain_branch
        if args.brain_worktree:
            record["brain_worktree"] = args.brain_worktree
        if args.targets is not None:
            record["targets"] = args.targets
        if args.target_branches is not None:
            record["target_branches"] = dict(args.target_branches)
        if args.target_worktrees is not None:
            record["target_worktrees"] = dict(args.target_worktrees)
        if args.brain_pr:
            record["brain_pr"] = args.brain_pr
        if args.target_prs is not None:
            record["target_prs"] = dict(args.target_prs)
        if args.notes:
            record["notes"] = args.notes
        if args.status:
            record["status"] = args.status
        if args.owner_agent_id is not None:
            record["owner_agent_id"] = args.owner_agent_id
        if args.owner_dispatched_at is not None:
            record["owner_dispatched_at"] = args.owner_dispatched_at
        if args.owner_state is not None:
            record["owner_state"] = args.owner_state
        if args.helpers_dispatched is not None:
            record["helpers_dispatched"] = args.helpers_dispatched
        if "spawned_at" not in record:
            record["spawned_at"] = dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        record.setdefault("status", "in-flight")
        record.setdefault("targets", [])
        _write_effort(args.slug, record)
        print(json.dumps(record, indent=2))
        return 0

    if op == "mark":
        record = _read_effort(args.slug)
        if record is None:
            print(f"no effort record for {args.slug!r}", file=sys.stderr)
            return 1
        valid = {"in-flight", "merged", "abandoned", "orphaned"}
        if args.status not in valid:
            print(f"status must be one of {sorted(valid)}", file=sys.stderr)
            return 1
        record["status"] = args.status
        _write_effort(args.slug, record)
        print(json.dumps(record, indent=2))
        return 0

    print(f"unknown efforts op: {op!r}", file=sys.stderr)
    return 1


def cmd_rebase(args) -> int:
    """Cheap-rebase the current branch onto origin/main, regenerating
    deterministic auto-files (wiki/_views/) on conflict. Per
    wiki/brain/adrs/parallel-efforts-on-request.md § Decision.

    Steps:
      1. fetch origin
      2. rebase current branch on origin/main
      3. on wiki/_views/ conflict: regenerate via brain.py views and
         git add wiki/_views/, then git rebase --continue
      4. on wiki/index.md or other content conflict: stop and surface;
         the operator resolves by hand
      5. on success: report the rebased commit; force-push is the
         operator's separate step (per the verify-before-chain rule
         in feedback_force_push_verify_commit.md, /rebase deliberately
         does NOT chain the push)
    """
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], REPO)
    if branch in ("main", "master"):
        print(f"refusing to rebase {branch!r} onto origin/main", file=sys.stderr)
        return 1

    print(f"# fetching origin", file=sys.stderr)
    subprocess.run(["git", "fetch", "origin", "--prune"], cwd=REPO, check=True)

    base = args.base or "origin/main"
    print(f"# rebasing {branch} onto {base}", file=sys.stderr)
    rc = subprocess.run(["git", "rebase", base], cwd=REPO).returncode
    if rc == 0:
        head = _git(["rev-parse", "HEAD"], REPO)
        print(f"rebased clean to {head[:8]}", file=sys.stderr)
        print(head)
        return 0

    # rebase paused on conflict — try to auto-resolve wiki/_views/
    while True:
        unmerged = _git(["diff", "--name-only", "--diff-filter=U"], REPO).splitlines()
        if not unmerged:
            break
        views_only = all(p.startswith("wiki/_views/") for p in unmerged if p)
        if not views_only:
            print(
                "# rebase conflict in non-views paths — resolve by hand:",
                file=sys.stderr,
            )
            for p in unmerged:
                print(f"  {p}", file=sys.stderr)
            return 2
        print("# auto-resolving wiki/_views/ via brain.py views", file=sys.stderr)
        # accept theirs first, then regenerate against the merged tree
        for p in unmerged:
            subprocess.run(["git", "checkout", "--theirs", p], cwd=REPO, check=True)
        subprocess.run(
            [sys.executable, str(REPO / "tools" / "brain.py"), "views"],
            cwd=REPO, check=True,
        )
        subprocess.run(["git", "add", "wiki/_views/"], cwd=REPO, check=True)
        rc = subprocess.run(["git", "rebase", "--continue"],
                            cwd=REPO,
                            env={**os.environ, "GIT_EDITOR": "true"}
                            ).returncode
        if rc == 0:
            head = _git(["rev-parse", "HEAD"], REPO)
            print(f"rebased to {head[:8]} (views auto-regenerated)", file=sys.stderr)
            print(head)
            return 0
        # else continue loop — there may be more views conflicts in later commits

    head = _git(["rev-parse", "HEAD"], REPO)
    print(f"rebased to {head[:8]}", file=sys.stderr)
    print(head)
    return 0


BRAIN_HOOK_SCRIPT = '''#!/usr/bin/env bash
# brain:managed:hook version=1
# Pre-tool hook: surface relevant brain pages before sibling-repo source search.
# Installed by ~/projects/brain/tools/brain.py install-sibling.
#
# This file is regenerated by every install pass — if you want to customise,
# fork by removing the `brain:managed:hook` marker on line 1.

set -uo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty' 2>/dev/null)

case "$tool_name" in
  Grep|Glob|Read) ;;
  *) exit 0 ;;
esac

REPO="__REPO__"
BRAIN_DIR="${BRAIN_DIR:-$HOME/projects/brain}"

[ -d "$BRAIN_DIR/wiki/$REPO" ] || exit 0

pattern=$(echo "$input" | jq -r '
  .tool_input.pattern //
  .tool_input.glob //
  .tool_input.file_path //
  empty' 2>/dev/null)

[ -z "$pattern" ] && exit 0
[ "${#pattern}" -lt 4 ] && exit 0

if command -v python3 >/dev/null 2>&1; then
  match=$(timeout 0.5s python3 "$BRAIN_DIR/tools/brain.py" search "$pattern" \\
            --repo "$REPO" --top 1 --json 2>/dev/null \\
            | jq -r '.results[0].path // empty' 2>/dev/null)
  if [ -n "$match" ]; then
    cat >&2 <<EOF
[brain] $REPO has synthesis at: $BRAIN_DIR/$match
        Read it before scanning source — it may answer the question.
EOF
  fi
fi

exit 0
'''


MANAGED_BLOCK_TEMPLATE = '''<!-- brain:managed:start -->

## Brain — synthesis layer for this repo

This repo (`__REPO__`) is described and tracked in **`__BRAIN_DIR__`**, a
local LLM-maintained knowledge base. The brain holds the *why* and *how*
at a level the source alone doesn't surface — architecture, conventions,
decision history (ADRs), in-flight initiatives (PRDs), cross-product
overlaps.

### Read the brain BEFORE searching source

When asked about this repo's architecture, conventions, "why does X work
this way," or any feature spanning multiple files — read brain pages first.
Source code is the implementation; the brain explains the shape.

**Top entry points for `__REPO__`:**

__ENTRY_POINTS__

**Decisions and initiatives:**

- `__BRAIN_DIR__/wiki/__REPO__/adrs/` — accepted ADRs (kind: decision)
- `__BRAIN_DIR__/wiki/__REPO__/prds/` — committed PRDs (kind: initiative)
- `__BRAIN_DIR__/wiki/__REPO__/ai-suggestions/` — agent-authored drafts
  awaiting human review; **not** decisions, **not** product state

### Cross-product context

Decisions affecting multiple repos live at:

- `__BRAIN_DIR__/wiki/org/` — cross-cutting (auth / AI surfaces / CI /
  domain mapping / frontend stacks / runtime topology)
- `__BRAIN_DIR__/wiki/insights/` — patterns from feedback / observed work
- `__BRAIN_DIR__/wiki/_overlaps/` — surfaced cross-team duplications

### Querying the brain

If `python3 __BRAIN_DIR__/tools/brain.py search '<query>'` is available,
prefer it over manual file walks. It returns ranked pages with title,
kind, confidence, score, excerpt.

### When to write to the brain

The brain has its own write workflow — never edit `__BRAIN_DIR__/wiki/`
directly from this repo. Instead, `cd __BRAIN_DIR__` and use the brain's
slash commands (`/shape`, `/in`, `/capture`).

<!-- brain:managed:manifest version="1" repo="__REPO__" generated="__DATE__" -->
<!-- brain:managed:end -->
'''


def _list_entry_points(brain_dir: Path, repo: str) -> str:
    """Build the bullet list of brain entry points for the repo."""
    repo_dir = brain_dir / "wiki" / repo
    candidates = [
        ("index.md", "repo navigation hub"),
        ("permanent/architecture.md", "durable shape"),
        ("permanent/architecture/index.md", "durable shape (folder hub)"),
        ("permanent/conventions.md", "code style + idioms"),
        ("permanent/conventions/index.md", "code style + idioms (folder hub)"),
        ("permanent/interfaces.md", "external contracts"),
        ("permanent/interfaces/index.md", "external contracts (folder hub)"),
        ("permanent/domain.md", "vocabulary + entities"),
        ("permanent/purpose.md", "what this repo exists for"),
        ("state.md", "Now / Perceived / Target trajectory"),
    ]
    lines = []
    seen_purposes = set()
    for path, label in candidates:
        if (repo_dir / path).exists() and label not in seen_purposes:
            lines.append(f"- `{brain_dir}/wiki/{repo}/{path}` — {label}")
            # collapse duplicates (avoid both architecture.md and architecture/index.md)
            seen_purposes.add(label.split(" (")[0])
    if not lines:
        lines.append(
            f"- `{brain_dir}/wiki/{repo}/` — (skeleton; no top-level pages yet)"
        )
    return "\n".join(lines)


def cmd_install_sibling(args) -> int:
    """Install the brain's managed block + PreToolUse hook into a sibling repo.

    Per `wiki/brain/ai-suggestions/prds/sibling-repo-installer.md`.

    Idempotent: re-running updates the managed block in place. Operator-
    authored content outside the sentinel comments is never touched.

    With --uninstall, removes the managed block + hook script + settings
    entry, leaving operator-authored content intact.

    With --all, iterates every active sibling repo on disk (under
    $BRAIN_PROJECTS_ROOT, default ~/projects/).

    With --dry-run, prints what would be written without modifying disk.
    """
    if args.all_active:
        # Walk wiki/<repo>/ folders that have an active shelf; install if
        # the sibling repo is on disk, skip with a note otherwise.
        repos = []
        for child in sorted(WIKI.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("_") or child.name in {"org", "brain", "insights"}:
                continue
            if (child / "index.md").exists() and (PROJECTS / child.name).exists():
                repos.append(child.name)
        if not repos:
            print("no active sibling repos found on disk", file=sys.stderr)
            return 0
        rc = 0
        for repo in repos:
            print(f"\n--- {repo} ---", file=sys.stderr)
            args.repo = repo
            args.all_active = False
            r = cmd_install_sibling(args)
            if r != 0:
                rc = r
        return rc

    if not args.repo:
        print("repo argument required (or --all)", file=sys.stderr)
        return 2

    repo = args.repo
    sibling_root = PROJECTS / repo
    if not sibling_root.exists():
        print(f"sibling repo not found: {sibling_root}", file=sys.stderr)
        return 1
    if not (sibling_root / ".git").exists():
        print(f"warning: {sibling_root} has no .git directory", file=sys.stderr)

    brain_dir = REPO

    today = today_utc().isoformat()

    # Prefer CLAUDE.md, fall back to AGENTS.md, else create CLAUDE.md.
    claude_md = sibling_root / "CLAUDE.md"
    agents_md = sibling_root / "AGENTS.md"
    if claude_md.exists():
        target = claude_md
    elif agents_md.exists():
        target = agents_md
    else:
        target = claude_md

    # Render the managed block
    entry_points = _list_entry_points(brain_dir, repo)
    block = (
        MANAGED_BLOCK_TEMPLATE
        .replace("__REPO__", repo)
        .replace("__BRAIN_DIR__", str(brain_dir))
        .replace("__ENTRY_POINTS__", entry_points)
        .replace("__DATE__", today)
    )

    # Splice into the target file
    if args.uninstall:
        if not target.exists():
            print(f"nothing to uninstall: {target} does not exist", file=sys.stderr)
            return 0
        text = target.read_text()
        m = re.search(
            r"\n*<!-- brain:managed:start -->.*?<!-- brain:managed:end -->\n*",
            text, re.DOTALL,
        )
        if not m:
            print(f"no managed block found in {target}", file=sys.stderr)
            new_text = text
        else:
            new_text = text[:m.start()] + "\n" + text[m.end():]
            new_text = re.sub(r"\n{3,}", "\n\n", new_text)
        if args.dry_run:
            print(f"[dry-run] would update: {target}", file=sys.stderr)
        else:
            target.write_text(new_text)
            print(f"updated: {target} (managed block removed)", file=sys.stderr)
    else:
        text = target.read_text() if target.exists() else f"# {repo}\n\nSibling-repo Claude Code instructions. See managed block below.\n\n"
        if "<!-- brain:managed:start -->" in text:
            new_text = re.sub(
                r"<!-- brain:managed:start -->.*?<!-- brain:managed:end -->",
                block.strip(),
                text, count=1, flags=re.DOTALL,
            )
        else:
            new_text = text.rstrip() + "\n\n" + block + "\n"
        if args.dry_run:
            print(f"[dry-run] would update: {target}", file=sys.stderr)
        else:
            target.write_text(new_text)
            print(f"updated: {target}", file=sys.stderr)

    # Hook script
    claude_dir = sibling_root / ".claude"
    hook_path = claude_dir / "brain-hook.sh"
    if args.uninstall:
        if hook_path.exists():
            if args.dry_run:
                print(f"[dry-run] would remove: {hook_path}", file=sys.stderr)
            else:
                hook_path.unlink()
                print(f"removed: {hook_path}", file=sys.stderr)
    else:
        hook_content = BRAIN_HOOK_SCRIPT.replace("__REPO__", repo)
        if args.dry_run:
            print(f"[dry-run] would write: {hook_path}", file=sys.stderr)
        else:
            claude_dir.mkdir(exist_ok=True)
            hook_path.write_text(hook_content)
            os.chmod(hook_path, 0o755)
            print(f"wrote: {hook_path}", file=sys.stderr)

    # settings.json registration
    settings_path = claude_dir / "settings.json"
    if args.uninstall:
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                print(f"warning: {settings_path} unparseable; not modifying", file=sys.stderr)
                return 0
            hooks = (settings.get("hooks") or {}).get("PreToolUse") or []
            hooks_filtered = [
                h for h in hooks
                if not _entry_calls_brain_hook(h)
            ]
            if len(hooks_filtered) != len(hooks):
                if args.dry_run:
                    print(f"[dry-run] would update: {settings_path}", file=sys.stderr)
                else:
                    settings.setdefault("hooks", {})["PreToolUse"] = hooks_filtered
                    if not hooks_filtered:
                        settings["hooks"].pop("PreToolUse", None)
                        if not settings["hooks"]:
                            settings.pop("hooks", None)
                    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
                    print(f"updated: {settings_path} (hook entry removed)", file=sys.stderr)
    else:
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                print(f"warning: {settings_path} unparseable; refusing to modify", file=sys.stderr)
                return 1
        else:
            settings = {}
        hooks_section = settings.setdefault("hooks", {})
        pre_hooks = hooks_section.setdefault("PreToolUse", [])
        already = any(_entry_calls_brain_hook(h) for h in pre_hooks)
        if not already:
            pre_hooks.append({
                "matcher": "Grep|Glob|Read",
                "hooks": [
                    {
                        "type": "command",
                        "command": str(hook_path),
                    }
                ],
            })
            if args.dry_run:
                print(f"[dry-run] would update: {settings_path}", file=sys.stderr)
            else:
                claude_dir.mkdir(exist_ok=True)
                settings_path.write_text(json.dumps(settings, indent=2) + "\n")
                print(f"updated: {settings_path} (hook entry added)", file=sys.stderr)
        else:
            print(f"already registered: {settings_path}", file=sys.stderr)

    return 0


def cmd_verify_claims(args) -> int:
    """Extract verifiable claims from a wiki page + emit a structured
    manifest the consumer (agent / operator / LLM) can verify against
    the cited sibling-repo source.

    open question §4 + the operator's 2026-05-08 directive on brain↔repo
    semantic verification.

    Three claim types extracted:

    1. **Path claims** — `~/projects/<repo>/<path>` references with
       optional `:<line>` or `:<line>-<line>` suffixes. Mechanical
       check: file exists; line range valid.
    2. **Version-pin claims** — patterns like `Pundit 2.5.2`,
       `Rails 8.1.3`, `Bun 1.0`. Mechanical check: defer (would need
       per-language manifest parsing); flagged for LLM grounding.
    3. **Identifier claims** — backticked tokens that look like
       class / module / function names appearing alongside a cited
       file path. Flagged for LLM verification.

    Output: JSON manifest with one entry per claim + a status:
    `verified` (mechanical pass) / `failed` (mechanical fail) /
    `needs-verification` (semantic — agent / LLM must read the cited
    file and judge). The LLM verifier reads the manifest, opens each
    cited file with the Read tool, and updates the status.

    The consumer runs:
        python3 tools/brain.py verify-claims <page> --json > manifest.json
        # then an LLM agent reads manifest.json, opens each cited file,
        # and produces a verified/failed verdict per claim.
    """
    page = args.page
    abs_page = (WIKI / page).resolve()
    try:
        abs_page.relative_to(WIKI)
    except ValueError:
        print(f"path escapes wiki/: {page}", file=sys.stderr)
        return 2
    if not abs_page.exists():
        print(f"page not found: {page}", file=sys.stderr)
        return 2

    parsed = parse(abs_page)
    if parsed is None:
        print(f"page has no parseable frontmatter: {page}", file=sys.stderr)
        return 2
    meta, body = parsed

    claims: list[dict] = []
    seen: set[tuple] = set()

    # Path claims with optional :line suffix.
    # Lookahead deliberately excludes `.` so file extensions like
    # `.md`/`.rb`/`.ts` aren't truncated. Sentence-end periods get
    # captured into the path; that's a heuristic-acceptable edge case
    # — the path-existence check normalises by stripping trailing
    # punctuation before resolving.
    path_rx = re.compile(
        r"~/projects/([\w-]+)/([\w./_-]+?)(?::(\d+)(?:-(\d+))?)?(?=[\s`)\],]|$)",
        re.MULTILINE,
    )
    for m in path_rx.finditer(body):
        repo = m.group(1)
        rel_path = m.group(2).rstrip(".,")  # strip trailing sentence punctuation
        line_start = int(m.group(3)) if m.group(3) else None
        line_end = int(m.group(4)) if m.group(4) else None
        key = ("path", repo, rel_path, line_start, line_end)
        if key in seen:
            continue
        seen.add(key)
        # Capture surrounding context (~80 chars on each side)
        ctx_start = max(0, m.start() - 80)
        ctx_end = min(len(body), m.end() + 80)
        context = body[ctx_start:ctx_end].replace("\n", " ").strip()
        # Mechanical check
        sibling = PROJECTS / repo
        status = "needs-verification"
        mechanical = {}
        if not sibling.exists():
            mechanical["sibling_on_disk"] = False
            status = "needs-verification"
        else:
            mechanical["sibling_on_disk"] = True
            target = sibling / rel_path
            mechanical["file_exists"] = target.exists()
            if not target.exists():
                status = "failed"
            else:
                if line_start is not None:
                    try:
                        line_count = sum(1 for _ in target.open())
                        mechanical["file_line_count"] = line_count
                        in_range = line_start <= line_count and (
                            line_end is None or line_end <= line_count
                        )
                        mechanical["lines_in_range"] = in_range
                        if not in_range:
                            status = "failed"
                        else:
                            status = "needs-verification"
                    except (OSError, UnicodeDecodeError):
                        mechanical["file_line_count"] = "(unreadable)"
                        status = "needs-verification"
                else:
                    status = "needs-verification"
        claims.append({
            "type": "path",
            "claim": m.group(0),
            "repo": repo,
            "rel_path": rel_path,
            "line_start": line_start,
            "line_end": line_end,
            "context": context,
            "mechanical": mechanical,
            "status": status,
        })

    # Version-pin claims (Title-cased identifier + space + version-like)
    version_rx = re.compile(
        r"\b([A-Z][\w]{2,})\s+(\d+\.\d+(?:\.\d+)?(?:[a-z]\d+)?)\b"
    )
    for m in version_rx.finditer(body):
        name = m.group(1)
        version = m.group(2)
        # Skip non-software-name false positives (heuristic)
        if name in {"At", "On", "By", "For", "Per", "The", "Section", "Article",
                    "Chapter", "Phase", "Step", "Option", "Ruby"}:
            # "Ruby 4.0.1" is a real claim, but it's already commonly
            # captured at the gemfile-lock level; the false-positive on
            # the word alone is the concern. Drop common short words.
            if name not in {"Ruby"}:
                continue
        key = ("version", name, version)
        if key in seen:
            continue
        seen.add(key)
        ctx_start = max(0, m.start() - 80)
        ctx_end = min(len(body), m.end() + 80)
        context = body[ctx_start:ctx_end].replace("\n", " ").strip()
        claims.append({
            "type": "version-pin",
            "claim": m.group(0),
            "name": name,
            "version": version,
            "context": context,
            "mechanical": {"reason": "version-pin requires manifest-walk verification"},
            "status": "needs-verification",
        })

    # Identifier claims — backticked code-shaped tokens within ~120
    # chars of a path claim. These are most likely class/module/method
    # names worth verifying via Grep/Read.
    if claims:  # only if we found path claims
        path_indices = [(c["context"], c["repo"], c["rel_path"])
                        for c in claims if c["type"] == "path"]
        ident_rx = re.compile(r"`([A-Z][\w]+(?:::[A-Z][\w]+)*|[a-z_][\w]+(?:#[\w_]+)?)`")
        for context, repo, rel in path_indices[:50]:  # cap to avoid combinatorial blowup
            for m in ident_rx.finditer(context):
                ident = m.group(1)
                if ident in {"AGENTS.md", "CLAUDE.md", "README.md"}:
                    continue
                key = ("ident", repo, rel, ident)
                if key in seen:
                    continue
                seen.add(key)
                claims.append({
                    "type": "identifier",
                    "claim": ident,
                    "near_path": f"~/projects/{repo}/{rel}",
                    "context": context[:200],
                    "mechanical": {"reason": "identifier verification requires Read/Grep"},
                    "status": "needs-verification",
                })

    summary = {
        "page": page,
        "title": meta.get("title", ""),
        "kind": meta.get("kind"),
        "status": meta.get("status"),
        "confidence": meta.get("confidence"),
        "updated": str(meta.get("updated", "")),
        "extracted_at": today_utc().isoformat(),
        "claim_count": len(claims),
        "by_status": {
            "verified": sum(1 for c in claims if c["status"] == "verified"),
            "failed": sum(1 for c in claims if c["status"] == "failed"),
            "needs-verification": sum(1 for c in claims if c["status"] == "needs-verification"),
        },
        "by_type": {
            t: sum(1 for c in claims if c["type"] == t)
            for t in ("path", "version-pin", "identifier")
        },
        "claims": claims,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"# Verify claims — {page}")
        print(f"Title: {meta.get('title', '')}")
        print(f"Kind: {meta.get('kind')}; status: {meta.get('status')}; "
              f"confidence: {meta.get('confidence')}")
        print(f"Extracted {summary['claim_count']} claim(s):")
        print(f"  by status: {summary['by_status']}")
        print(f"  by type:   {summary['by_type']}")
        print()
        for c in claims:
            marker = {"verified": "✓", "failed": "✗", "needs-verification": "?"}[c["status"]]
            print(f"  {marker} [{c['type']}] {c['claim']}")
            if c["status"] == "failed":
                print(f"      ✗ {c['mechanical']}")
        print()
        print("(Re-run with --json for the full structured manifest. "
              "Hand the JSON to an LLM agent to verify "
              "`needs-verification` claims by reading each cited file.)")
    return 0 if all(c["status"] != "failed" for c in claims) else 1


def cmd_status(_args) -> int:
    """Brain-wide status dashboard.

    Reads every wiki/_state/*.json + computes corpus stats; surfaces
    one-line health line per dimension (security / deadlines /
    issues / sync / reflection / efforts).

    """
    state_dir = WIKI / "_state"
    today = today_utc()

    print(f"# Brain status — {today.isoformat()}")
    print()

    # Corpus
    pages = wiki_pages()
    by_kind = collections.Counter()
    by_status = collections.Counter()
    by_confidence = collections.Counter()
    for p in pages:
        parsed = parse(p)
        if parsed:
            meta = parsed[0]
            by_kind[meta.get("kind", "?")] += 1
            by_status[meta.get("status", "?")] += 1
            by_confidence[meta.get("confidence", "?")] += 1
    print(f"corpus: {len(pages)} pages")
    print(f"  by kind: " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    print(f"  by status: " + ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    print(f"  by confidence: " + ", ".join(f"{k}={v}" for k, v in sorted(by_confidence.items())))
    print()

    # Security
    sec_path = state_dir / "security.json"
    if sec_path.exists():
        try:
            sec = json.loads(sec_path.read_text())
            sweep = sec.get("last_full_sweep") or "(never)"
            scanned = sum(1 for r in sec.get("repos", {}).values() if r.get("last_scan"))
            total = len(sec.get("repos", {}))
            print(f"security: last full sweep = {sweep}; {scanned}/{total} repos scanned")
            if scanned == 0:
                print(f"  (bootstrap pending — run `brain.py schedule run --target security-scan`)")
        except json.JSONDecodeError:
            print(f"security: wiki/_state/security.json unparseable")
    else:
        print("security: wiki/_state/security.json absent")
    print()

    # Deadlines — named external dates the org tracks (compliance
    # dates, contract renewals, launch commitments). Optional surface:
    # an absent file means the org tracks none.
    dl_path = state_dir / "deadlines.json"
    if dl_path.exists():
        try:
            dl = json.loads(dl_path.read_text())
            entries = dl.get("deadlines", [])
            print(f"deadlines: {len(entries)} tracked; "
                  f"last assessment: {dl.get('last_assessment', '(never)')}")
            for entry in sorted(entries, key=lambda e: e.get("date", "")):
                date = dt.date.fromisoformat(entry["date"])
                days_left = (date - today).days
                readiness = entry.get("readiness", "")
                suffix = f", readiness {readiness}" if readiness else ""
                print(f"  {entry.get('name', '(unnamed)')}: "
                      f"{date.isoformat()} ({days_left} days{suffix})")
        except (json.JSONDecodeError, ValueError, KeyError):
            print(f"deadlines: wiki/_state/deadlines.json unparseable")
    else:
        print("deadlines: wiki/_state/deadlines.json absent (none tracked)")
    print()

    # Issues
    iss_path = state_dir / "issues.json"
    if iss_path.exists():
        try:
            iss = json.loads(iss_path.read_text())
            pull = iss.get("last_pull") or "(never)"
            populated = sum(1 for r in iss.get("repos", {}).values() if r.get("last_pull"))
            total = len(iss.get("repos", {}))
            print(f"issues: last pull = {pull}; {populated}/{total} repos populated")
        except json.JSONDecodeError:
            print(f"issues: wiki/_state/issues.json unparseable")
    else:
        print("issues: wiki/_state/issues.json absent")
    print()

    # Sync cursors
    cursor_path = SYNC_CURSORS
    if cursor_path.exists():
        try:
            cursors = json.loads(cursor_path.read_text())
            data = cursors.get("cursors") or cursors
            print(f"sync-cursors: {len(data)} sibling repos tracked")
        except json.JSONDecodeError:
            print(f"sync-cursors: unparseable")
    else:
        print("sync-cursors: absent")

    # Efforts
    if EFFORTS_DIR.exists():
        records = list(EFFORTS_DIR.glob("*.json"))
        print(f"efforts: {len(records)} records in wiki/_state/efforts/")
    else:
        print("efforts: directory absent")

    # AI-suggestions backlog
    ai_dirs = list(WIKI.glob("**/ai-suggestions/*/"))
    ai_files = []
    for d in ai_dirs:
        ai_files.extend(d.glob("*.md"))
    suggested = sum(1 for f in ai_files
                    if (parse(f) or ({},))[0].get("status") == "suggested")
    superseded = sum(1 for f in ai_files
                     if (parse(f) or ({},))[0].get("status") == "superseded")
    print(f"ai-suggestions: {suggested} pending review, {superseded} graduated")
    print()

    print("# Reflection-check (run `brain.py reflection-check` for detail)")
    return 0


def _schedule_run_security_scan() -> int:
    """Manifest-walk inventory across sibling repos.

    Scanner = "manifest-walk" — counts dependency entries in
    `Gemfile.lock`, `package.json`, `requirements.txt`,
    `Cargo.toml`, `go.mod`. Does NOT do CVE checking
    (`bundle audit` / `npm audit` / `trivy` are separate
    follow-ups). Records inventory + last_scan timestamp.
    """
    state_path = WIKI / "_state" / "security.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"_schema": "v1", "repos": {}}
    # Bootstrap the repo map from the registry so the op is
    # config-driven on a fresh shell; repos added to brain.config.yml
    # later join the map on the next run.
    for repo in sorted(ACTIVE_REPOS):
        state.setdefault("repos", {}).setdefault(repo, {})
    if not state.get("repos"):
        print("security-scan: no active repos declared in brain.config.yml "
              "— nothing to scan")
        return 0
    today = today_utc().isoformat()
    scanned = 0
    for repo, entry in state.get("repos", {}).items():
        sibling = PROJECTS / repo
        if not sibling.exists():
            entry["notes"] = f"(skipped — repo not on disk at {sibling})"
            continue
        manifests = {
            "Gemfile.lock": _count_gemfile_lock,
            "package.json": _count_package_json,
            "package-lock.json": _count_package_lock,
            "requirements.txt": _count_requirements,
            "Cargo.toml": _count_cargo,
            "go.mod": _count_go_mod,
        }
        inventory = {}
        for filename, counter in manifests.items():
            target = sibling / filename
            if target.exists():
                try:
                    inventory[filename] = counter(target)
                except Exception as exc:
                    inventory[filename] = f"(parse error: {exc})"
        entry["last_scan"] = today
        entry["scanner"] = "manifest-walk"
        entry["findings"] = {"critical": 0, "high": 0, "medium": 0, "low": 0,
                             "_note": "inventory only; CVE check not run"}
        entry["inventory"] = inventory
        entry["notes"] = (
            f"manifest-walk scanned {len(inventory)} files; "
            f"CVE check requires `bundle audit` / `npm audit` / `trivy` "
            f"(follow-up)."
        )
        scanned += 1
    state["last_full_sweep"] = today
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print(f"security-scan: scanned {scanned} repo(s); wrote {state_path.relative_to(REPO)}")
    return 0


def _count_gemfile_lock(p: Path) -> int:
    """Count top-level gem entries across all GIT / PATH / GEM
    `specs:` blocks. Top-level gems are 4-space-indented `name
    (version)` lines; transitive deps live at 6-space indent."""
    n = 0
    in_specs = False
    rx = re.compile(r"^    [\w.-]+ \(.+\)$")
    for line in p.read_text().splitlines():
        if line.strip() == "specs:":
            in_specs = True
            continue
        if line and not line.startswith(" "):
            in_specs = False
            continue
        if in_specs and rx.match(line):
            n += 1
    return n


def _count_package_json(p: Path) -> int:
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        return -1
    return (
        len(data.get("dependencies") or {})
        + len(data.get("devDependencies") or {})
        + len(data.get("peerDependencies") or {})
    )


def _count_package_lock(p: Path) -> int:
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        return -1
    return len(data.get("packages") or data.get("dependencies") or {})


def _count_requirements(p: Path) -> int:
    n = 0
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            n += 1
    return n


def _count_cargo(p: Path) -> int:
    n = 0
    in_deps = False
    for line in p.read_text().splitlines():
        line = line.strip()
        if line.startswith("[dependencies]") or line.startswith("[dev-dependencies]"):
            in_deps = True
            continue
        if line.startswith("["):
            in_deps = False
            continue
        if in_deps and "=" in line and not line.startswith("#"):
            n += 1
    return n


def _count_go_mod(p: Path) -> int:
    n = 0
    in_require = False
    for line in p.read_text().splitlines():
        s = line.strip()
        if s.startswith("require ("):
            in_require = True
            continue
        if in_require and s == ")":
            in_require = False
            continue
        if in_require and s and not s.startswith("//"):
            n += 1
        elif s.startswith("require ") and "(" not in s:
            n += 1
    return n


# --- derived index (composable views) ------------------------------------
#
# Per wiki/brain/adrs/sql-views-over-derived-index.md: one disposable
# SQLite index over the three data planes, rebuilt deterministically
# from files on every views regeneration. Gitignored; single writer
# (this indexer); every consumer opens read-only. Delete-and-rebuild
# is always safe — files are the only source of truth.

INDEX_DB = WIKI / "_views" / "index.db"

INDEX_SCHEMA_DOC = """\
# Derived index schema (wiki/_views/index.db — gitignored, disposable)
#
# pages(path PK, title, kind, status, confidence, updated, team,
#       tokens, repos JSON, affects JSON, body)
#   -- every wiki page outside _-folders; repos/affects are JSON
#      arrays: use json_each(pages.repos)
# links(src, dst)          -- resolved wiki-internal markdown links
# inbox(id PK, kind, priority, summary, route, source,
#       produced_by, produced_at)
# state(surface, key, value)  -- wiki/_state/*.json flattened;
#                                value is JSON text
# snapshots(path PK, connector, title, pulled, meta JSON, body)
#   -- sources/** files with frontmatter; connector = first folder
# pages_fts, snapshots_fts  -- FTS5 (title, body); query via
#   MATCH + ORDER BY rank (ascending); quote user tokens.
"""


def _fts_quote(query: str) -> str:
    """Neutralise FTS5 MATCH syntax: quote each whitespace token."""
    tokens = [t.replace('"', '""') for t in query.split()]
    return " ".join(f'"{t}"' for t in tokens)


def _build_index() -> dict:
    """Rebuild the derived index atomically; returns build stats."""
    import sqlite3
    tmp = INDEX_DB.with_suffix(".db.tmp")
    tmp.unlink(missing_ok=True)
    INDEX_DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(tmp)
    db.executescript("""
    PRAGMA synchronous=OFF; PRAGMA journal_mode=MEMORY;
    CREATE TABLE pages(path TEXT PRIMARY KEY, title TEXT, kind TEXT,
      status TEXT, confidence TEXT, updated TEXT, team TEXT,
      tokens INTEGER, repos TEXT, affects TEXT, body TEXT);
    CREATE TABLE links(src TEXT, dst TEXT, PRIMARY KEY(src, dst));
    CREATE INDEX links_dst ON links(dst);
    CREATE TABLE inbox(id TEXT PRIMARY KEY, kind TEXT, priority TEXT,
      summary TEXT, route TEXT, source TEXT, produced_by TEXT,
      produced_at TEXT);
    CREATE TABLE state(surface TEXT, key TEXT, value TEXT);
    CREATE TABLE snapshots(path TEXT PRIMARY KEY, connector TEXT,
      title TEXT, pulled TEXT, meta TEXT, body TEXT);
    CREATE VIRTUAL TABLE pages_fts USING fts5(title, body,
      content='pages', content_rowid='rowid',
      tokenize="unicode61 tokenchars '-_'");
    CREATE VIRTUAL TABLE snapshots_fts USING fts5(title, body,
      content='snapshots', content_rowid='rowid',
      tokenize="unicode61 tokenchars '-_'");
    """)

    n_pages = 0
    with db:
        for p in wiki_pages():
            parsed = parse(p)
            if parsed is None:
                continue
            meta, body = parsed
            db.execute(
                "INSERT INTO pages VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (str(p.relative_to(WIKI)), str(meta.get("title", "")),
                 meta.get("kind"), meta.get("status"),
                 meta.get("confidence"), str(meta.get("updated", "")),
                 meta.get("team"), approx_tokens(body),
                 json.dumps(meta.get("repos") or []),
                 json.dumps(meta.get("affects") or []), body))
            n_pages += 1

        outbound, _inbound = _link_graph()
        db.executemany("INSERT OR IGNORE INTO links VALUES(?,?)",
                       [(s, d) for s, ds in outbound.items() for d in ds])

        for item in _inbox_items():
            db.execute("INSERT OR REPLACE INTO inbox VALUES(?,?,?,?,?,?,?,?)",
                       (item.get("id"), item.get("kind"),
                        item.get("priority"), item.get("summary"),
                        item.get("route"), item.get("source"),
                        item.get("produced_by"), item.get("produced_at")))

        for f in sorted((WIKI / "_state").glob("*.json")):
            try:
                data = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                db.executemany(
                    "INSERT INTO state VALUES(?,?,?)",
                    [(f.stem, k, json.dumps(v)) for k, v in data.items()])

        n_snaps = 0
        sources_dir = REPO / "sources"
        if sources_dir.exists():
            for f in sorted(sources_dir.rglob("*.md")):
                if f.name == "README.md":
                    continue
                parsed = parse(f)
                if parsed is None:
                    continue
                meta, body = parsed
                rel = f.relative_to(sources_dir)
                db.execute(
                    "INSERT OR REPLACE INTO snapshots VALUES(?,?,?,?,?,?)",
                    (str(rel), rel.parts[0], str(meta.get("title", "")),
                     str(meta.get("pulled") or meta.get("captured") or ""),
                     json.dumps({k: str(v) for k, v in meta.items()}),
                     body))
                n_snaps += 1

        db.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
        db.execute("INSERT INTO snapshots_fts(snapshots_fts) VALUES('rebuild')")

    db.close()
    os.replace(tmp, INDEX_DB)
    return {"pages": n_pages, "snapshots": n_snaps,
            "size_kb": INDEX_DB.stat().st_size // 1024}


def _index_connect():
    """Read-only connection; None when no index has been built yet."""
    import sqlite3
    if not INDEX_DB.exists():
        return None
    return sqlite3.connect(f"file:{INDEX_DB}?mode=ro", uri=True)


def cmd_index(args) -> int:
    """Rebuild the derived index (also happens on every `views` run)."""
    if getattr(args, "schema", False):
        print(INDEX_SCHEMA_DOC)
        return 0
    stats = _build_index()
    print(f"index: {stats['pages']} pages, {stats['snapshots']} snapshots "
          f"→ {INDEX_DB.relative_to(REPO)} ({stats['size_kb']} KB)")
    return 0


def cmd_query(args) -> int:
    """Run one read-only SQL statement against the derived index."""
    db = _index_connect()
    if db is None:
        print("query: no index yet — run `brain.py index` first",
              file=sys.stderr)
        return 1
    try:
        cur = db.execute(args.sql)
    except Exception as exc:
        print(f"query: {exc}", file=sys.stderr)
        print("(schema: `brain.py index --schema`)", file=sys.stderr)
        return 1
    rows = cur.fetchmany(args.limit)
    cols = [d[0] for d in cur.description or []]
    if getattr(args, "json", False):
        print(json.dumps([dict(zip(cols, r)) for r in rows],
                         indent=2, default=str))
    else:
        if cols:
            print("  " + " | ".join(cols))
        for r in rows:
            print("  " + " | ".join(str(v) for v in r))
        print(f"  ({len(rows)} row(s))", file=sys.stderr)
    return 0


# --- composable view specs ------------------------------------------------

VIEWS_SPEC_DIR = REPO / "views"
CUSTOM_VIEWS_DIR = WIKI / "_views" / "custom"


def _compile_block(block: dict) -> tuple[str, list]:
    """One spec block → (sql, params). Raw `sql:` is the full tier;
    the shorthands (`pages:`, `state:`, `inbox:`) compile to SQL —
    never bypass it (per the sql-views-over-derived-index ADR)."""
    if block.get("sql"):
        return block["sql"], []
    if "pages" in block:
        f = block["pages"] or {}
        where, params = [], []
        for field in ("kind", "status", "confidence"):
            if f.get(field):
                where.append(f"{field} = ?")
                params.append(f[field])
        if f.get("repo"):
            where.append(
                "EXISTS (SELECT 1 FROM json_each(pages.repos) "
                "WHERE json_each.value = ?)")
            params.append(f["repo"])
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        return (f"SELECT path, title, status, confidence, updated "
                f"FROM pages{clause} ORDER BY updated DESC, path", params)
    if "state" in block:
        return ("SELECT key, value FROM state WHERE surface = ? "
                "ORDER BY key", [block["state"]])
    if "inbox" in block:
        f = block["inbox"] or {}
        if isinstance(f, str):
            f = {"kind": f}
        where, params = [], []
        if f.get("kind"):
            where.append("kind = ?")
            params.append(f["kind"])
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        return (f"SELECT id, kind, priority, summary FROM inbox{clause} "
                f"ORDER BY CASE priority WHEN 'high' THEN 0 "
                f"WHEN 'normal' THEN 1 ELSE 2 END, produced_at, id", params)
    raise ValueError(
        f"block {block.get('title', '?')!r} needs one of: sql, pages, "
        f"state, inbox")


def _render_rows(cols: list[str], rows: list) -> str:
    if not rows:
        return "*(no rows)*\n"
    def esc(v) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")[:120]
    if len(cols) == 1:
        return "".join(f"- {esc(r[0])}\n" for r in rows)
    out = "| " + " | ".join(cols) + " |\n"
    out += "|" + "---|" * len(cols) + "\n"
    for r in rows:
        out += "| " + " | ".join(esc(v) for v in r) + " |\n"
    return out


def _render_custom_views() -> list[str]:
    """Render every spec in views/ to wiki/_views/custom/<name>.md.
    Deterministic: specs must ORDER BY; rows are capped per block."""
    if not VIEWS_SPEC_DIR.exists():
        return []
    specs = sorted(VIEWS_SPEC_DIR.glob("*.yml")) + sorted(
        VIEWS_SPEC_DIR.glob("*.yaml"))
    if not specs:
        return []
    db = _index_connect()
    if db is None:
        _build_index()
        db = _index_connect()
    rendered = []
    CUSTOM_VIEWS_DIR.mkdir(parents=True, exist_ok=True)
    for spec_path in specs:
        try:
            spec = yaml.safe_load(spec_path.read_text()) or {}
        except yaml.YAMLError as exc:
            print(f"views: skipping {spec_path.name}: {exc}", file=sys.stderr)
            continue
        name = spec_path.stem
        parts = [
            "---",
            f'title: "{spec.get("title", name)}"',
            "kind: meta",
            "status: living",
            f"updated: {today_utc().isoformat()}",
            "confidence: high",
            "sources:",
            f"  - ../../../views/{spec_path.name}",
            "---",
            "",
            f"# {spec.get('title', name)}",
            "",
            f"Auto-generated by `brain.py views` from "
            f"`views/{spec_path.name}` — edit the spec, not this page."
            + (f" Audience: {spec['audience']}."
               if spec.get("audience") else ""),
            "",
        ]
        if spec.get("description"):
            parts += [spec["description"], ""]
        for block in spec.get("blocks") or []:
            parts.append(f"## {block.get('title', '(untitled block)')}")
            parts.append("")
            try:
                sql, params = _compile_block(block)
                cur = db.execute(sql, params)
                rows = cur.fetchmany(int(block.get("limit", 20)))
                cols = [d[0] for d in cur.description or []]
                parts.append(_render_rows(cols, rows))
            except Exception as exc:
                parts.append(f"*(block error: {exc})*\n")
        out = CUSTOM_VIEWS_DIR / f"{name}.md"
        out.write_text("\n".join(parts))
        rendered.append(name)
    return rendered


# --- link graph (0.4) — pruning + deepening inputs -----------------------

# Stale thresholds (days) per page kind — the groom skill's half-life
# table, "Stale" column. Kinds not listed use the reference default.
HALF_LIFE_STALE_DAYS = {
    "reference": 180, "initiative": 60, "decision": 730,
    "entity": 365, "insight": 90, "overlap": 120,
}


def _link_graph() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(outbound, inbound) maps over wiki pages, keyed by
    wiki-relative path. Edges are resolved relative markdown links;
    tooling folders (_views etc.) are excluded on both sides."""
    outbound: dict[str, set[str]] = {}
    inbound: dict[str, set[str]] = {}
    for page in WIKI.rglob("*.md"):
        rel = page.relative_to(WIKI)
        if any(part.startswith("_") for part in rel.parts):
            continue
        rel_s = str(rel)
        outbound.setdefault(rel_s, set())
        inbound.setdefault(rel_s, set())
    for rel_s in list(outbound):
        page = WIKI / rel_s
        for href in re.findall(r"\]\(([^)]+)\)", page.read_text()):
            href = href.split("#", 1)[0].strip()
            if (not href or not href.endswith(".md")
                    or href.startswith(("http://", "https://", "mailto:", "~/"))):
                continue
            target = (page.parent / href).resolve()
            try:
                target_rel = str(target.relative_to(WIKI))
            except ValueError:
                continue
            if target_rel in outbound and target_rel != rel_s:
                outbound[rel_s].add(target_rel)
                inbound[target_rel].add(rel_s)
    return outbound, inbound


def page_context(rel: str) -> dict:
    """Graph context for one wiki page — the open-knowledge lesson
    that every read should be a briefing: backlinks, outbound links,
    computed reverse edges, and recent audit-log lines that mention
    the page. Used by `brain.py page`, the MCP get_page tool, and
    anything else that reads pages for an agent."""
    outbound, inbound = _link_graph()
    ctx = {
        "backlinks": sorted(inbound.get(rel, ())),
        "outbound": sorted(outbound.get(rel, ())),
        "affected_by": [], "consumed_by": [], "recent_log": [],
    }
    pages_json = WIKI / "_views" / "pages.json"
    if pages_json.exists():
        try:
            data = json.loads(pages_json.read_text())
            for entry in data.get("pages", []):
                if entry.get("path") == rel:
                    ctx["affected_by"] = entry.get("affected_by", [])
                    ctx["consumed_by"] = entry.get("consumed_by", [])
                    break
        except json.JSONDecodeError:
            pass
    log_path = REPO / "log" / "log.md"
    if log_path.exists():
        slug = Path(rel).stem
        ctx["recent_log"] = [
            line.strip() for line in
            log_path.read_text().splitlines()[-200:]
            if slug in line][-5:]
    return ctx


def render_page_context(rel: str) -> str:
    ctx = page_context(rel)
    lines = [f"<!-- graph context for {rel} -->"]
    if ctx["backlinks"]:
        lines.append("backlinks: " + ", ".join(ctx["backlinks"]))
    if ctx["outbound"]:
        lines.append("links to: " + ", ".join(ctx["outbound"]))
    if ctx["affected_by"]:
        lines.append("affected by: " + ", ".join(ctx["affected_by"]))
    if ctx["consumed_by"]:
        lines.append("consumed by: " + ", ".join(ctx["consumed_by"]))
    if ctx["recent_log"]:
        lines.append("recent activity:")
        lines.extend(f"  {ln}" for ln in ctx["recent_log"])
    if len(lines) == 1:
        lines.append("(no inbound/outbound edges recorded)")
    return "\n".join(lines)


def cmd_page(args) -> int:
    """Read one page WITH its graph context — a briefing, not a cat."""
    rel = args.path
    target = (WIKI / rel).resolve()
    try:
        target.relative_to(WIKI)
    except ValueError:
        print(f"page: path escapes wiki/: {rel}", file=sys.stderr)
        return 2
    if not target.exists():
        print(f"page: not found: {rel}", file=sys.stderr)
        return 1
    if getattr(args, "context_only", False):
        print(render_page_context(rel))
        return 0
    print(target.read_text())
    print()
    print(render_page_context(rel))
    return 0


def cmd_lint_page(args) -> int:
    """Fast single-page check for write-time feedback: frontmatter
    parses with required fields, wiki-internal links resolve,
    supersedes/superseded_by targets exist. Warnings, not gates —
    the PostToolUse hook prints these into the writing agent's
    transcript the moment a page is saved; CI stays the enforcement.
    """
    rel = args.path
    target = Path(rel)
    if not target.is_absolute():
        target = (REPO / rel).resolve()
    try:
        wiki_rel = target.relative_to(WIKI)
    except ValueError:
        return 0  # not a wiki page — nothing to say
    if not target.exists():
        return 0
    warnings = []
    parsed = parse(target)
    if parsed is None:
        warnings.append("no parseable YAML frontmatter")
    else:
        meta, _body = parsed
        for field in sorted(REQUIRED_FIELDS - set(meta)):
            warnings.append(f"missing required frontmatter field: {field}")
        kind = meta.get("kind")
        if kind and kind not in VALID_KINDS:
            warnings.append(f"unknown kind: {kind}")
        for field in ("supersedes", "superseded_by"):
            ref = meta.get(field)
            if ref and not (WIKI / ref).exists():
                warnings.append(f"{field} target missing: {ref}")
    for href in re.findall(r"\]\(([^)]+)\)", target.read_text()):
        href = href.split("#", 1)[0].strip()
        if (not href or not href.endswith(".md")
                or href.startswith(("http://", "https://", "mailto:", "~/"))):
            continue
        link_target = (target.parent / href).resolve()
        try:
            link_target.relative_to(REPO)
        except ValueError:
            continue
        if not link_target.exists():
            warnings.append(f"broken link: {href}")
    if warnings:
        print(f"lint-page {wiki_rel}:")
        for w in warnings:
            print(f"  ! {w}")
    return 0


def cmd_links(args) -> int:
    """Link-graph health views: orphans / hubs / dead-ends / suggest.

    The deterministic input to pruning (orphans want linking or
    archiving) and deepening (hubs are the load-bearing pages whose
    confidence matters most).
    """
    outbound, inbound = _link_graph()
    is_index = lambda p: Path(p).name == "index.md"  # noqa: E731

    orphans = sorted(p for p, src in inbound.items()
                     if not src and not is_index(p))
    hubs = sorted(((p, len(src)) for p, src in inbound.items() if src),
                  key=lambda x: (-x[1], x[0]))[:15]
    dead_ends = sorted(p for p, dst in outbound.items()
                       if not dst and not is_index(p))

    suggestions = []
    metas = {}
    for p in outbound:
        parsed = parse(WIKI / p)
        if parsed:
            m = parsed[0]
            metas[p] = set(m.get("repos") or []) | set(m.get("affects") or [])
    paths = sorted(metas)
    for i, a in enumerate(paths):
        for b in paths[i + 1:]:
            if not metas[a] or is_index(a) or is_index(b):
                continue
            shared = metas[a] & metas[b]
            if shared and b not in outbound[a] and a not in outbound[b]:
                suggestions.append((a, b, sorted(shared)))
    suggestions = suggestions[:15]

    if getattr(args, "json", False):
        print(json.dumps({
            "orphans": orphans, "dead_ends": dead_ends,
            "hubs": [{"path": p, "inbound": n} for p, n in hubs],
            "suggestions": [{"a": a, "b": b, "shared": s}
                            for a, b, s in suggestions],
        }, indent=2))
        return 0

    print(f"# link graph — {len(outbound)} pages\n")
    print(f"orphans ({len(orphans)}) — no inbound links; link or archive:")
    for p in orphans or ["  (none)"]:
        print(f"  {p}" if p != "  (none)" else p)
    print(f"\nhubs (top {len(hubs)}) — most-linked; keep these freshest:")
    for p, n in hubs or []:
        print(f"  {n:>3}← {p}")
    if not hubs:
        print("  (none)")
    print(f"\ndead ends ({len(dead_ends)}) — no outbound links:")
    for p in dead_ends or ["  (none)"]:
        print(f"  {p}" if p != "  (none)" else p)
    print(f"\nsuggested links ({len(suggestions)}) — shared repos, not linked:")
    for a, b, s in suggestions:
        print(f"  {a} ↔ {b}  (shared: {', '.join(s)})")
    if not suggestions:
        print("  (none)")
    return 0


# --- connectors (0.3) — pull-only snapshot-writers ----------------------
#
# Contract per wiki/brain/adrs/connector-snapshot-contract.md: a
# connector observes one external system with read-only-scoped
# credentials, writes immutable dedup-keyed snapshots into
# sources/<connector>/, advances a cursor at
# wiki/_state/connector-cursors.json, queues an inbox item per new
# batch, and NEVER touches wiki/. Unconfigured connectors no-op.

CONNECTOR_CURSORS = WIKI / "_state" / "connector-cursors.json"


def _connector_config(name: str) -> dict:
    config_path = REPO / "brain.config.yml"
    if not config_path.exists():
        return {}
    try:
        cfg = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    return (cfg.get("connectors") or {}).get(name) or {}


def _env(key: str) -> str:
    if os.environ.get(key):
        return os.environ[key]
    env_path = REPO / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _read_connector_cursors() -> dict:
    if CONNECTOR_CURSORS.exists():
        try:
            return json.loads(CONNECTOR_CURSORS.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def _write_connector_cursors(data: dict) -> None:
    CONNECTOR_CURSORS.parent.mkdir(parents=True, exist_ok=True)
    CONNECTOR_CURSORS.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _snapshot_write(connector: str, rel: str, title: str, body: str,
                    extra_fm: dict | None = None) -> Path | None:
    """Write one immutable snapshot; returns None when it already
    exists (the additive-only guarantee doubles as dedup)."""
    path = REPO / "sources" / connector / rel
    if path.exists():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = {"title": title, "connector": connector,
          "pulled": today_utc().isoformat(), **(extra_fm or {})}
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{fm_text}\n---\n\n{body}\n")
    return path


def _github_watched_repos() -> list[str]:
    """Configured owner/repo slugs plus auto-discovered origins of the
    active sibling checkouts."""
    slugs = list(_connector_config("github").get("repos") or [])
    for repo in sorted(ACTIVE_REPOS):
        sibling = PROJECTS / repo
        if not (sibling / ".git").exists():
            continue
        res = subprocess.run(["git", "-C", str(sibling), "remote",
                              "get-url", "origin"],
                             capture_output=True, text=True)
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", res.stdout.strip())
        if m and m.group(1) not in slugs:
            slugs.append(m.group(1))
    return slugs


def _connector_github_pull() -> int:
    """Snapshot new releases + merged-PR batches per watched repo via gh."""
    slugs = _github_watched_repos()
    if not slugs:
        print("github-pull: no repos watched (active_repos empty and "
              "connectors.github.repos unset) — nothing to pull")
        return 0
    if not shutil.which("gh"):
        print("github-pull: gh CLI not available; skipping", file=sys.stderr)
        return 0
    cursors = _read_connector_cursors()
    gh_cursors = cursors.setdefault("github", {})
    today = today_utc().isoformat()
    batches = 0
    for slug in slugs:
        safe = slug.replace("/", "--")
        since = gh_cursors.get(slug, {}).get("last_pull", "1970-01-01")

        res = subprocess.run(
            ["gh", "release", "list", "--repo", slug, "--limit", "10",
             "--json", "tagName,name,publishedAt"],
            capture_output=True, text=True, timeout=30)
        releases = json.loads(res.stdout) if res.returncode == 0 and res.stdout else []
        new_releases = [r for r in releases
                        if (r.get("publishedAt") or "")[:10] > since]
        for rel in new_releases:
            tag = re.sub(r"[^A-Za-z0-9._-]+", "-", rel["tagName"])
            body = subprocess.run(
                ["gh", "release", "view", rel["tagName"], "--repo", slug,
                 "--json", "body", "--jq", ".body"],
                capture_output=True, text=True, timeout=30).stdout
            _snapshot_write("github", f"{safe}/release--{tag}.md",
                            f"{slug} release {rel['tagName']}",
                            body or "(no release notes)",
                            {"repo": slug, "tag": rel["tagName"],
                             "published": rel.get("publishedAt", "")})

        res = subprocess.run(
            ["gh", "pr", "list", "--repo", slug, "--state", "merged",
             "--limit", "50", "--json", "number,title,mergedAt,url",
             "--search", f"merged:>{since}"],
            capture_output=True, text=True, timeout=30)
        prs = json.loads(res.stdout) if res.returncode == 0 and res.stdout else []
        wrote = None
        if prs:
            lines = "".join(
                f"- #{p['number']} {p['title']} "
                f"({(p.get('mergedAt') or '')[:10]}) — {p['url']}\n"
                for p in sorted(prs, key=lambda p: p.get("mergedAt") or ""))
            wrote = _snapshot_write(
                "github", f"{safe}/prs--{today}.md",
                f"{slug} merged PRs since {since}",
                lines, {"repo": slug, "since": since, "count": len(prs)})

        if new_releases or wrote:
            batches += 1
            inbox_add(
                id=f"github-{safe}-{today}", kind="ingest",
                summary=f"{slug}: {len(new_releases)} release(s), "
                        f"{len(prs)} merged PR(s) since {since}",
                route=f"/in sources/github/{safe}/",
                source=f"sources/github/{safe}/",
                produced_by="github-pull", update=True)
        gh_cursors[slug] = {"last_pull": today}
    _write_connector_cursors(cursors)
    print(f"github-pull: {len(slugs)} repo(s) checked, {batches} new batch(es)")
    return 0


def _connector_notion_pull() -> int:
    """Re-snapshot watched Notion pages whose last_edited moved."""
    pages = _connector_config("notion").get("pages") or []
    if not pages:
        print("notion-pull: no pages watched (connectors.notion.pages "
              "unset) — nothing to pull")
        return 0
    token = _env("NOTION_TOKEN")
    if not token:
        print("notion-pull: NOTION_TOKEN not set in .env; skipping",
              file=sys.stderr)
        return 0
    cursors = _read_connector_cursors()
    notion_cursors = cursors.setdefault("notion", {})
    changed = []
    for ref in pages:
        m = re.search(r"([0-9a-fA-F]{32})", str(ref).replace("-", ""))
        if not m:
            print(f"notion-pull: cannot parse page id from {ref!r}",
                  file=sys.stderr)
            continue
        raw = m.group(1).lower()
        pid = f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
        req = urllib.request.Request(
            f"https://api.notion.com/v1/pages/{pid}",
            headers={"Authorization": f"Bearer {token}",
                     "Notion-Version": "2022-06-28"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                meta = json.loads(resp.read())
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            print(f"notion-pull: {pid}: {exc}", file=sys.stderr)
            continue
        last_edited = meta.get("last_edited_time", "")
        if last_edited and last_edited > notion_cursors.get(pid, ""):
            venv_python = Path.home() / ".local/share/mempalace-venv/bin/python3"
            interpreter = str(venv_python) if venv_python.exists() else sys.executable
            res = subprocess.run(
                [interpreter, str(REPO / "tools" / "notion-export.py"), pid],
                capture_output=True, text=True, timeout=120,
                env={**os.environ, "NOTION_TOKEN": token})
            if res.returncode == 0:
                notion_cursors[pid] = last_edited
                changed.append(pid)
            else:
                print(f"notion-pull: export failed for {pid}: "
                      f"{res.stderr.strip()[:200]}", file=sys.stderr)
    if changed:
        inbox_add(id=f"notion-{today_utc().isoformat()}", kind="ingest",
                  summary=f"{len(changed)} Notion page(s) changed and "
                          f"re-snapshotted",
                  route="/in sources/notion/", source="sources/notion/",
                  produced_by="notion-pull", update=True)
    _write_connector_cursors(cursors)
    print(f"notion-pull: {len(pages)} page(s) checked, {len(changed)} changed")
    return 0


def _slack_api(method: str, token: str, **params) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"https://slack.com/api/{method}?{qs}",
        headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _connector_slack_pull() -> int:
    """Snapshot new messages per watched channel as daily transcripts."""
    channels = _connector_config("slack").get("channels") or []
    if not channels:
        print("slack-pull: no channels watched (connectors.slack.channels "
              "unset) — nothing to pull")
        return 0
    token = _env("SLACK_TOKEN")
    if not token:
        print("slack-pull: SLACK_TOKEN not set in .env; skipping",
              file=sys.stderr)
        return 0
    cursors = _read_connector_cursors()
    slack_cursors = cursors.setdefault("slack", {})
    try:
        listing = _slack_api("conversations.list", token,
                             types="public_channel,private_channel",
                             limit=999)
    except urllib.error.URLError as exc:
        print(f"slack-pull: conversations.list failed: {exc}", file=sys.stderr)
        return 1
    if not listing.get("ok"):
        print(f"slack-pull: {listing.get('error', 'unknown error')}",
              file=sys.stderr)
        return 1
    by_name = {c["name"]: c["id"] for c in listing.get("channels", [])}
    today = today_utc().isoformat()
    pulled = 0
    for name in channels:
        cid = by_name.get(name)
        if not cid:
            print(f"slack-pull: channel {name!r} not visible to this token",
                  file=sys.stderr)
            continue
        oldest = slack_cursors.get(name, "0")
        try:
            history = _slack_api("conversations.history", token,
                                 channel=cid, oldest=oldest, limit=200)
        except urllib.error.URLError as exc:
            print(f"slack-pull: history({name}) failed: {exc}", file=sys.stderr)
            continue
        messages = [m for m in history.get("messages", [])
                    if m.get("type") == "message" and m.get("ts", "0") > oldest]
        if not messages:
            continue
        messages.sort(key=lambda m: m["ts"])
        latest = messages[-1]["ts"]
        lines = "".join(
            f"- **{dt.datetime.fromtimestamp(float(m['ts']), dt.timezone.utc).strftime('%H:%M')}**"
            f" `{m.get('user', m.get('bot_id', '?'))}`: "
            f"{(m.get('text') or '').strip()}\n"
            for m in messages)
        wrote = _snapshot_write(
            "slack", f"{name}/{today}--{latest.replace('.', '-')}.md",
            f"#{name} — {len(messages)} message(s)",
            lines, {"channel": name, "oldest": oldest, "latest": latest,
                    "count": len(messages)})
        if wrote:
            pulled += 1
            slack_cursors[name] = latest
            inbox_add(
                id=f"slack-{name}-{today}", kind="ingest",
                summary=f"#{name}: {len(messages)} new message(s)",
                route=f"/in sources/slack/{name}/",
                source=f"sources/slack/{name}/",
                produced_by="slack-pull", update=True)
    _write_connector_cursors(cursors)
    print(f"slack-pull: {len(channels)} channel(s) checked, {pulled} batch(es)")
    return 0


def _connector_datadog_pull() -> int:
    """Daily production-state snapshot: monitor states + SLO inventory.

    Per the API research: monitor state, not logs, is the daily
    primitive (logs search is quota-scarce and stays out of the
    default pull). Needs connectors.datadog.site in config plus
    DD_API_KEY + DD_APP_KEY (app key scoped to monitors_read +
    slos_read) in .env.
    """
    site = _connector_config("datadog").get("site") or ""
    if not site:
        print("datadog-pull: connectors.datadog.site unset — nothing to pull")
        return 0
    api_key, app_key = _env("DD_API_KEY"), _env("DD_APP_KEY")
    if not api_key or not app_key:
        print("datadog-pull: DD_API_KEY / DD_APP_KEY not set in .env; "
              "skipping", file=sys.stderr)
        return 0

    def dd_get(path: str, params: dict | None = None):
        qs = ("?" + urllib.parse.urlencode(params)) if params else ""
        req = urllib.request.Request(
            f"https://api.{site}{path}{qs}",
            headers={"DD-API-KEY": api_key, "DD-APPLICATION-KEY": app_key})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    today = today_utc().isoformat()
    try:
        monitors = dd_get("/api/v1/monitor",
                          {"group_states": "all", "with_downtimes": "true",
                           "page_size": 200})
        slos = dd_get("/api/v1/slo").get("data", [])
    except urllib.error.URLError as exc:
        print(f"datadog-pull: API error: {exc} "
              f"(check DD_SITE={site!r} and app-key scopes)", file=sys.stderr)
        return 0

    by_state: dict[str, int] = collections.Counter(
        m.get("overall_state", "Unknown") for m in monitors)
    alerting = sorted(m.get("name", "?") for m in monitors
                      if m.get("overall_state") in ("Alert", "Warn"))

    lines = [f"- **{m.get('overall_state', '?')}** {m.get('name', '?')} "
             f"(id {m.get('id')})\n" for m in
             sorted(monitors, key=lambda m: (m.get("overall_state", ""),
                                             str(m.get("name", ""))))]
    slo_lines = [f"- {s.get('name', '?')} (type {s.get('type', '?')})\n"
                 for s in sorted(slos, key=lambda s: str(s.get("name", "")))]
    _snapshot_write(
        "datadog", f"monitors--{today}.md",
        f"Datadog monitors + SLOs — {today}",
        f"## Monitors ({len(monitors)})\n\n" + "".join(lines)
        + f"\n## SLOs ({len(slos)})\n\n" + "".join(slo_lines),
        {"site": site, "monitors": len(monitors), "slos": len(slos),
         "alerting": len(alerting)})

    state_path = WIKI / "_state" / "datadog.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({
        "pulled": today, "site": site,
        "monitors_total": len(monitors),
        "by_state": dict(by_state),
        "alerting": alerting[:25],
        "slos_total": len(slos),
    }, indent=2, sort_keys=True) + "\n")

    if alerting:
        inbox_add(id=f"datadog-alerting-{today}", kind="ingest",
                  summary=f"Datadog: {len(alerting)} monitor(s) in "
                          f"Alert/Warn state",
                  route="/in sources/datadog/",
                  source=f"sources/datadog/monitors--{today}.md",
                  produced_by="datadog-pull", update=True)
    print(f"datadog-pull: {len(monitors)} monitor(s) "
          f"({dict(by_state)}), {len(slos)} SLO(s)")
    return 0


def _connector_langfuse_pull() -> int:
    """Daily prompt-state snapshot: inventory + production versions.

    Per the API research: Langfuse has no read-only key type — keys
    are project-scoped and write-capable, so the documented guidance
    is dedicated-project keys or self-host. Needs
    connectors.langfuse.host in config plus LANGFUSE_PUBLIC_KEY +
    LANGFUSE_SECRET_KEY in .env. Trace/score increments are a
    follow-up; prompts are the state the views need first.
    """
    host = (_connector_config("langfuse").get("host") or "").rstrip("/")
    if not host:
        print("langfuse-pull: connectors.langfuse.host unset — "
              "nothing to pull")
        return 0
    pub, sec = _env("LANGFUSE_PUBLIC_KEY"), _env("LANGFUSE_SECRET_KEY")
    if not pub or not sec:
        print("langfuse-pull: LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY "
              "not set in .env; skipping", file=sys.stderr)
        return 0
    import base64
    auth = base64.b64encode(f"{pub}:{sec}".encode()).decode()

    def lf_get(path: str, params: dict | None = None):
        qs = ("?" + urllib.parse.urlencode(params)) if params else ""
        req = urllib.request.Request(
            f"{host}/api/public{path}{qs}",
            headers={"Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    today = today_utc().isoformat()
    prompts, page = [], 1
    try:
        while True:
            data = lf_get("/v2/prompts", {"page": page, "limit": 100})
            prompts.extend(data.get("data", []))
            meta = data.get("meta", {})
            if page >= int(meta.get("totalPages", 1)):
                break
            page += 1
            time.sleep(3)  # Hobby tier: ~20 req/min
    except urllib.error.URLError as exc:
        print(f"langfuse-pull: API error: {exc} (check host + keys)",
              file=sys.stderr)
        return 0

    prompts.sort(key=lambda p: str(p.get("name", "")))
    lines = []
    for pr in prompts:
        versions = pr.get("versions") or []
        labels = pr.get("labels") or []
        lines.append(f"- **{pr.get('name', '?')}** — "
                     f"{len(versions)} version(s); labels: "
                     f"{', '.join(labels) or '(none)'}\n")
    _snapshot_write(
        "langfuse", f"prompts--{today}.md",
        f"Langfuse prompt inventory — {today}",
        f"## Prompts ({len(prompts)})\n\n" + "".join(lines),
        {"host": host, "prompts": len(prompts)})

    state_path = WIKI / "_state" / "langfuse.json"
    state_path.write_text(json.dumps({
        "pulled": today, "host": host,
        "prompts_total": len(prompts),
        "prompts": [{"name": p.get("name"),
                     "versions": len(p.get("versions") or []),
                     "labels": p.get("labels") or []}
                    for p in prompts[:50]],
    }, indent=2, sort_keys=True) + "\n")

    inbox_add(id=f"langfuse-{today}", kind="ingest",
              summary=f"Langfuse: {len(prompts)} prompt(s) snapshotted",
              route="/in sources/langfuse/",
              source=f"sources/langfuse/prompts--{today}.md",
              produced_by="langfuse-pull", update=True)
    print(f"langfuse-pull: {len(prompts)} prompt(s)")
    return 0


def _schedule_run_inbox_refresh() -> int:
    """Recompute the deterministic slice of the tend queue.

    Producers owned by this op (produced_by == "inbox-refresh") are
    fully reconciled on every run: items are upserted while their
    trigger holds and removed once it clears, so the queue never
    shows stale machine-generated work. Operator- and
    connector-produced items are never touched.

      cursor-diff-<repo>   sibling repo changed since its sync cursor
      half-life-<slug>     confidence:high page not updated in >30d
      link-health          broken wiki-internal links exist
    """
    current: dict[str, dict] = {}

    data = _read_cursors()
    for repo in sorted(ACTIVE_REPOS):
        entry = data.get("cursors", {}).get(repo)
        sibling = PROJECTS / repo
        if not entry or not sibling.exists():
            continue
        try:
            changed = _git(["diff", entry["sha"] + "..HEAD", "--name-only"],
                           sibling).splitlines()
        except Exception:
            continue
        if changed:
            current[f"cursor-diff-{repo}"] = {
                "kind": "ingest",
                "summary": f"{repo}: {len(changed)} file(s) changed since "
                           f"cursor {entry['sha'][:8]}",
                "route": f"/in {repo} (walk `brain.py sync-cursor diff {repo}`)",
                "source": f"~/projects/{repo}",
                "priority": "normal",
            }

    today = today_utc()
    page_meta: dict[str, dict] = {}
    for p in wiki_pages():
        parsed = parse(p)
        if parsed is None:
            continue
        meta, _body = parsed
        rel = str(p.relative_to(WIKI))
        page_meta[rel] = meta
        if meta.get("status") in ("superseded", "archived"):
            continue
        updated = meta.get("updated")
        if isinstance(updated, str):
            try:
                updated = dt.date.fromisoformat(updated)
            except ValueError:
                continue
        if not isinstance(updated, dt.date):
            continue
        age = (today - updated).days
        reasons = []
        if meta.get("confidence") == "high" and age > 30:
            reasons.append(f"confidence:high but {age}d since update "
                           f"(30d refresh rule)")
        stale_days = HALF_LIFE_STALE_DAYS.get(
            meta.get("kind", "reference"),
            HALF_LIFE_STALE_DAYS["reference"])
        if age > stale_days:
            reasons.append(f"kind:{meta.get('kind')} stale at {age}d "
                           f"(>{stale_days}d half-life)")
        if reasons:
            slug = re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-")
            current[f"half-life-{slug}"] = {
                "kind": "groom",
                "summary": f"{rel}: {'; '.join(reasons)} — refresh or demote",
                "route": "/groom",
                "source": f"wiki/{rel}",
                "priority": "low",
            }

    outbound, inbound = _link_graph()
    orphans = [p for p, src in inbound.items()
               if not src and Path(p).name != "index.md"]
    if orphans:
        current["link-orphans"] = {
            "kind": "groom",
            "summary": f"{len(orphans)} orphan page(s) with no inbound "
                       f"links — link or archive "
                       f"(`brain.py links` for the list)",
            "route": "/groom",
            "source": "wiki/",
            "priority": "low",
        }

    # Deepening picker: low-confidence pages that the graph leans on.
    # Damping (first dogfooding amendment, 2026-07-10): kinds whose
    # medium/low confidence is policy-correct are excluded — topics
    # and pitches live at their tier by design, and initiative bumps
    # are human-gated — and pages get a 7-day grace period: nothing
    # deserves a deepening demand the week it was written.
    picks = []
    grace_cutoff = today - dt.timedelta(days=7)
    for rel, meta in page_meta.items():
        if meta.get("status") in ("superseded", "archived"):
            continue
        if meta.get("kind") in ("topic", "pitch", "initiative"):
            continue
        if meta.get("confidence") not in ("low", "medium"):
            continue
        updated = meta.get("updated")
        if isinstance(updated, str):
            try:
                updated = dt.date.fromisoformat(updated)
            except ValueError:
                updated = None
        if isinstance(updated, dt.date) and updated > grace_cutoff:
            continue
        degree = len(inbound.get(rel, ()))
        if degree >= 2:
            picks.append((degree, rel, meta.get("confidence")))
    for degree, rel, conf in sorted(picks, reverse=True)[:3]:
        slug = re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-")
        current[f"research-{slug}"] = {
            "kind": "research",
            "summary": f"{rel}: confidence:{conf} but {degree} pages "
                       f"link to it — deepen with cited research",
            "route": f"deepdive wiki/{rel}, snapshot findings to "
                     f"sources/research/, earn the confidence bump",
            "source": f"wiki/{rel}",
            "priority": "normal",
        }

    for repo in sorted(ACTIVE_REPOS):
        if not (WIKI / repo / "index.md").exists():
            current[f"coverage-gap-{repo}"] = {
                "kind": "research",
                "summary": f"{repo} is in active scope but has no "
                           f"wiki/{repo}/ shelf yet — first-pass ingest",
                "route": f"/in {repo}",
                "source": f"~/projects/{repo}",
                "priority": "normal",
            }

    broken = 0
    for page in WIKI.rglob("*.md"):
        rel = page.relative_to(WIKI)
        if any(part.startswith("_") for part in rel.parts):
            continue
        for href in re.findall(r"\]\(([^)]+)\)", page.read_text()):
            href = href.split("#", 1)[0].strip()
            if (not href or href.endswith("/") or not href.endswith(".md")
                    or href.startswith(("http://", "https://", "mailto:", "~/"))):
                continue
            target = (page.parent / href).resolve()
            try:
                target.relative_to(WIKI)
            except ValueError:
                continue
            if not target.exists():
                broken += 1
    if broken:
        current["link-health"] = {
            "kind": "groom",
            "summary": f"{broken} broken wiki-internal link(s) — "
                       f"run `brain.py reflection-check links` for the list",
            "route": "/groom",
            "source": "wiki/",
            "priority": "high",
        }

    added = updated_n = 0
    for id, fields in current.items():
        existed = (INBOX_DIR / f"{id}.json").exists()
        inbox_add(id=id, produced_by="inbox-refresh", update=True, **fields)
        added += 0 if existed else 1
        updated_n += 1 if existed else 0

    removed = 0
    for item in _inbox_items():
        if item.get("produced_by") == "inbox-refresh" and item["id"] not in current:
            (INBOX_DIR / f"{item['id']}.json").unlink(missing_ok=True)
            removed += 1

    _playthrough_queue_slice()

    print(f"inbox-refresh: {added} added, {updated_n} refreshed, "
          f"{removed} cleared; {len(_inbox_items())} pending total")
    return 0


def _dt_now_compact() -> str:
    import time
    return time.strftime("%Y%m%d-%H%M%S")


PLAYTHROUGH_CURSOR = WIKI / "_state" / "playthrough-cursor.json"


def _playthrough_queue_slice() -> None:
    """Queue one persona-playthrough sweep per shipped version.

    Distinct produced_by so the inbox-refresh reconciler never
    clears a pending sweep — the item persists until tended. The
    cursor advances at queue time, so a swept (inbox done) item is
    not re-queued. First run initialises the cursor silently: a
    fresh shell or newborn instance owes no sweep.
    """
    version_path = REPO / "VERSION"
    if not version_path.exists():
        return
    version = version_path.read_text().strip()
    if PLAYTHROUGH_CURSOR.exists():
        seen = json.loads(PLAYTHROUGH_CURSOR.read_text()).get("version")
    else:
        seen = None
    if seen == version:
        return
    if seen is not None:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", version)
        inbox_add(
            id=f"playthrough-{slug}",
            kind="custom",
            summary=f"{version} shipped — persona playthrough sweep "
                    f"before the next slice",
            route="/playthrough",
            source="VERSION",
            priority="normal",
            produced_by="playthrough-cursor",
            update=True,
        )
    PLAYTHROUGH_CURSOR.write_text(json.dumps(
        {"version": version, "queued": today_utc().isoformat()},
        indent=2) + "\n")


def _schedule_run_deadline_countdown() -> int:
    """Refresh `wiki/_state/deadlines.json` last_assessment + per-deadline days-left.

    The file is optional — an org with no tracked deadlines has no
    file, and the op is a clean no-op rather than a failure. Each
    entry needs `name` + `date` (ISO); `readiness` (low|medium|high)
    and `note` are operator-maintained fields the op never touches.
    """
    state_path = WIKI / "_state" / "deadlines.json"
    if not state_path.exists():
        print("deadline-countdown: no deadlines tracked "
              "(wiki/_state/deadlines.json absent)")
        return 0
    state = json.loads(state_path.read_text())
    today = today_utc()
    state["last_assessment"] = today.isoformat()
    lines = []
    for entry in state.get("deadlines", []):
        date = dt.date.fromisoformat(entry["date"])
        entry["_days_left"] = (date - today).days
        lines.append(f"{entry.get('name', '(unnamed)')}: "
                     f"{entry['_days_left']} days to {date.isoformat()}")
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print(f"deadline-countdown: {len(lines)} deadline(s) refreshed"
          + "".join(f"\n  {ln}" for ln in lines))
    return 0


def _schedule_run_issues_pull() -> int:
    """Pull issue counts via `gh issue list` per active sibling repo on disk."""
    state_path = WIKI / "_state" / "issues.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"repos": {}}
    for repo in sorted(ACTIVE_REPOS):
        state.setdefault("repos", {}).setdefault(repo, {})
    if not state.get("repos"):
        print("issues-pull: no active repos declared in brain.config.yml "
              "— nothing to pull")
        return 0
    today = today_utc().isoformat()
    populated = 0
    if not shutil.which("gh"):
        print("issues-pull: gh CLI not available; skipping", file=sys.stderr)
        return 0
    for repo, entry in state.get("repos", {}).items():
        sibling = PROJECTS / repo
        if not sibling.exists():
            entry["notes"] = f"(skipped — repo not on disk at {sibling})"
            continue
        try:
            res = subprocess.run(
                ["gh", "issue", "list", "--state", "open", "--limit", "1000",
                 "--json", "number,labels,createdAt"],
                cwd=sibling, capture_output=True, text=True, timeout=30,
            )
            if res.returncode != 0:
                entry["notes"] = f"(gh issue list failed: {res.stderr.strip()[:120]})"
                continue
            issues = json.loads(res.stdout or "[]")
        except Exception as exc:
            entry["notes"] = f"(gh issue list error: {exc})"
            continue
        critical = sum(1 for i in issues if any(
            (l.get("name") or "").lower() in ("critical", "p0", "sev-1") for l in i.get("labels", [])
        ))
        blocking = sum(1 for i in issues if any(
            (l.get("name") or "").lower() in ("blocking", "blocker") for l in i.get("labels", [])
        ))
        stale_30d = 0
        for i in issues:
            try:
                ts = i.get("createdAt", "")[:10]
                if ts and (today_utc() - dt.date.fromisoformat(ts)).days > 30:
                    stale_30d += 1
            except (ValueError, TypeError):
                continue
        entry.update({
            "last_pull": today,
            "open": len(issues),
            "critical_open": critical,
            "blocking_open": blocking,
            "stale_open_30d": stale_30d,
            "notes": "via gh issue list",
        })
        populated += 1
    state["last_pull"] = today
    state["source"] = "github-issues"
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print(f"issues-pull: populated {populated} repo(s)")
    return 0


def _schedule_run_notion_walk() -> int:
    """Walk sources/notion/ + flag snapshots older than 30 days."""
    notion_dir = REPO / "sources" / "notion"
    if not notion_dir.exists():
        print("notion-walk: no planning-source snapshots yet "
              "(sources/notion/ absent)")
        return 0
    today = today_utc()
    snapshots = list(notion_dir.glob("*.md"))
    stale = []
    for s in snapshots:
        # Notion snapshots carry an `updated:` or `captured:` frontmatter
        try:
            meta = (parse(s) or ({},))[0]
            ts_field = meta.get("captured") or meta.get("updated") or meta.get("fetched")
            if isinstance(ts_field, dt.date):
                age = (today - ts_field).days
            elif isinstance(ts_field, str):
                age = (today - dt.date.fromisoformat(ts_field[:10])).days
            else:
                continue
            if age > 30:
                stale.append((s.relative_to(REPO), age))
        except (ValueError, TypeError):
            continue
    cursor_path = WIKI / "_state" / "notion-cursor.json"
    state = {
        "_schema": "v1",
        "last_walk": today.isoformat(),
        "snapshot_count": len(snapshots),
        "stale_count": len(stale),
        "stale_examples": [{"path": str(p), "age_days": age} for p, age in stale[:10]],
    }
    cursor_path.write_text(json.dumps(state, indent=2) + "\n")
    print(f"notion-walk: {len(snapshots)} snapshot(s); {len(stale)} stale (>30d)")
    return 0


def _schedule_run_overlap_refresh() -> int:
    """Re-run the cluster command and dump output to wiki/_overlaps/."""
    overlap_path = WIKI / "_overlaps" / f"auto-refresh-{today_utc().isoformat()}.md"
    overlap_path.parent.mkdir(exist_ok=True)
    res = subprocess.run(
        [sys.executable, str(REPO / "tools" / "brain.py"), "cluster"],
        capture_output=True, text=True, timeout=60, cwd=REPO,
    )
    today = today_utc().isoformat()
    body = f"""---
title: "Auto-refreshed cluster scan {today}"
kind: overlap
status: living
updated: {today}
sources:
  - sources/notion/
  - wiki/_views/pages.json
---

# Auto-refreshed cluster scan {today}

Output of `brain.py cluster` (TF-IDF + HDBSCAN clustering over the
synthesis corpus). Run by `brain.py schedule run overlap-refresh`.

## Items

```
{res.stdout or '(no output)'}
```

## Overlap

(stub — review the cluster output and surface intersections that
warrant a `/overlap` deep-dive.)

## Recommendation

Operator decides whether any cluster warrants spawning a `/shape
org` follow-up.
"""
    overlap_path.write_text(body)
    print(f"overlap-refresh: wrote {overlap_path.relative_to(REPO)}")
    return 0


def _schedule_run_zoom_out_digest() -> int:
    """Synthesise a brain-wide zoom-out digest (deterministic, no LLM)."""
    digest_path = WIKI / "_state" / "zoom-out-digest.md"
    today = today_utc()
    # Frontmatter so Astro's docsSchema accepts it (title required).
    # Even though wiki/_state/ is a machine-readable shelf, the
    # symlinked docs/ root picks up every .md.
    parts = [
        "---",
        f'title: "Brain zoom-out digest — {today.isoformat()}"',
        "kind: meta",
        "status: living",
        f"updated: {today.isoformat()}",
        "sources: []",
        "---",
        "",
        f"# Brain zoom-out digest — {today.isoformat()}\n",
    ]

    # Recent log entries
    log_path = REPO / "log" / "log.md"
    if log_path.exists():
        log_lines = log_path.read_text().splitlines()
        recent = []
        for line in log_lines[::-1]:
            if line.startswith(today.isoformat()[:7]):  # this month
                recent.append(line)
            if len(recent) >= 30:
                break
        parts.append(f"\n## Recent log entries (this month, last 30)\n")
        for line in reversed(recent):
            parts.append(line)

    # In-flight efforts
    if EFFORTS_DIR.exists():
        efforts = list(EFFORTS_DIR.glob("*.json"))
        parts.append(f"\n## In-flight efforts ({len(efforts)})\n")
        for e in sorted(efforts):
            try:
                rec = json.loads(e.read_text())
                parts.append(f"- `{rec.get('slug', e.stem)}` — phase: "
                             f"{rec.get('phase', '?')}, status: "
                             f"{rec.get('status', '?')}")
            except json.JSONDecodeError:
                parts.append(f"- `{e.stem}` (unparseable record)")

    # AI-suggestion backlog
    ai_files = list(WIKI.glob("**/ai-suggestions/**/*.md"))
    suggested = [f for f in ai_files
                 if (parse(f) or ({},))[0].get("status") == "suggested"]
    parts.append(f"\n## AI-suggestion backlog ({len(suggested)} pending review)\n")
    for f in sorted(suggested)[:10]:
        meta = (parse(f) or ({},))[0]
        parts.append(f"- [{meta.get('title', f.name)}]({f.relative_to(WIKI)})")

    # Reflection-check summary (run quick)
    parts.append("\n## Reflection-check summary\n")
    parts.append("Run `brain.py reflection-check` for current findings.")

    digest_path.write_text("\n".join(parts) + "\n")
    print(f"zoom-out-digest: wrote {digest_path.relative_to(REPO)}")
    return 0


def _schedule_run_ai_suggestion_grooming() -> int:
    """Walk ai-suggestions/ + flag pages with `updated:` > 180 days old."""
    today = today_utc()
    threshold = today - dt.timedelta(days=180)
    ai_files = list(WIKI.glob("**/ai-suggestions/**/*.md"))
    stale = []
    for f in ai_files:
        meta = (parse(f) or ({},))[0]
        if meta.get("status") != "suggested":
            continue
        updated = meta.get("updated")
        if isinstance(updated, str):
            try:
                updated = dt.date.fromisoformat(updated)
            except ValueError:
                continue
        if not isinstance(updated, dt.date):
            continue
        if updated < threshold:
            stale.append({
                "path": str(f.relative_to(WIKI)),
                "updated": updated.isoformat(),
                "age_days": (today - updated).days,
                "title": meta.get("title", "(untitled)"),
            })
    state_path = WIKI / "_state" / "ai-suggestion-grooming.json"
    state_path.write_text(json.dumps({
        "_schema": "v1",
        "last_run": today.isoformat(),
        "threshold_days": 180,
        "stale_count": len(stale),
        "stale": stale,
    }, indent=2) + "\n")
    print(f"ai-suggestion-grooming: {len(ai_files)} ai-suggestions inspected; "
          f"{len(stale)} stale (>180d)")
    if stale:
        print("  Candidates for graduation or archive:")
        for s in stale[:10]:
            print(f"    {s['age_days']:4d}d  {s['path']}")
    return 0


SCHEDULE_HANDLERS = {
    "security-scan": _schedule_run_security_scan,
    "deadline-countdown": _schedule_run_deadline_countdown,
    "inbox-refresh": _schedule_run_inbox_refresh,
    "github-pull": _connector_github_pull,
    "notion-pull": _connector_notion_pull,
    "slack-pull": _connector_slack_pull,
    "datadog-pull": _connector_datadog_pull,
    "langfuse-pull": _connector_langfuse_pull,
    "issues-pull": _schedule_run_issues_pull,
    "notion-walk": _schedule_run_notion_walk,
    "overlap-refresh": _schedule_run_overlap_refresh,
    "zoom-out-digest": _schedule_run_zoom_out_digest,
    "ai-suggestion-grooming": _schedule_run_ai_suggestion_grooming,
}


def cmd_schedule(args) -> int:
    """Manage the declarative schedule at brain-schedule.yml.

    This v1 ships the config + listing only; the runner is a
    separate decision.
    """
    config_path = REPO / "brain-schedule.yml"
    if not config_path.exists():
        print(f"brain-schedule.yml not found at {config_path}", file=sys.stderr)
        return 1
    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        print(f"brain-schedule.yml unparseable: {exc}", file=sys.stderr)
        return 1

    op = (args.op or "list").lower()

    if op == "list":
        print(f"# brain-schedule.yml v{config.get('version', '?')}")
        for entry in config.get("operations") or []:
            enabled = "✓" if entry.get("enabled") else "✗"
            print(f"  {enabled}  {entry.get('cadence', '?'):8s}  {entry.get('name')}")
            print(f"      {entry.get('description', '')}")
            if not entry.get("enabled") and entry.get("deferred_until"):
                print(f"      deferred until: {entry['deferred_until']}")
        return 0

    if op == "run":
        target = args.target
        if not target:
            print("schedule run requires --target <op-name>", file=sys.stderr)
            return 2
        # In-process handler first
        if target in SCHEDULE_HANDLERS:
            print(f"# running: {target}", file=sys.stderr)
            return SCHEDULE_HANDLERS[target]()
        # Fall back to handler in config (shell-out)
        for entry in config.get("operations") or []:
            if entry.get("name") == target:
                if not entry.get("enabled"):
                    print(f"operation {target!r} is disabled in brain-schedule.yml",
                          file=sys.stderr)
                    return 1
                handler = entry.get("handler")
                if not handler:
                    print(f"operation {target!r} has no handler", file=sys.stderr)
                    return 1
                print(f"# running: {target}", file=sys.stderr)
                rc = subprocess.run(handler, shell=True, cwd=REPO).returncode
                return rc
        print(f"operation {target!r} not found in brain-schedule.yml", file=sys.stderr)
        return 1

    if op == "run-due":
        # v1: run every enabled op (no last_run tracking yet).
        # The runs.json tracker is part of the deferred runtime.
        rc_total = 0
        for entry in config.get("operations") or []:
            if not entry.get("enabled"):
                continue
            name = entry.get("name")
            print(f"# running: {name}", file=sys.stderr)
            if name in SCHEDULE_HANDLERS:
                rc = SCHEDULE_HANDLERS[name]()
            else:
                handler = entry.get("handler")
                if not handler:
                    continue
                rc = subprocess.run(handler, shell=True, cwd=REPO).returncode
            if rc != 0:
                rc_total = rc
        return rc_total

    print(f"unknown schedule op: {op}", file=sys.stderr)
    return 2


# The kernel manifest — what crosses into every born instance, per
# wiki/brain/adrs/kernel-manifest-instancing.md. Fail-closed: anything
# not listed here stays in the tool's repo. Mechanism and its
# documentation cross; observations and self-tracking never do.
KERNEL_COPY_PATHS = [
    # mechanism
    "tools",
    ".claude/commands",
    ".claude/skills",
    ".claude/settings.json",
    ".claude/personas/agents",
    ".claude/personas/README.md",
    "ui/src", "ui/astro.config.mjs", "ui/package.json",
    "ui/package-lock.json", "ui/tsconfig.json",
    "ui/remark-rewrite-links.mjs", "ui/serve.mjs", "ui/Dockerfile",
    "ui/README.md",
    "deploy",
    "tests",
    ".github",
    "views",
    "AGENTS.md",
    "brain-schedule.yml",
    ".gitignore", ".dockerignore", ".env.example", ".mcp.json",
    "railway.toml", "VERSION",
    # the kernel's own documentation trail
    "wiki/brain/adrs",
    "wiki/brain/authoring-adrs-and-prds.md",
    "wiki/org/methodology",
    "wiki/org/operator-lessons.md",
]


def _init_full(target: Path, org: str) -> int:
    """Birth a working instance: manifest copy + fresh scaffold."""
    src_root = REPO
    kernel_version = (src_root / "VERSION").read_text().strip()
    for rel in KERNEL_COPY_PATHS:
        src = src_root / rel
        if not src.exists():
            print(f"init --full: manifest path missing in kernel: {rel}",
                  file=sys.stderr)
            return 1
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(
                src, dst, symlinks=True,
                ignore=shutil.ignore_patterns(
                    "node_modules", "__pycache__", ".build-cache",
                    "dist", "*.pyc", ".pytest_cache"))
        else:
            shutil.copy2(src, dst)

    (target / "CLAUDE.md").symlink_to("AGENTS.md")
    (target / "sources").mkdir(exist_ok=True)
    shutil.copy2(src_root / "sources" / "README.md",
                 target / "sources" / "README.md")
    (target / "log").mkdir(exist_ok=True)
    (target / "log" / "log.md").write_text("")
    for d in ("_views", "_archive", "_overlaps", "_state",
              "org", "insights", "brain"):
        (target / "wiki" / d).mkdir(parents=True, exist_ok=True)
    (target / "wiki" / "_state" / "sync-cursors.json").write_text("{}\n")

    today = today_utc().isoformat()
    org_label = org or "<your organisation>"

    def page(rel: str, title: str, kind: str, body: str):
        depth = "../" * len(Path(rel).parts)
        p = target / "wiki" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            f"---\ntitle: \"{title}\"\nkind: {kind}\nstatus: draft\n"
            f"updated: {today}\nconfidence: high\nsources:\n"
            f"  - {depth}AGENTS.md\n---\n\n# {title}\n\n{body}\n")

    def owner(section: str) -> str:
        if section in ("What changed", "Open initiatives",
                       "Recent decisions"):
            return "/shape"
        if section == "Insights now":
            return "/feedback"
        return "/groom"

    home_sections = "\n\n".join(
        f"## {s}\n\n<!-- home-section: empty; maintained-by: "
        f"{owner(s)} -->\n*(empty — nothing yet)*"
        for s in ("What changed", "Open initiatives", "Recent decisions",
                  "Drift surface", "Insights now", "Brain trajectory",
                  "Curated picks"))
    page("index.md", f"{org_label} brain — home", "meta",
         f"A brain instance for {org_label}, born from kernel "
         f"{kernel_version} on {today}. Fill `brain.config.yml`, run "
         f"`python3 tools/brain.py setup`, then `/in <source>`.\n\n"
         f"{home_sections}\n\n## Where to find things\n\n"
         f"- [Brain — meta level](brain/index.md)\n"
         f"- [Org — methodology + cross-product](org/index.md)")
    adr_lines = []
    for adr in sorted((target / "wiki" / "brain" / "adrs").glob("*.md")):
        parsed = parse(adr)
        title = str(parsed[0].get("title", adr.stem)) if parsed else adr.stem
        short = title.split(";")[0].split(":")[0].strip()
        adr_lines.append(f"- [{short}](adrs/{adr.name})")
    page("brain/index.md", "Brain (meta level)", "meta",
         "This instance's self-tracking shelf. The `adrs/` folder "
         "carries the **kernel decision trail** it was born with — "
         "decisions about the tool, superseded here only by your own "
         "records.\n\n"
         "- [State](state.md)\n"
         "- [Authoring ADRs and PRDs](authoring-adrs-and-prds.md)\n"
         "\n## ADRs (kernel trail)\n\n"
         + "\n".join(adr_lines)
         + "\n\n## PRDs\n\n*(none yet)*")
    page("brain/state.md", "Brain — state", "reference",
         "## Cross-level context\n\n*(none yet)*\n\n## Past\n\n"
         f"- **{today}** — instance born from kernel "
         f"{kernel_version}.\n\n## Now\n\n- Unconfigured — awaiting "
         "`setup` and the first ingest.\n\n## Perceived\n\n*(none "
         "yet)*\n\n## Target\n\n- First ingest.")
    page("org/index.md", f"{org_label} — org level", "meta",
         "Cross-organisation pages: methodology (born with the "
         "kernel), operator lessons, and whatever the org earns.\n\n"
         "- [Methodology](methodology/index.md)\n"
         "- [Operator lessons](operator-lessons.md)")

    # Crossed pages may cite tool-repo sources (research notes,
    # conversation snapshots) that stay behind — drop citations that
    # don't resolve inside the instance so its own gates run clean.
    for page_file in (target / "wiki").rglob("*.md"):
        text = page_file.read_text()
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end == -1:
            continue
        fm, body = text[:end], text[end:]
        kept, changed = [], False
        for line in fm.splitlines():
            stripped = line.strip()
            ref_like = stripped.startswith("- ") and (
                stripped[2:].startswith(("../", "sources/", "tools/",
                                         "wiki/", ".claude/")))
            if ref_like:
                ref = stripped[2:].strip()
                resolved = (page_file.parent / ref).resolve()                     if ref.startswith(".") else (target / ref)
                if not resolved.exists() and not ref.startswith("http"):
                    changed = True
                    continue
            kept.append(line)
        if changed:
            new_fm = "\n".join(kept)
            # A page whose citations all stayed behind falls back to
            # the schema — the kernel is its own primary source.
            import re as _re
            if _re.search(r"sources:\s*$", new_fm):
                rel_depth = "../" * len(
                    page_file.relative_to(target / "wiki").parts)
                new_fm += f"\n  - {rel_depth}AGENTS.md"
            page_file.write_text(new_fm + body)

    config = (src_root / "brain.config.yml").read_text()
    if org:
        config = config.replace('org: ""', f'org: "{org}"', 1)
    (target / "brain.config.yml").write_text(config)

    subprocess.run(["git", "init", "-q"], cwd=target, check=False)
    hooks = target / ".git" / "hooks"
    if hooks.exists() and not (hooks / "pre-commit").exists():
        (hooks / "pre-commit").symlink_to(
            "../../tools/git-hooks/pre-commit")

    env = {**os.environ, "BRAIN_DIR": str(target)}
    for gate in ("views", "validate"):
        res = subprocess.run(
            [sys.executable, str(target / "tools" / "brain.py"), gate],
            cwd=target, env=env, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"init --full: {gate} failed in instance:\n"
                  f"{res.stdout[:800]}{res.stderr[:400]}", file=sys.stderr)
            return 1
    print(f"instance born at {target}")
    print(f"  kernel {kernel_version} · org={org_label!r} · "
          f"validate+views green")
    print(f"  next: cd {target} && python3 tools/brain.py setup")
    return 0


def cmd_init(args) -> int:
    """Scaffold an empty brain shell at the target directory.

    Creates the minimum viable substrate: AGENTS.md (kernel-flavoured),
    wiki/ skeleton (index.md + brain/ + org/), tools/ pointer, an empty
    sources/, an empty log/log.md. After this, the operator fills wiki/
    with their organisation's content.

    Per `wiki/brain/ai-suggestions/prds/extractable-brain-shell.md`.
    """
    target = Path(args.path).resolve()
    if target.exists() and any(target.iterdir()):
        if not args.force:
            print(f"refusing to init non-empty directory: {target} (use --force)",
                  file=sys.stderr)
            return 1

    target.mkdir(parents=True, exist_ok=True)

    if getattr(args, "full", False):
        return _init_full(target, args.org or "")

    org = args.org or "<your-organisation>"

    # AGENTS.md — kernel-flavoured (no organisation specifics)
    agents_md = f'''# AGENTS.md — schema for the brain

You are the agent maintaining this brain. This file tells you how.
The methodology is the LLM-wiki pattern from
<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>.

This brain was scaffolded by `brain.py init` on {today_utc().isoformat()}
for {org}.

## Mission

Maintain a synthesis of {org} — products, repositories, decisions,
people, roadmap — accurate enough that:

1. **Codebases could be regenerated** from the specs stored here.
2. **Cross-team overlaps surface, not hide.**
3. **Autonomous agents can use this as their primary context.**

## The three layers

1. **Raw sources** (`sources/`) — immutable.
2. **The wiki** (`wiki/`) — markdown pages you own. `wiki/index.md` is
   the catalog.
3. **The schema** — this file.

## Page kinds

Set `kind:` in frontmatter:

| Kind         | Purpose                                            |
|--------------|----------------------------------------------------|
| `reference`  | How a thing *is*.                                  |
| `initiative` | Active piece of work (PRD).                        |
| `decision`   | A specific decision (ADR).                         |
| `entity`     | A person, team, division, product, customer.       |
| `meta`       | About the brain itself.                            |
| `insight`    | A pattern derived from feedback / observed work.   |
| `epic`       | Umbrella over multi-PRD/ADR work.                  |

## Active scope

Sibling repos this brain tracks:

| Repo        | Status |
|-------------|--------|
| (add yours) |        |

## Tools

- `python3 tools/brain.py validate` — frontmatter + section conformance.
- `python3 tools/brain.py check --no-net` — citation paths resolve.
- `python3 tools/brain.py views` — regenerate `wiki/_views/`.
- `python3 tools/brain.py search '<query>'` — hybrid keyword search.
- `python3 tools/brain.py install-sibling <repo>` — wire the brain into
  a sibling repo's Claude Code session.
- `python3 tools/brain.py reflection-check` — drift between brain and
  target-repo state.
- `python3 tools/brain-mcp.py` — stdio MCP server for MCP-aware clients.

## Conventions

- Filenames: kebab-case, `.md`.
- Frontmatter: every wiki page starts with YAML (`title`, `kind`,
  `status`, `updated`, `sources` required; others optional).
- Cross-links: relative markdown links between wiki pages.
- Dates: absolute (`YYYY-MM-DD`), never relative.
- Voice: present tense, declarative.
- Don't invent. If a fact is not in a source you can cite, write
  *"(unknown — needs source)"*.
- Supersede, don't silently overwrite.

This is the kernel-flavoured AGENTS.md. Edit liberally to match your
organisation's shape — add active-scope rows, ingest conventions,
cross-product cluster names, etc.
'''
    (target / "AGENTS.md").write_text(agents_md)
    # Convenience symlink for tools that expect CLAUDE.md
    try:
        (target / "CLAUDE.md").symlink_to("AGENTS.md")
    except (FileExistsError, OSError):
        pass

    # wiki/ skeleton
    (target / "wiki").mkdir(exist_ok=True)
    (target / "wiki" / "_views").mkdir(exist_ok=True)
    (target / "wiki" / "_archive").mkdir(exist_ok=True)
    (target / "wiki" / "_overlaps").mkdir(exist_ok=True)
    (target / "wiki" / "_state").mkdir(exist_ok=True)
    (target / "wiki" / "brain").mkdir(exist_ok=True)
    (target / "wiki" / "brain" / "ai-suggestions").mkdir(exist_ok=True)
    (target / "wiki" / "brain" / "adrs").mkdir(exist_ok=True)
    (target / "wiki" / "brain" / "prds").mkdir(exist_ok=True)
    (target / "wiki" / "org").mkdir(exist_ok=True)
    (target / "wiki" / "org" / "ai-suggestions").mkdir(exist_ok=True)
    (target / "wiki" / "insights").mkdir(exist_ok=True)

    # wiki/index.md — minimal home with the contract sections
    home_md = f'''---
title: "{org} brain — home"
kind: meta
status: draft
updated: {today_utc().isoformat()}
sources: []
---

# {org} brain

This is an LLM-maintained knowledge base scaffolded by `brain.py init`.
Fill it with your organisation's content — per-repo shelves, cross-
product synthesis, decisions, initiatives.

## What changed

<!-- home-section: empty; maintained-by: /shape -->
*(empty — no `/shape` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Open initiatives

<!-- home-section: empty; maintained-by: /shape -->
*(empty — no `/shape` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Recent decisions

<!-- home-section: empty; maintained-by: /shape -->
*(empty — no `/shape` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Drift surface

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no `/groom` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Insights now

<!-- home-section: empty; maintained-by: /feedback -->
*(empty — no `/feedback` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Brain trajectory

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no `/groom` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Curated picks

<!-- home-section: empty; maintained-by: /groom -->
*(empty — no `/groom` run yet)*

[See more in `wiki/_views/by-kind.md`](_views/by-kind.md)

## Where to find things

- [Brain — meta level](brain/index.md)
- [Org — methodology + cross-product](org/index.md)
- Per-repo shelves arrive as you add them: `wiki/<repo>/index.md`
'''
    (target / "wiki" / "index.md").write_text(home_md)

    # wiki/brain/index.md
    brain_idx = f'''---
title: "Brain (meta level)"
kind: meta
status: draft
updated: {today_utc().isoformat()}
sources: []
---

# Brain — meta level

This shelf tracks how the brain itself operates: schema, conventions,
tooling, governance.

## ADRs
*(none yet — `/shape brain --record <decision>` to author)*

## PRDs
*(none yet — `/shape brain <pitch>` to author)*

## AI suggestions (drafts for human review)
*(none yet)*
'''
    (target / "wiki" / "brain" / "index.md").write_text(brain_idx)

    # wiki/org/index.md
    org_idx = f'''---
title: "{org} — methodology + cross-product"
kind: meta
status: draft
updated: {today_utc().isoformat()}
sources: []
---

# {org} — methodology + cross-product

This shelf tracks how {org} works as an organisation: process,
methodology, cross-product synthesis, competitor intel, compliance.

## Pages
*(none yet — fill as your organisation's shape becomes visible)*
'''
    (target / "wiki" / "org" / "index.md").write_text(org_idx)

    # log/log.md
    (target / "log").mkdir(exist_ok=True)
    (target / "log" / "log.md").write_text(
        f"# Brain operations log\n\n"
        f"{today_utc().isoformat()} init — brain scaffolded by `brain.py init` for {org}\n"
    )

    # sources/ — empty
    (target / "sources").mkdir(exist_ok=True)
    (target / "sources" / ".gitkeep").touch()

    # .gitignore
    (target / ".gitignore").write_text(
        "# brain-shell scaffold\n"
        ".env\n"
        ".env.*\n"
        "!.env.example\n"
        "*.swp\n"
        "*~\n"
        ".DS_Store\n"
        "__pycache__/\n"
        "*.pyc\n"
        "node_modules/\n"
        ".claude/worktrees/\n"
        ".claude/scheduled_tasks.lock\n"
        "wiki/_views/home-staleness.json\n"
    )

    # Run views once so wiki/_views/by-kind.md etc. exist (the home page
    # references them).
    saved_repo = (REPO, WIKI)
    globals()["REPO"] = target
    globals()["WIKI"] = target / "wiki"
    try:
        cmd_views(args)
    except Exception as exc:
        print(f"warning: initial views regen failed: {exc}", file=sys.stderr)
    finally:
        globals()["REPO"], globals()["WIKI"] = saved_repo

    print(f"brain shell scaffolded at: {target}", file=sys.stderr)
    print(f"  AGENTS.md / CLAUDE.md (symlink)")
    print(f"  wiki/index.md  (home)")
    print(f"  wiki/brain/index.md, wiki/org/index.md (sub-hubs)")
    print(f"  log/log.md (audit trail)")
    print(f"  sources/ (empty)")
    print(f"")
    print(f"  Note: tools/ is intentionally NOT copied — point this shell at")
    print(f"  an existing brain.py via $BRAIN_DIR or copy tools/ from the")
    print(f"  reference brain. The kernel-vs-content extraction is itself an")
    print(f"  open initiative tracked in")
    print(f"  wiki/brain/ai-suggestions/prds/extractable-brain-shell.md.")
    return 0


def _entry_calls_brain_hook(entry: dict) -> bool:
    """Heuristic: does this PreToolUse entry call brain-hook.sh?"""
    if not isinstance(entry, dict):
        return False
    for h in (entry.get("hooks") or []):
        if isinstance(h, dict):
            cmd = h.get("command") or ""
            if "brain-hook.sh" in cmd:
                return True
    if "brain-hook.sh" in (entry.get("command") or ""):
        return True
    return False


def cmd_search(args) -> int:
    """Hybrid search over the wiki/ synthesis layer.

    Combines keyword scoring (title weight 3×, body weight 1×) with a
    source-factor multiplier (cross-product 1.6× / permanent 1.4× /
    decisions 1.2× / ai-suggestions 0.75× / archive 0.3×) and a
    confidence-tier multiplier (high 1.3× / medium 1.0× / low 0.85×).
    Returns top-K matches.

    Per `wiki/brain/ai-suggestions/prds/hybrid-search-via-brain-py.md`.
    Semantic recall via mempalace is deferred to a follow-up; pure
    keyword + source-aware ranking is enough for v1.
    """
    SOURCE_FACTORS = [
        (re.compile(r"^wiki/org/cross-product/"), 1.6),
        (re.compile(r"^wiki/org/competitors/"), 1.4),
        (re.compile(r"^wiki/org/"), 1.5),
        (re.compile(r"^wiki/insights/"), 1.4),
        (re.compile(r"^wiki/brain/adrs/"), 1.4),
        (re.compile(r"^wiki/brain/prds/"), 1.3),
        (re.compile(r"^wiki/[^/]+/permanent/"), 1.4),
        (re.compile(r"^wiki/[^/]+/state\.md$"), 1.3),
        (re.compile(r"^wiki/[^/]+/epics/"), 1.3),
        (re.compile(r"^wiki/[^/]+/(adrs|prds)/"), 1.2),
        (re.compile(r"^wiki/[^/]+/build-notes/"), 1.0),
        (re.compile(r"^wiki/[^/]+/ai-suggestions/"), 0.75),
        (re.compile(r"^wiki/_archive/"), 0.3),
    ]
    CONFIDENCE_FACTORS = {"high": 1.3, "medium": 1.0, "low": 0.85}

    def source_factor(rel_path: str) -> float:
        for pat, factor in SOURCE_FACTORS:
            if pat.search(rel_path):
                return factor
        return 1.0

    def confidence_factor(meta: dict) -> float:
        return CONFIDENCE_FACTORS.get(meta.get("confidence"), 0.95)

    query_terms = [t.lower() for t in re.findall(r"\w+", args.query) if len(t) >= 2]
    if not query_terms:
        print(f"empty query terms after tokenisation: {args.query!r}", file=sys.stderr)
        return 2

    repo_filter = args.repo
    kind_filter = args.kind
    include_superseded = args.include_superseded
    top_k = args.top

    results = []
    for p in wiki_pages():
        parsed = parse(p)
        if parsed is None:
            continue
        meta, body = parsed
        rel = str(p.relative_to(WIKI))

        status = meta.get("status")
        if status in ("superseded", "archived") and not include_superseded:
            continue

        if kind_filter and meta.get("kind") != kind_filter:
            continue

        if repo_filter:
            page_repos = set(meta.get("repos") or []) | set(meta.get("affects") or [])
            if repo_filter not in page_repos and not rel.startswith(f"{repo_filter}/"):
                continue

        title = (meta.get("title") or "").lower()
        body_lower = body.lower()
        score = 0.0
        for term in query_terms:
            score += 3.0 * title.count(term)
            score += body_lower.count(term)
        if score == 0:
            continue

        score *= source_factor(rel)
        score *= confidence_factor(meta)

        # Build a short excerpt from the first body line containing any term
        excerpt = ""
        for line in body.splitlines():
            ll = line.lower()
            if any(t in ll for t in query_terms):
                excerpt = line.strip()[:160]
                break

        results.append({
            "path": rel,
            "title": meta.get("title", ""),
            "kind": meta.get("kind"),
            "confidence": meta.get("confidence"),
            "status": status,
            "score": round(score, 3),
            "excerpt": excerpt,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:top_k]

    if args.json:
        print(json.dumps({"query": args.query, "results": results}, indent=2))
        return 0 if results else 1

    if not results:
        print(f"no matches for: {args.query}", file=sys.stderr)
        return 1
    for r in results:
        marker = "[h]" if r["confidence"] == "high" else (
            "[l]" if r["confidence"] == "low" else "[m]"
        )
        print(f"{r['score']:6.2f}  {marker} {r['path']}")
        if r["title"]:
            print(f"        {r['title'][:120]}")
        if r["excerpt"]:
            print(f"        “{r['excerpt']}”")
    return 0


def cmd_reflection_check(args) -> int:
    """Detect drift between brain claims and target-repo state.

    Mechanical-only checks (deterministic, offline-safe).

    Each sub-check prints findings to stdout (one per line) and
    contributes to the exit code. Exit 0 if every requested
    check is clean; exit 1 if anything is flagged.

    Findings are warnings by default — the check surfaces drift,
    the human acts. CI integration should read the findings,
    not the exit code, until calibration is done.
    """
    which = (args.which or "all").lower()
    findings: list[str] = []

    pages_data: list[dict] = []  # cache for cross-check use
    pages_index: dict[str, dict] = {}

    def load_pages():
        nonlocal pages_data, pages_index
        if pages_data:
            return
        for p in wiki_pages():
            parsed = parse(p)
            if parsed is None:
                continue
            meta, body = parsed
            rel = str(p.relative_to(WIKI))
            pages_data.append({"path": rel, "meta": meta, "body": body, "abs": p})
            pages_index[rel] = pages_data[-1]

    def check_links() -> int:
        """Every wiki/ markdown link resolves to a real file."""
        n = 0
        for page in WIKI.rglob("*.md"):
            rel = page.relative_to(WIKI)
            if any(part.startswith("_") for part in rel.parts):
                continue
            text = page.read_text()
            for href in re.findall(r"\]\(([^)]+)\)", text):
                href = href.split("#", 1)[0].strip()
                if not href or href.endswith("/") or href.startswith(("http://", "https://", "mailto:", "~/")):
                    continue
                if not href.endswith(".md"):
                    continue
                target = (page.parent / href).resolve()
                try:
                    rel_target = target.relative_to(WIKI)
                except ValueError:
                    # link escapes wiki/ — out of scope
                    continue
                if not target.exists():
                    findings.append(
                        f"links: {rel} → broken link to {rel_target}"
                    )
                    n += 1
        return n

    def check_confidence_floor() -> int:
        """`confidence: high` pages whose `updated:` is > 30 days old."""
        load_pages()
        cutoff = today_utc() - dt.timedelta(days=30)
        n = 0
        for entry in pages_data:
            meta = entry["meta"]
            if meta.get("confidence") != "high":
                continue
            updated = meta.get("updated")
            if not updated:
                continue
            if isinstance(updated, str):
                try:
                    updated = dt.date.fromisoformat(updated)
                except ValueError:
                    continue
            if updated < cutoff:
                findings.append(
                    f"confidence-floor: {entry['path']} is confidence:high "
                    f"but updated:{updated} (>30d ago — needs refresh per "
                    f"AGENTS.md § Knowledge half-life)"
                )
                n += 1
        return n

    def check_active_scope() -> int:
        """AGENTS.md § Active scope table matches wiki/<repo>/ folders that exist."""
        agents = (REPO / "AGENTS.md").read_text()
        # Find entries in the active-scope table
        scope_section = re.search(
            r"###?\s*Active scope.*?(?=^##\s|\Z)",
            agents, re.MULTILINE | re.DOTALL,
        )
        if not scope_section:
            findings.append("active-scope: AGENTS.md missing § Active scope")
            return 1
        body = scope_section.group(0)
        # Crudely extract repo names from the table (first column rows)
        agents_repos = set()
        for line in body.splitlines():
            m = re.match(r"\|\s*`([\w-]+)`\s*\|", line)
            if m:
                agents_repos.add(m.group(1))
        # active sibling repos per the table — with active status
        # (matches both ``| `repo` | active   |`` and ``| `repo` | **active** |``)
        active_in_agents = set()
        for line in body.splitlines():
            m = re.match(r"\|\s*`([\w-]+)`\s*\|\s*(?:\*\*)?active(?:\*\*)?", line)
            if m:
                active_in_agents.add(m.group(1))
        # Walk wiki/ for top-level <repo>/ folders that have index.md
        wiki_repos = set()
        for child in WIKI.iterdir():
            if not child.is_dir():
                continue
            if child.name.startswith("_") or child.name == "org" or child.name == "brain" or child.name == "insights":
                continue
            if (child / "index.md").exists():
                wiki_repos.add(child.name)
        n = 0
        only_agents = active_in_agents - wiki_repos
        only_wiki = wiki_repos - active_in_agents
        for r in sorted(only_agents):
            findings.append(
                f"active-scope: {r} is **active** in AGENTS.md but no wiki/{r}/index.md exists"
            )
            n += 1
        for r in sorted(only_wiki):
            findings.append(
                f"active-scope: wiki/{r}/index.md exists but {r} is not **active** in AGENTS.md"
            )
            n += 1
        return n

    def check_supersedes_cycles() -> int:
        """`supersedes:` / `superseded_by:` chains have no cycles."""
        load_pages()
        graph: dict[str, str] = {}
        for entry in pages_data:
            sb = entry["meta"].get("superseded_by")
            if sb and isinstance(sb, str):
                graph[entry["path"]] = sb.strip()
        n = 0
        for start in list(graph):
            seen = [start]
            cur = start
            while cur in graph:
                cur = graph[cur]
                if cur in seen:
                    findings.append(
                        f"supersedes-cycles: cycle detected → {' → '.join(seen + [cur])}"
                    )
                    n += 1
                    break
                seen.append(cur)
                if len(seen) > 50:
                    findings.append(
                        f"supersedes-cycles: chain too long from {start} (>50)"
                    )
                    n += 1
                    break
        return n

    def check_page_size() -> int:
        """Pages > 500 lines are flagged as split candidates.

        Excludes content-driven cases:
        - `kind: epic` — umbrella structure inherently large.
        - `status: superseded` — redirect stubs / historical content.
        - `status: accepted` ADRs — committed decisions with full
          alternatives + consequences are content-driven.
        - `status: living` PRDs / reference pages — content-driven
          (per AGENTS.md § Scale conventions: *"aim for"* not
          *"must be"*).

        The threshold remains 500 but the *flag* fires only for
        `status: draft` content where size genuinely indicates the
        author should split before shipping.
        """
        load_pages()
        n = 0
        for entry in pages_data:
            kind = entry["meta"].get("kind")
            status = entry["meta"].get("status")
            if kind == "epic":
                continue
            if status in ("superseded", "archived"):
                continue
            # Living / accepted / shipped content is content-driven
            # by the time it's stable. Only drafts trigger the flag.
            if status not in ("draft", None):
                continue
            line_count = entry["body"].count("\n")
            if line_count > 500:
                findings.append(
                    f"page-size: {entry['path']} has {line_count} body lines "
                    f"(kind={kind}, status={status}); split candidate per "
                    f"AGENTS.md § Scale conventions"
                )
                n += 1
        return n

    def check_sources_exist() -> int:
        """Every non-URL `sources:` entry resolves on disk.

        Sibling-repo paths (~/projects/<repo>/...) are skipped
        if the sibling repo isn't on this machine. The full
        check lives in `brain.py check --no-net`; this is a
        thin pointer to that.
        """
        # delegate to existing cmd_check logic
        n = 0
        for entry in pages_data or (load_pages() or pages_data):
            for src in entry["meta"].get("sources") or []:
                if not isinstance(src, str):
                    continue
                if src.startswith(("http://", "https://")):
                    continue
                kind, msg = _check_path(src, entry["abs"])
                if kind == "broken":
                    findings.append(
                        f"sources-exist: {entry['path']} cites missing path: {src}"
                    )
                    n += 1
        return n

    def check_sync_drift() -> int:
        """For each sibling repo on disk, list how many commits HEAD is
        ahead of the recorded sync-cursor."""
        cursors_path = WIKI / "_state" / "sync-cursors.json"
        if not cursors_path.exists():
            return 0
        try:
            cursors = json.loads(cursors_path.read_text())
        except json.JSONDecodeError:
            findings.append("sync-drift: wiki/_state/sync-cursors.json unparseable")
            return 1
        n = 0
        for repo, cursor in (cursors.get("cursors") or cursors).items():
            if not isinstance(cursor, dict):
                continue
            sha = cursor.get("sha")
            if not sha:
                continue
            sibling = PROJECTS / repo
            if not (sibling / ".git").exists():
                continue
            try:
                count = subprocess.run(
                    ["git", "rev-list", f"{sha}..HEAD", "--count"],
                    cwd=sibling, capture_output=True, text=True, timeout=10,
                )
                if count.returncode != 0:
                    findings.append(
                        f"sync-drift: {repo} cursor SHA {sha[:8]} not reachable from HEAD "
                        f"(rebase / force-push? — re-set cursor)"
                    )
                    n += 1
                    continue
                ahead = int((count.stdout or "0").strip() or "0")
                if ahead > 50:
                    findings.append(
                        f"sync-drift: {repo} HEAD is {ahead} commits ahead of cursor "
                        f"({sha[:8]}); consider an incremental ingest pass"
                    )
                    n += 1
            except Exception:
                continue
        return n

    def check_epic_children() -> int:
        """`parent_epic:` references resolve and the epic's `## Children`
        section lists the child by slug."""
        load_pages()
        n = 0
        # Collect epics
        epics: dict[str, dict] = {}
        for entry in pages_data:
            if entry["meta"].get("kind") == "epic":
                slug = Path(entry["path"]).stem
                epics[slug] = entry
        for entry in pages_data:
            parent = entry["meta"].get("parent_epic")
            if not parent:
                continue
            if parent not in epics:
                findings.append(
                    f"epic-children: {entry['path']} claims parent_epic={parent!r} "
                    f"but no kind:epic page with that slug exists"
                )
                n += 1
                continue
            epic = epics[parent]
            child_slug = Path(entry["path"]).stem
            if child_slug not in epic["body"]:
                findings.append(
                    f"epic-children: {entry['path']} claims parent_epic={parent!r} "
                    f"but the epic page does not mention this child by slug "
                    f"({child_slug})"
                )
                n += 1
        return n

    def check_sources_immutability() -> int:
        """`sources/` tree should be additive-only (no modified files vs git
        baseline)."""
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", "HEAD", "--", "sources/"],
                cwd=REPO, capture_output=True, text=True, timeout=10,
            )
        except Exception as exc:
            findings.append(f"sources-immutability: git diff failed: {exc}")
            return 1
        modified = [
            line for line in (res.stdout or "").splitlines()
            if line.strip() and line.startswith("sources/")
        ]
        # Filter to truly modified (not new). `git diff HEAD --name-only` lists
        # both modified and new (untracked are NOT shown by HEAD diff). We
        # need git status to tell new from modified.
        if not modified:
            return 0
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain", "--", "sources/"],
                cwd=REPO, capture_output=True, text=True, timeout=10,
            )
        except Exception:
            status = None
        # Parse status: lines starting with " M" = modified tracked file
        truly_modified = []
        if status and status.returncode == 0:
            for ln in status.stdout.splitlines():
                code = ln[:2]
                path = ln[3:]
                if "M" in code and path.startswith("sources/"):
                    truly_modified.append(path)
        else:
            truly_modified = modified
        # README.md files document the shelf's conventions; they are
        # maintained docs, not source material — exempt from the
        # additive-only guarantee.
        truly_modified = [p for p in truly_modified
                          if Path(p).name != "README.md"]
        n = 0
        for path in truly_modified:
            findings.append(
                f"sources-immutability: {path} is modified relative to git "
                f"baseline (sources/ is additive-only per AGENTS.md)"
            )
            n += 1
        return n

    def check_repo_claims() -> int:
        """Heuristic brain↔repo truth check.

        Walks each page's body for `~/projects/<repo>/<path>` claims;
        if the sibling repo is on disk, verifies the path resolves.
        Skips claims about lines (`:42`) and ranges.

        Mechanical-only — no LLM verification of code semantics.
        """
        load_pages()
        n = 0
        # Match ~/projects/<repo>/<path> with optional :line suffix.
        # Lookahead excludes `.` so file extensions aren't truncated.
        rx = re.compile(
            r"~/projects/([\w-]+)/([\w./_-]+?)(?::\d+(?:-\d+)?)?(?=[\s`)\],]|$)",
            re.MULTILINE,
        )
        seen: set[tuple[str, str]] = set()  # (page_path, claimed_path)
        for entry in pages_data:
            for m in rx.finditer(entry["body"]):
                repo = m.group(1)
                rel_path = m.group(2)
                key = (entry["path"], f"{repo}/{rel_path}")
                if key in seen:
                    continue
                seen.add(key)
                sibling = PROJECTS / repo
                if not sibling.exists():
                    continue  # repo not on disk; skip
                target = sibling / rel_path
                if not target.exists():
                    findings.append(
                        f"repo-claims: {entry['path']} cites "
                        f"~/projects/{repo}/{rel_path} but the path does not "
                        f"exist in the sibling repo"
                    )
                    n += 1
        return n

    def check_internal_refs() -> int:
        """Every repo-path reference in docs/skills/templates resolves.

        The standalone guarantee: no file in the kernel surface may
        reference a repo path that doesn't exist. Complements
        check_links (wiki-internal markdown links) by covering the
        non-wiki surface — AGENTS.md, README.md, skills, commands,
        personas, templates, UI docs — and path mentions outside
        markdown link syntax (backticked paths, prose). Placeholder
        paths (`<repo>`, globs, YYYY dates) are skipped.
        """
        ref_re = re.compile(
            r'(?:\]\(|`|^|\s|"|\')'
            r'((?:\.\./)*(?:wiki|sources|tools|log|ui|\.claude|\.github)/'
            r'[A-Za-z0-9_./<>-]+?\.(?:md|py|sh|json|yml|mjs|astro))'
            r'(?:#[^)\s`]*)?(?:\)|`|\s|$|"|\')',
            re.M,
        )
        scan: set[Path] = {REPO / "AGENTS.md", REPO / "README.md"}
        for pattern in (".claude/**/*.md", "tools/**/*.md", "ui/*.md",
                        "ui/*.mjs", "wiki/**/*.md",
                        # UI source strings too — the onboarding deck
                        # leak (2026-07-12) hid inside a TS array the
                        # markdown-only sweep never read.
                        "ui/src/**/*.astro", "ui/src/**/*.mjs",
                        "ui/src/**/*.ts"):
            scan.update(REPO.glob(pattern))
        n = 0
        seen: set[tuple[str, str]] = set()
        for f in sorted(scan):
            rel_f = str(f.relative_to(REPO))
            if "node_modules" in rel_f or "_views" in rel_f or not f.exists():
                continue
            text = f.read_text(errors="ignore")
            for m in ref_re.finditer(text):
                raw = m.group(1)
                if "<" in raw or "*" in raw or "YYYY" in raw:
                    continue
                stripped = re.sub(r"^(\.\./)+", "", raw)
                # Tooling-managed surfaces (wiki/_state/, wiki/_views/,
                # wiki/_overlaps/, log/archive/) are created at runtime;
                # a documented path there is a contract, not a dangling
                # reference.
                if re.match(r"(wiki/_|log/archive/)", stripped):
                    continue
                if (f.parent / raw).resolve().exists() or (REPO / stripped).exists():
                    continue
                if (rel_f, raw) in seen:
                    continue
                seen.add((rel_f, raw))
                findings.append(
                    f"internal-refs: {rel_f} references {raw} which does "
                    f"not resolve inside the repo"
                )
                n += 1
        return n

    def check_denylist() -> int:
        """Machine-local content denylist (never committed).

        The standalone guarantee's other half: internal-refs catches
        dangling paths, but a client/org term leaking into the public
        kernel is prose, not a path. Operators keep one term per line
        in .reflection-denylist (git-ignored; BRAIN_DENYLIST
        overrides) — client names, internal repo names, anything that
        must never ship. Absent file → clean no-op, so the check is
        personal by construction: the terms themselves never enter
        the repo.
        """
        deny_path = Path(os.environ.get(
            "BRAIN_DENYLIST", REPO / ".reflection-denylist"))
        if not deny_path.exists():
            return 0
        terms = [ln.strip() for ln in deny_path.read_text().splitlines()
                 if ln.strip() and not ln.startswith("#")]
        if not terms:
            return 0
        n = 0
        skip_re = re.compile(
            r"node_modules|\.git/|_views/|\.build-cache|dist/|"
            r"\.astro/|\.env|\.reflection-denylist")
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True,
            text=True).stdout.splitlines()
        for rel in tracked:
            if skip_re.search(rel):
                continue
            f = REPO / rel
            if not f.is_file():
                continue
            try:
                text = f.read_text(errors="ignore").lower()
            except OSError:
                continue
            for term in terms:
                if term.lower() in text:
                    findings.append(
                        f"denylist: {rel} contains a deny-listed term "
                        f"(#{terms.index(term) + 1} in "
                        f"{deny_path.name})")
                    n += 1
        return n

    runners = {
        "links": check_links,
        "denylist": check_denylist,
        "confidence-floor": check_confidence_floor,
        "active-scope": check_active_scope,
        "supersedes-cycles": check_supersedes_cycles,
        "page-size": check_page_size,
        "sources-exist": check_sources_exist,
        "sync-drift": check_sync_drift,
        "epic-children": check_epic_children,
        "sources-immutability": check_sources_immutability,
        "repo-claims": check_repo_claims,
        "internal-refs": check_internal_refs,
    }

    if which == "all":
        targets = list(runners)
    elif which in runners:
        targets = [which]
    else:
        print(f"unknown reflection-check: {which!r}", file=sys.stderr)
        print(f"available: all, {', '.join(runners)}", file=sys.stderr)
        return 2

    total = 0
    for name in targets:
        before = len(findings)
        runners[name]()
        delta = len(findings) - before
        print(f"# {name}: {delta} finding(s)", file=sys.stderr)
        total += delta

    for f in findings:
        print(f)

    print(f"# reflection-check {which}: {total} total finding(s)", file=sys.stderr)
    return 0 if total == 0 else 1


def main() -> int:
    version = "(unversioned)"
    version_file = REPO / "VERSION"
    if version_file.exists():
        version = version_file.read_text().strip()
    ap = argparse.ArgumentParser(prog="brain")
    ap.add_argument("--version", action="version",
                    version=f"brain {version}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="check frontmatter conformance").set_defaults(
        func=cmd_validate
    )

    ap_check = sub.add_parser("check",
                              help="verify sources: citations resolve")
    ap_check.add_argument("--no-net", action="store_true",
                          help="skip URL checks")
    ap_check.add_argument("--page",
                          help="only check one page (wiki-relative path)")
    ap_check.add_argument("-v", "--verbose", action="store_true",
                          help="list skipped (sibling-repo) citations")
    ap_check.set_defaults(func=cmd_check)

    sub.add_parser("stats", help="corpus health").set_defaults(func=cmd_stats)
    sub.add_parser("views", help="emit auto-generated index pages").set_defaults(
        func=cmd_views
    )

    ap_cov = sub.add_parser("coverage", help="repo coverage gap analysis")
    ap_cov.add_argument("repo", help="sibling repo name (under $BRAIN_PROJECTS_ROOT, default ~/projects/)")
    ap_cov.set_defaults(func=cmd_coverage)

    ap_serve = sub.add_parser("serve", help="read-only HTTP API")
    ap_serve.add_argument("--host", default="127.0.0.1")
    ap_serve.add_argument("--port", type=int,
                          default=int(os.environ.get("BRAIN_PORT", 8765)))
    ap_serve.add_argument("--workbench", action="store_true",
                          help="deprecated no-op: the app page mounts "
                               "whenever BRAIN_SERVING is unset")
    ap_serve.set_defaults(func=cmd_serve)

    ap_prom = sub.add_parser("promote", help="scaffold initiative from insight")
    ap_prom.add_argument("insight", help="wiki-relative path to insight page")
    ap_prom.add_argument("--slug", help="initiative slug (default: <insight>-initiative)")
    ap_prom.set_defaults(func=cmd_promote)

    ap_cl = sub.add_parser("cluster", help="TF-IDF + HDBSCAN clustering")
    ap_cl.add_argument("--min-cluster", type=int, default=2,
                       help="HDBSCAN min_cluster_size (default 2)")
    ap_cl.add_argument("--min-corpus", type=int, default=10,
                       help="skip if fewer than this many pages (default 10)")
    ap_cl.set_defaults(func=cmd_cluster)

    sub.add_parser("check-no-notion-writes",
                   help="enforce Notion read-only doctrine"
                   ).set_defaults(func=cmd_check_no_notion_writes)

    ap_chf = sub.add_parser("check-home-fresh",
                            help="verify wiki/ edits include a wiki/index.md edit")
    ap_chf.add_argument("--base", default="origin/main",
                        help="base ref for the diff (default: origin/main)")
    ap_chf.set_defaults(func=cmd_check_home_fresh)

    ap_crf = sub.add_parser("check-readme-fresh",
                            help="verify significant changes include a README.md edit")
    ap_crf.add_argument("--base", default="origin/main",
                        help="base ref for the diff (default: origin/main)")
    ap_crf.set_defaults(func=cmd_check_readme_fresh)

    ap_idx = sub.add_parser("index",
                            help="rebuild the derived SQLite index "
                                 "(gitignored, disposable)")
    ap_idx.add_argument("--schema", action="store_true",
                        help="print the documented schema")
    ap_idx.set_defaults(func=cmd_index)

    ap_q = sub.add_parser("query",
                          help="read-only SQL over the derived index")
    ap_q.add_argument("sql")
    ap_q.add_argument("--limit", type=int, default=200)
    ap_q.add_argument("--json", action="store_true")
    ap_q.set_defaults(func=cmd_query)

    ap_page = sub.add_parser("page",
                             help="read a page WITH its graph context "
                                  "(backlinks, edges, recent activity)")
    ap_page.add_argument("path", help="wiki-relative path")
    ap_page.add_argument("--context-only", dest="context_only",
                         action="store_true")
    ap_page.set_defaults(func=cmd_page)

    ap_lint = sub.add_parser("lint-page",
                             help="fast single-page warnings for "
                                  "write-time feedback (hook-invoked)")
    ap_lint.add_argument("path")
    ap_lint.set_defaults(func=cmd_lint_page)

    ap_links = sub.add_parser("links",
                              help="link-graph health: orphans / hubs / "
                                   "dead-ends / suggested links")
    ap_links.add_argument("--json", action="store_true")
    ap_links.set_defaults(func=cmd_links)

    ap_setup = sub.add_parser("setup",
                              help="one-command bootstrap for a fresh "
                                   "checkout (idempotent)")
    ap_setup.add_argument("--org", default="", help="organisation name")
    ap_setup.add_argument("--repos", default="",
                          help="comma-separated active repos")
    ap_setup.add_argument("--yes", action="store_true",
                          help="accept every optional step")
    ap_setup.add_argument("--dry-run", dest="dry_run", action="store_true",
                          help="print the plan; change nothing")
    ap_setup.set_defaults(func=cmd_setup)

    ap_ia = sub.add_parser("install-agent",
                           help="register the brain's MCP server for a "
                                "harness (claude/cursor/codex/opencode)")
    ap_ia.add_argument("harness", nargs="?", default="")
    ap_ia.add_argument("--all", action="store_true")
    ap_ia.set_defaults(func=cmd_install_agent)

    ap_doc = sub.add_parser("doctor",
                            help="one-screen health checklist "
                                 "(exit 1 on failing checks)")
    ap_doc.add_argument("--json", action="store_true")
    ap_doc.set_defaults(func=cmd_doctor)

    ap_ib = sub.add_parser("inbox",
                           help="the tend queue at wiki/_state/inbox/ — "
                                "producers add items, /tend digests them")
    ib_sub = ap_ib.add_subparsers(dest="op", required=True)
    ib_add = ib_sub.add_parser("add", help="queue an item (idempotent on --id)")
    ib_add.add_argument("--id", required=True,
                        help="dedup key (lowercase slug); re-adding is a no-op")
    ib_add.add_argument("--kind", required=True,
                        choices=sorted(INBOX_KINDS))
    ib_add.add_argument("--summary", required=True,
                        help="one line: what needs tending and why")
    ib_add.add_argument("--route", default="",
                        help="suggested skill invocation (e.g. '/in <source>')")
    ib_add.add_argument("--priority", default="normal",
                        choices=sorted(INBOX_PRIORITIES))
    ib_add.add_argument("--source", default="",
                        help="path or URL the item is about")
    ib_add.add_argument("--produced-by", dest="produced_by", default="",
                        help="producer name (defaults to 'operator')")
    ib_add.add_argument("--update", action="store_true",
                        help="upsert: refresh summary/route on an existing id")
    ib_list = ib_sub.add_parser("list", help="pending items, priority-ordered")
    ib_list.add_argument("--json", action="store_true")
    ib_sub.add_parser("summary",
                      help="one-line count for session-start surfacing")
    ib_done = ib_sub.add_parser("done", help="clear a digested item")
    ib_judge = ib_sub.add_parser(
        "judge", help="stamp an attention verdict on an item (in-session "
                      "only; the briefing's Needs-you band reads it)")
    ib_judge.add_argument("id")
    ib_judge.add_argument("--attention", required=True,
                          choices=ATTENTION_VERDICTS)
    ib_judge.add_argument("--reason", required=True,
                          help="one line, traceable, no raw payloads")
    ib_grade = ib_sub.add_parser(
        "grade", help="operator grades a verdict (useful|noise) — "
                      "calibration for future judgement")
    ib_grade.add_argument("id")
    ib_grade.add_argument("--grade", required=True,
                          choices=("useful", "noise"))
    ib_grade.add_argument("--note", default="")
    ib_done.add_argument("id")
    ap_ib.set_defaults(func=cmd_inbox)

    ap_sc = sub.add_parser("sync-cursor",
                           help="manage sibling-repo sync cursors "
                                "(wiki/_state/sync-cursors.json)")
    sc_sub = ap_sc.add_subparsers(dest="op", required=True)
    sc_get = sc_sub.add_parser("get",
                               help="print cursor(s); omit <repo> to print all")
    sc_get.add_argument("repo", nargs="?",
                        help="sibling repo name (e.g. app)")
    sc_set = sc_sub.add_parser("set",
                               help="advance cursor to sibling repo's HEAD")
    sc_set.add_argument("repo")
    sc_set.add_argument("--scope", default=None,
                        help="full-tree | <relative path> (default: full-tree)")
    sc_set.add_argument("--synced-by", dest="synced_by", default=None,
                        help="audit reference (PR # or log line) for this advance")
    sc_set.add_argument("--force", action="store_true",
                        help="override sibling-repo-handling refusal "
                             "(branch != main, dirty tree)")
    sc_diff = sc_sub.add_parser("diff",
                                help="list paths changed in sibling repo since "
                                     "the cursor's SHA")
    sc_diff.add_argument("repo")
    ap_sc.set_defaults(func=cmd_sync_cursor)

    ap_eff = sub.add_parser("efforts",
                            help="manage in-flight effort registry "
                                 "(wiki/_state/efforts/<slug>.json)")
    eff_sub = ap_eff.add_subparsers(dest="op", required=True)
    eff_list = eff_sub.add_parser("list", help="list all effort records")
    eff_list.add_argument("--status", default=None,
                          help="filter by status (in-flight | merged | abandoned | orphaned)")
    eff_list.add_argument("--json", action="store_true",
                          help="emit JSON instead of the tab-separated table")
    eff_get = eff_sub.add_parser("get", help="print one effort record as JSON")
    eff_get.add_argument("slug")
    eff_set = eff_sub.add_parser("set", help="create or update an effort record")
    eff_set.add_argument("slug")
    eff_set.add_argument("--brain-branch", default=None)
    eff_set.add_argument("--brain-worktree", default=None,
                         help="absolute path to the brain worktree")
    eff_set.add_argument("--targets", nargs="*", default=None,
                         help="target sibling repos (e.g. app api)")
    eff_set.add_argument("--target-branch", action="append", dest="target_branches",
                         type=lambda s: tuple(s.split("=", 1)), default=None,
                         metavar="REPO=BRANCH",
                         help="repeatable: per-target sibling-repo branch")
    eff_set.add_argument("--target-worktree", action="append", dest="target_worktrees",
                         type=lambda s: tuple(s.split("=", 1)), default=None,
                         metavar="REPO=PATH",
                         help="repeatable: per-target sibling-repo worktree path")
    eff_set.add_argument("--brain-pr", default=None,
                         help="brain PR URL or number")
    eff_set.add_argument("--target-pr", action="append", dest="target_prs",
                        type=lambda s: tuple(s.split("=", 1)), default=None,
                        metavar="REPO=PR",
                        help="repeatable: per-target sibling-repo PR URL or number")
    eff_set.add_argument("--notes", default=None)
    eff_set.add_argument("--status", default=None,
                         choices=["in-flight", "merged", "abandoned", "orphaned"])
    eff_set.add_argument("--owner-agent-id", dest="owner_agent_id", default=None,
                         help="opaque identifier of the dispatched owner subagent "
                              "(per parallel-execution-agent-teams ADR)")
    eff_set.add_argument("--owner-dispatched-at", dest="owner_dispatched_at",
                         default=None,
                         help="ISO-8601 UTC timestamp the owner subagent was dispatched")
    eff_set.add_argument("--owner-state", dest="owner_state", default=None,
                         choices=["active", "completed", "blocked", "none-dispatched"],
                         help="lifecycle state of the dispatched owner subagent")
    eff_set.add_argument("--helpers-dispatched", dest="helpers_dispatched",
                         type=int, default=None,
                         help="count of helper subagents the owner has fanned out")
    eff_mark = eff_sub.add_parser("mark", help="set an effort's status")
    eff_mark.add_argument("slug")
    eff_mark.add_argument("status",
                          choices=["in-flight", "merged", "abandoned", "orphaned"])
    ap_eff.set_defaults(func=cmd_efforts)

    ap_reb = sub.add_parser("rebase",
                            help="cheap-rebase current branch onto origin/main, "
                                 "auto-resolving wiki/_views/ via regen")
    ap_reb.add_argument("--base", default="origin/main",
                        help="base ref (default: origin/main)")
    ap_reb.set_defaults(func=cmd_rebase)

    sub.add_parser("snapshot",
                   help="write a brain corpus snapshot to wiki/_views/snapshots/"
                   ).set_defaults(func=cmd_snapshot)

    sub.add_parser("rotate-log",
                   help="rotate log/log.md to log/archive/ once it crosses the threshold"
                   ).set_defaults(func=cmd_rotate_log)

    ap_pers = sub.add_parser("personas",
                             help="infer the RFC persona pool for a wiki page")
    ap_pers.add_argument("page", help="wiki-relative path to the page")
    ap_pers.set_defaults(func=cmd_personas)

    ap_inst = sub.add_parser(
        "install-sibling",
        help="install the brain's managed block + PreToolUse hook into a sibling repo "
             "(idempotent; --uninstall to remove)"
    )
    ap_inst.add_argument("repo", nargs="?",
                         help="sibling repo name (e.g. app); omit with --all")
    ap_inst.add_argument("--all", dest="all_active", action="store_true",
                         help="install into every active sibling repo on disk")
    ap_inst.add_argument("--uninstall", action="store_true",
                         help="remove the managed block + hook + settings entry")
    ap_inst.add_argument("--dry-run", action="store_true",
                         help="print what would be written without modifying disk")
    ap_inst.set_defaults(func=cmd_install_sibling)

    sub.add_parser(
        "status",
        help="brain-wide status dashboard (reads wiki/_state/*.json + corpus)"
    ).set_defaults(func=cmd_status)

    ap_verify = sub.add_parser(
        "verify-claims",
        help="extract verifiable claims (paths, version-pins, identifiers) "
             "from a wiki page; emit a structured manifest the consumer "
             "(agent / LLM / operator) can verify against sibling-repo source"
    )
    ap_verify.add_argument("page",
                           help="wiki-relative path (e.g. <repo>/permanent/architecture/index.md)")
    ap_verify.add_argument("--json", action="store_true",
                           help="emit JSON for tool consumers")
    ap_verify.set_defaults(func=cmd_verify_claims)

    ap_sched = sub.add_parser(
        "schedule",
        help="manage the declarative schedule at brain-schedule.yml"
    )
    ap_sched.add_argument("op", nargs="?", default="list",
                          choices=["list", "run", "run-due"],
                          help="list (default) | run --target <op> | run-due")
    ap_sched.add_argument("--target",
                          help="operation name when op=run")
    ap_sched.set_defaults(func=cmd_schedule)

    ap_init = sub.add_parser(
        "init",
        help="scaffold an empty brain shell at <path> (AGENTS.md + wiki/ "
             "skeleton + log/ + sources/) — for new organisations adopting "
             "the brain pattern"
    )
    ap_init.add_argument("path", help="directory to scaffold the brain into")
    ap_init.add_argument("--org", default=None,
                         help="organisation name (default: '<your-organisation>')")
    ap_init.add_argument("--force", action="store_true",
                         help="scaffold even if the target directory is non-empty")
    ap_init.add_argument("--full", action="store_true",
                         help="birth a complete instance: kernel manifest "
                              "copy + fresh scaffold (per the "
                              "kernel-manifest-instancing ADR)")
    ap_init.set_defaults(func=cmd_init)

    ap_search = sub.add_parser(
        "search",
        help="hybrid search over the wiki/ synthesis layer "
             "(keyword + source-factor + confidence-tier ranking)"
    )
    ap_search.add_argument("query", help="search terms")
    ap_search.add_argument("--top", type=int, default=10,
                           help="max results to return (default: 10)")
    ap_search.add_argument("--repo",
                           help="filter to pages about/affecting this repo")
    ap_search.add_argument("--kind",
                           choices=["reference", "initiative", "decision", "entity",
                                    "meta", "overlap", "insight", "epic"],
                           help="filter to pages of this kind")
    ap_search.add_argument("--include-superseded", action="store_true",
                           help="include superseded/archived pages")
    ap_search.add_argument("--json", action="store_true",
                           help="emit JSON output (for tool consumers)")
    ap_search.set_defaults(func=cmd_search)

    ap_refl = sub.add_parser(
        "reflection-check",
        help="detect drift between brain claims and target-repo state "
             "(links, confidence-floor age, active-scope, supersedes-cycles, "
             "page-size, sources-exist). Surfaces findings; exit 1 if any."
    )
    ap_refl.add_argument("which", nargs="?", default="all",
                         help="which check to run: links | confidence-floor | "
                              "active-scope | supersedes-cycles | page-size | "
                              "sources-exist | sync-drift | epic-children | "
                              "sources-immutability | repo-claims | all "
                              "(default: all)")
    ap_refl.set_defaults(func=cmd_reflection_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
