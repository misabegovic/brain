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

### 3b. Reach for the code substrate when the question is structural

*"What does this repo contain"*, *"who calls X"*, *"what breaks if I
change X"*, *"how coupled is X"* — the substrate answers these
deterministically where the wiki answers them from synthesis. `brain.py structure findings --repo <repo>` always answers; `brain.py enola findings` / `enola impact <symbol>` add call graphs where the binary is installed. Both skip cleanly when absent — a named skip, never a silent pass. And for *"which decisions govern this file?"* or *"what code does this page cover?"*, `brain.py enola govern <target>` answers in either direction with the relation trail attached — pages compile into the graph as knowledge nodes, so governance is a lookup, not archaeology. It answers *no knowledge pages compiled* until the pinned enola release carries the mdintent extractor; that reply is a named skip, not an error.

*"When did X appear"*, *"which change introduced this cycle"* — these are **temporal**, and a snapshot cannot answer them however good it is. `brain.py enola history blame <name-or-path> <repo>` reports when something entered the architecture and when it left; `history log` walks the recorded revisions and `history show <rev>` expands one. Reach for these before `git log -S`, which reconstructs the same answer from text and misses the structural half. Experimental upstream — treat the output as a lead to confirm, not as a citable fact.

Prefer the substrate *first* for these and the wiki for the narrative
around the answer: the wiki says why a thing exists, the substrate says
what actually touches it, and where they disagree the disagreement is
itself the finding — surface it rather than picking a side. Findings are
candidates to verify; never relay one as fact without confirming it
against the code.

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
