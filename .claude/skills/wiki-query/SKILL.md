---
name: wiki-query
description: Answer a question from the brain — consult index.md, read candidate pages, fall back to mempalace for verbatim/cross-conversation context, answer with citations to wiki pages and source paths, and file any reusable reasoning back into the wiki. Load when the user asks a factual or contextual question that the brain plausibly knows the answer to ("what is X", "where do we...", "why did we decide...", "have we discussed...").
---

# Query the brain

The brain is an LLM-maintained wiki at `~/projects/brain`. It points at raw
sources (sibling repos, Notion exports, ad-hoc notes) and at a mempalace
verbatim index for cross-conversation/source recall.

## Protocol

### 1. Start with `wiki/index.md`

Open it. Skim section headings and one-line hooks for plausible candidates.
Don't grep blindly — the index exists so the agent doesn't have to.

### 2. Read candidate pages

Read them in full, including their frontmatter `sources:` block. Chase
cross-links that look load-bearing.

### 3. Reach for mempalace when the wiki is thin

The wiki is a *synthesis*; mempalace is a read-only retrieval surface over
whatever was previously mined. Use it when:

- The wiki cites a long source and you need the exact wording.
- The wiki is silent on the question and you suspect prior conversations
  or source files cover it.
- You want to verify the wiki's claim against the source.

```bash
mempalace search "<phrasing close to what the source would say>"
mempalace status   # which wings exist; treat counts as a snapshot, not live
```

Mention the search key in your answer so the user can rerun it. The palace
is *not* refreshed automatically — mining is intentionally not part of the
active workflow yet, so a miss is "not in the snapshot," not "doesn't exist."

### 4. Answer with citations

Every non-trivial claim cites either:

- A wiki page (`wiki/<repo>/permanent/architecture.md#stack`)
- A source path (`~/projects/<repo>/AGENTS.md`)
- A mempalace search key (`mempalace search "..."`)

If you can't cite anything, say so explicitly: *"the brain doesn't cover
this — mempalace returned nothing relevant either."* Don't invent.

### 5. File reusable reasoning back

If answering required synthesis you'd want again, the answer should not
remain only in this chat. Either:

- Edit the relevant wiki page to incorporate the conclusion (with citation),
  update its `updated:` date, and append a `log/log.md` line:
  `YYYY-MM-DD query — <question> → <pages updated>`.
- Or, if the synthesis spans pages that don't exist yet, run the
  `wiki-ingest` skill on the conversation as the "source" — same protocol.

If the answer is purely retrieval (no synthesis), don't pollute the wiki.
The wiki is for understanding, not for chat logs.
