---
name: palace-mine
description: Mine a source into mempalace so it becomes searchable as verbatim retrieval for the wiki — pick projects vs convos mode, split mega-files first if needed, run `mempalace mine` against the right wing, verify with `mempalace status`, log the run. Sub-skill of `/in`; the user-facing command is `/in` (or `mine: <target>` to force mining only). Load when the user says "mine", "feed the palace", "refresh the palace", or otherwise asks to add fresh content to mempalace (distinct from wiki-ingest, which writes wiki pages).
---

# Mine a source into mempalace

You are working in `~/projects/brain`. mempalace is the verbatim/semantic
retrieval layer underneath `wiki/`. Mining is the operation that puts fresh
content *into* the palace; ingesting is the operation that synthesises wiki
pages *on top of* it.

The palace lives at `~/.mempalace/palace/` (machine-global, shared across
projects). Wings are top-level partitions — by convention, one wing per
sibling repo or one wing per conversation corpus. Run `mempalace status` to
see the current layout before mining.

## Protocol

### 1. Decide what to mine and pick a mode

Ask the user (or infer from the request) which of these the source is:

| Source                                          | Mode        | Typical wing                  |
|-------------------------------------------------|-------------|-------------------------------|
| Sibling repo under `~/projects/<repo>`          | `projects`  | `<repo>`                      |
| `sources/notion/`, `sources/notes/`, `sources/web/` inside the brain | `projects`  | `brain`                       |
| Claude Code transcripts (`~/.claude/projects/<slug>/`) | `convos`    | name of the project they cover (e.g. `app`) |
| Claude.ai / ChatGPT / Slack export directory    | `convos`    | something descriptive (`claude-ai`, `slack-eng`) |

`projects` mode reads code/docs (respects `.gitignore` by default). `convos`
mode reads chat exports. If unsure, `mempalace mine --help` lists the flags.

### 2. Confirm the wing

Default wing = directory name. Override with `--wing <name>` so the new
drawers land alongside the right corpus rather than creating a stray wing.
Check `mempalace status` to see which wings already exist.

### 3. Split mega-files first when mining conversations

Concatenated transcript files trip the miner. For `convos` mode, first run:

```
mempalace split <dir> --dry-run
```

If the dry run reports files to split, run it again without `--dry-run`.
Skip this step for `projects` mode.

### 4. Dry-run the mine before committing

```
mempalace mine <dir> [--mode convos] [--wing <name>] --dry-run
```

Read the file count and any warnings. If the count is wildly off (e.g. it's
about to scan node_modules), refine with `--include-ignored` or pick a
narrower directory rather than running the full mine.

### 5. Run the mine

```
mempalace mine <dir> [--mode convos] [--wing <name>] [--agent muhamed]
```

For convo extraction that should auto-classify into decisions / milestones /
problems, add `--extract general`. Otherwise the default `exchange`
extraction is fine.

The mine may take a while on large corpora. Stream the output; don't sleep
on it.

### 6. Verify

```
mempalace status
```

Confirm the wing's drawer count moved by roughly what the dry-run predicted.
Spot-check one query: `mempalace search "<phrase you expect to be in there>"`
and confirm it returns a hit from the new wing.

### 7. Log the run

Append one line to `log/log.md`, newest at the bottom:

```
YYYY-MM-DD mine — <dir> → wing:<name> (<delta> drawers, mode:<projects|convos>)
```

Use today's absolute date. If the mine was a no-op (idempotent re-run,
delta 0), log it anyway — that's still useful provenance.

## What mining is *not*

- Not a wiki edit. Mining never touches `wiki/`. If the user wants the
  source reflected in wiki pages too, follow `/mine` with `/ingest`.
- Not authoritative. The palace is a retrieval surface; the wiki is the
  synthesis. Mined content is only as good as its sources, and re-mines
  overwrite — treat it as a refreshable cache, not a record.
- Not for binaries. Skip anything binary; reference it from a wiki page if
  it matters.

## Done check

- [ ] Mode and wing are explicit (no accidental new wings).
- [ ] For `convos` mode: split was considered.
- [ ] Dry run was inspected before the real mine.
- [ ] `mempalace status` confirms drawers landed in the expected wing.
- [ ] At least one `mempalace search` returns a hit from the new content.
- [ ] `log/log.md` has a new line for this mine.
