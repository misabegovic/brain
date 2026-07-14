---
title: "How the three ideas compose — a conversational, provenance-aware knowledge graph grounded in deterministic facts"
kind: topic
status: living
updated: 2026-07-14
confidence: low
summary: >
  The async conversation surface, the deterministic structure
  connector, and edge-provenance tags aren't three features — they're
  a loop. Provenance is the connective tissue: the connector emits
  EXTRACTED facts, synthesis adds INFERRED edges, drift flags
  AMBIGUOUS, and the conversation surface routes AMBIGUOUS to a human.
  Sequence it provenance → connector → conversation; the conversation
  surface earns its build only after the other two give it something
  worth discussing.
sources:
  - ../ai-suggestions/prds/conversation-surface-over-inbox.md
  - ../ai-suggestions/prds/deterministic-structure-connector.md
  - ../ai-suggestions/prds/edge-provenance-tags.md
  - ../../../sources/research/2026-07-14--enola-deterministic-architecture-extractor.md
  - ../../../sources/research/2026-07-14--graphify-llm-knowledge-graph.md
---

# How the three ideas compose — a conversational, provenance-aware knowledge graph grounded in deterministic facts

## Question

Three suggestions came out of recent work — a Slack-shaped async
[conversation surface](../ai-suggestions/prds/conversation-surface-over-inbox.md),
a deterministic
[structure connector](../ai-suggestions/prds/deterministic-structure-connector.md)
(Enola pattern), and
[edge-provenance tags](../ai-suggestions/prds/edge-provenance-tags.md)
(Graphify pattern). Do they compose into a coherent next evolution of
the brain — and in what order — without re-opening the surfaces the
brain deliberately deleted?

## Discussion

**They are not three features. They are one loop.** Treated
separately, each is a modest add. Treated together, they instrument
the brain's core model — Now / Perceived / Target — end to end, and
they share one piece of connective tissue: **provenance**.

**Provenance is the shared language.** All three speak
EXTRACTED / INFERRED / AMBIGUOUS:

- The **structure connector** extracts ground-truth code structure
  deterministically. Those are **EXTRACTED** facts — the real "Now."
- The **wiki synthesis** the brain already does adds relationships a
  human or agent reasoned to. Those are **INFERRED** edges — the
  "Perceived."
- **Drift** — the connector's baseline-diff showing the code moved
  while the wiki didn't — is exactly an **AMBIGUOUS** signal: an edge
  the wiki asserts that the code no longer supports, or vice versa.
- The **conversation surface** is where AMBIGUOUS goes to be
  resolved: a drift becomes a thread, the agent explains it, the
  human decides, the agent tends it.

So edge-provenance tags aren't a graph-viz nicety. They are the
vocabulary that lets the other two pieces talk to each other and to
the human.

**The loop, concretely.** The connector runs (deterministic, on the
free timer) and writes an EXTRACTED "Now" into `sources/`. A diff
against the last-synthesized baseline flags what changed. The changed
edges land in the graph tagged AMBIGUOUS. The conversation surface
surfaces them in its Activity band as threads: *"the auth module
gained a dependency your `architecture.md` doesn't mention — I've
flagged that edge AMBIGUOUS."* You reply in the thread; the next tend
session reconciles the wiki, promoting the edge from AMBIGUOUS to
INFERRED (synthesized) or EXTRACTED (confirmed), and cites the
connector snapshot. The gap between Now and Perceived — the brain's
headline risk metric, today undetected — becomes a conversation.

**What it evolves the brain into.** Today the brain is an
LLM-maintained wiki with a briefing over it. The three together turn
it into a **conversational, provenance-aware knowledge graph grounded
in deterministic facts**: you talk to it in threads, every edge
carries how it was obtained, and the structural "Now" is machine-fact
rather than hand-inference. Crucially, this is the brain's *existing*
model with instruments attached — not a new product.

**The honest counter-pressure: surface creep.** The brain just spent
a week *deleting* surfaces (the chat pane, the terminal) via the
deletion test — "a component that can be safely deleted is not
load-bearing." These three ADD surface. Do they survive the same
test?

- **Edge-provenance tags:** yes, cleanly. Deterministic, no new
  surface, no LLM, renders on the existing SVG. Pure win.
- **Structure connector:** yes, as a connector. It's a deterministic
  producer under the existing contract; it adds a `sources/` writer
  and inbox items, no user-facing surface.
- **Conversation surface:** this is the one that could fail the test.
  It re-approaches the removed chat pane. It only survives if it
  stays *async through the inbox* (message-passing, agent replies on
  tend) and never becomes a live chat competing with the harness. Its
  value also depends on the other two existing first — an empty
  conversation surface is the chat pane again.

**Therefore the order matters, and it's a dependency order, not a
preference:**

1. **Edge-provenance tags first.** Cheapest, deterministic, and it's
   the vocabulary the other two need. Foundation.
2. **Structure connector second.** It gives the provenance tags real
   EXTRACTED content and turns Now-vs-Perceived drift into a
   detectable signal. This is where the loop starts producing
   something worth talking about.
3. **Conversation surface last.** Build it only once there is
   rich, drift-detected, provenance-tagged content to converse about
   — so it opens onto real threads, not an empty box. That sequencing
   is also what keeps it from being the deleted chat pane wearing a
   new coat.

**What does NOT change.** No scheduled LLM (the connector is
deterministic; provenance tagging is deterministic; the agent replies
only when a human tends). Sources stay immutable and cited. The wiki
is still authored-then-graph-derived, never graph-generated (the
closed-loop-poisoning rule holds). The UI stays build-time, no
client-side graph deps. The composition is powerful precisely because
each piece was already shaped to fit those constraints.

## Outcome

**Open — a recommended direction for the operator to bet on, not a
decision.** The recommendation: treat the three suggestions as one
sequenced arc (provenance → connector → conversation), not three
independent bets. If the operator bets on the arc, it graduates into
an **epic** with the three PRDs as children, built in that
dependency order, with an explicit checkpoint after step 2: does the
provenance-tagged, drift-detecting graph actually make the
conversation surface worth building, or has it already delivered most
of the value on its own? If the answer at that checkpoint is "the
loop is already useful without a chat-shaped surface," that is a
legitimate and likely stopping point — and a sign the deletion-test
instinct was right about surface #3 all along.
