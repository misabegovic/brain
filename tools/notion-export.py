#!/usr/bin/env python3
"""
Export Notion pages into ../sources/notion/ as markdown.

Usage:
    NOTION_TOKEN=secret_xxx ./tools/notion-export.py <page-id-or-url> [...]

Each given page (and its child pages, recursively) lands at
sources/notion/<slug>--<short-id>.md with YAML frontmatter that records the
Notion URL, title, and pull date. The wiki layer above sources/ cites these
files like any other raw source.

Prereqs:
  1. Create an internal integration at https://www.notion.so/my-integrations
  2. Share the pages/databases you want to export with that integration.
  3. Export NOTION_TOKEN with the integration's secret.
  4. Run this script with the venv interpreter that has notion-client:
       ~/.local/share/mempalace-venv/bin/python3 tools/notion-export.py <page>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

from notion_client import Client


REPO_ROOT = Path(__file__).resolve().parent.parent
NOTION_DIR = REPO_ROOT / "sources" / "notion"


def page_id(arg: str) -> str:
    """Accept either a bare ID, a dashed UUID, or a full Notion URL."""
    m = re.search(r"([0-9a-fA-F]{32})", arg.replace("-", ""))
    if not m:
        raise SystemExit(f"could not parse a Notion id from {arg!r}")
    raw = m.group(1).lower()
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "untitled"


def rich_text(rt: list[dict]) -> str:
    parts = []
    for span in rt:
        t = span.get("plain_text", "")
        ann = span.get("annotations") or {}
        if ann.get("code"):
            t = f"`{t}`"
        if ann.get("bold"):
            t = f"**{t}**"
        if ann.get("italic"):
            t = f"*{t}*"
        if ann.get("strikethrough"):
            t = f"~~{t}~~"
        href = span.get("href")
        if href:
            t = f"[{t}]({href})"
        parts.append(t)
    return "".join(parts)


def render_blocks(client: Client, parent_id: str, depth: int = 0) -> list[str]:
    out: list[str] = []
    cursor = None
    indent = "  " * depth
    while True:
        kwargs = {"block_id": parent_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.blocks.children.list(**kwargs)
        for b in resp["results"]:
            t = b["type"]
            data = b[t]
            text = rich_text(data.get("rich_text", [])) if isinstance(data, dict) else ""
            if t == "paragraph":
                out.append(f"{indent}{text}" if text else "")
            elif t in ("heading_1", "heading_2", "heading_3"):
                level = int(t[-1])
                out.append(f"{'#' * level} {text}")
            elif t == "bulleted_list_item":
                out.append(f"{indent}- {text}")
            elif t == "numbered_list_item":
                out.append(f"{indent}1. {text}")
            elif t == "to_do":
                box = "[x]" if data.get("checked") else "[ ]"
                out.append(f"{indent}- {box} {text}")
            elif t == "quote":
                out.append(f"{indent}> {text}")
            elif t == "callout":
                icon = (data.get("icon") or {}).get("emoji", "")
                out.append(f"{indent}> {icon} {text}".rstrip())
            elif t == "code":
                lang = data.get("language", "")
                out.append(f"```{lang}\n{text}\n```")
            elif t == "divider":
                out.append("---")
            elif t == "toggle":
                out.append(f"{indent}- {text}")
            elif t == "child_page":
                title = data.get("title", "untitled")
                out.append(f"{indent}- [child page: {title}](./{slugify(title)}--{b['id'][:8]}.md)")
            elif t == "image":
                src = (data.get("file") or data.get("external") or {}).get("url", "")
                cap = rich_text(data.get("caption", []))
                out.append(f"![{cap}]({src})")
            elif t == "bookmark" or t == "embed":
                url = data.get("url", "")
                out.append(f"<{url}>")
            else:
                out.append(f"<!-- unsupported block: {t} -->")

            if b.get("has_children") and t not in ("child_page",):
                child = render_blocks(client, b["id"], depth + 1)
                out.extend(child)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return out


def export_page(client: Client, pid: str, recurse_children: bool) -> Path:
    page = client.pages.retrieve(page_id=pid)
    title_prop = next(
        (v for v in page["properties"].values() if v.get("type") == "title"),
        None,
    )
    title = "untitled"
    if title_prop:
        title = rich_text(title_prop.get("title", [])) or "untitled"

    NOTION_DIR.mkdir(parents=True, exist_ok=True)
    short = pid.replace("-", "")[:8]
    fname = f"{slugify(title)}--{short}.md"
    out_path = NOTION_DIR / fname

    body = render_blocks(client, pid)
    fm = "\n".join(
        [
            "---",
            f"title: {title}",
            f"notion_url: {page.get('url', '')}",
            f"notion_id: {pid}",
            f"pulled: {date.today().isoformat()}",
            "---",
            "",
        ]
    )
    out_path.write_text(fm + "\n".join(body) + "\n")
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")

    if recurse_children:
        cursor = None
        while True:
            kwargs = {"block_id": pid, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            resp = client.blocks.children.list(**kwargs)
            for b in resp["results"]:
                if b["type"] == "child_page":
                    export_page(client, b["id"], recurse_children=True)
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")

    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Export Notion pages to sources/notion/")
    ap.add_argument("pages", nargs="+", help="Notion page IDs or URLs")
    ap.add_argument(
        "--no-recurse",
        action="store_true",
        help="Don't recurse into child pages",
    )
    args = ap.parse_args()

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("error: NOTION_TOKEN env var is required", file=sys.stderr)
        return 2
    client = Client(auth=token)

    for arg in args.pages:
        export_page(client, page_id(arg), recurse_children=not args.no_recurse)
    return 0


if __name__ == "__main__":
    sys.exit(main())
