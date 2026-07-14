---
title: "How the three ideas compose — a conversational, provenance-aware knowledge graph grounded in deterministic facts"
kind: topic
status: living
updated: 2026-07-14
confidence: low
summary: >
  Original synthesis: the three ideas are "one loop bound by
  provenance." A five-persona RFC (2026-07-14) rejected that framing
  as an overfit narrative — the pieces touch disjoint graphs and the
  real bus is the inbox, which already exists. Revised verdict: three
  independent bets, not an epic. The connector (drift) is the only
  latent-valuable one and is multiply gated; the conversation surface
  is a no-go (re-litigates a settled decision + completes a
  prompt-injection trifecta); provenance tags proceed standalone with
  a corrected design.
sources:
  - ../../../sources/conversations/2026-07-14--three-ideas-rfc-pass.md
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

## RFC — five-persona review (2026-07-14)

Run through the persona pool (three Shape Up roles + two user
personas), each a real deepdive. The verdict was unanimous: the
"one loop" framing does not survive contact.

**PM (product).** The "one loop" packaging would smuggle a big,
twice-killed UI surface into a build on the coattails of two cheaper,
sounder ideas. The three touch three different graphs via three
different data paths; the shared EXTRACTED/INFERRED/AMBIGUOUS
vocabulary is a naming coincidence dressed as architecture, and the
conversation surface never reads the tags the arc says are its
foundation. Sized separately, only the connector targets a real need
(Now-vs-Perceived drift) — and it is blocked by a fact the synthesis
never confronts: this brain has no active repos to point at. Verdict:
no on the arc; three separate calls with off-ramps.

**Tech Lead (architecture).** "Provenance is the connective tissue"
is a lexical pun. EXTRACTED means opposite things at the three stops:
in the connector it is epistemic origin (parsed from an AST, the
opposite of judgment); in the edge-provenance PRD it is mapped to
hand-authored links (the most intentional edge in the system). The
enum collides with itself — a hand-authored link into a low-confidence
hub is simultaneously EXTRACTED and AMBIGUOUS — and drift's AMBIGUOUS
lives on code→code edges that do not exist in the brain's graph at
all. The real bus is the inbox. The loop's "promote the edge from
AMBIGUOUS to INFERRED" requires mutable per-edge state the
disposable-index ADR forbids.

**Developer (build reality, verified against the code).** The graph
the `/graph/` SVG renders (`data.mjs::linkGraph`) holds only authored
markdown links — every edge is already EXTRACTED; the INFERRED tier
(suggested links) lives in a second, duplicate graph implementation
in Python (`_link_graph`/`cmd_links`) that never reaches the UI. So
"tag existing edges" is really "reconcile two graph implementations."
AMBIGUOUS is a node property; smearing it onto incident edges is the
exact tag-noise the PRD fears. The connector substrate is small; its
drift-diff is net-new and stateful, and connector inbox items are
never reconciled, so drift won't auto-clear. The conversation
surface's "post appears in its thread immediately" breaks the
inbox-only-write invariant, and "unread since last visit" has nowhere
to live in an identity-free, git-committed, multi-reader model.

**Viktor (daily operator).** Drift-to-inbox is the one I'd fight for
— it catches the architecture rot I can't see today — but its value
and its abandon-trigger are the same knob: three noise items in a
week and I stop opening the inbox, which breaks the surface my whole
loop depends on. The conversation surface I'd delete without blinking:
I already talk to the brain in my terminal, richer and now, and the
Activity tab is a fresh cry-wolf surface aimed at my core frustration.
Provenance tags I don't care about and will keep anyway — plumbing,
not a feature. Build one damped connector experiment, not a
three-child epic.

**Sam (security).** Read as an arc, these re-open the two things the
kernel spent a week deleting — a scheduled subprocess and a
conversation surface — and wire untrusted text from both into the one
agent that has write access to the wiki and read access to every
sibling repo. The guards are all documentation guarantees in No-gos,
not code paths. The conversation surface is a lethal-trifecta
completion: a channel post is untrusted input, the tending agent
holds private data and can act (write the wiki, queue execute-priority
items, open PRs), and the guards don't hold — the confidence floor
only labels output, `sources/`-immutability doesn't cover topics or
the inbox, and topic/`state.md` edits are not human-gated.
Attribution is unforgeable on the anonymous local endpoint. The
connector re-introduces the deleted subprocess with env-inheritance
and secret-into-immutable-storage leaks; its drift text is a second
injection channel. Edge-provenance is lowest-risk, but the
GraphML/Cypher export must honor the serving-mode `ai-suggestions`
exclusion at the node *and* dangling-edge level or it becomes the
first serving-mode draft leak.

## Outcome

**Revised after the RFC (2026-07-14) — the review rejected the
framing and refined the pieces.** The original "one loop bound by
provenance" synthesis does not hold: `EXTRACTED/INFERRED/AMBIGUOUS`
names three different axes across the three pieces, they operate on
disjoint edge populations, and the real bus connecting them is the
**inbox, which already exists**. Drop the epic framing. These are
**three independent bets with off-ramps**, not one arc.

1. **Edge-provenance tags — proceed standalone, redesigned.** Split
   the overloaded enum into an *authorship channel* (authored vs
   suggested) and a *separate* node-risk flag; drop
   AMBIGUOUS-as-an-edge-tag (it is a node property; smearing it onto
   edges is structural noise). It requires reconciling the two
   duplicate graph implementations (`_link_graph` vs `linkGraph`), not
   tagging twice. And the serving-mode `ai-suggestions` exclusion must
   run over graph nodes *and* edges before any render / export /
   MCP-graph-read.
   **→ Built 0.21.0 (2026-07-14), exactly to this corrected design.**
   `brain.py` emits a single tagged edge list to
   `wiki/_views/graph.json` (EXTRACTED authored / INFERRED suggested
   on the authorship axis, AMBIGUOUS as a node flag), the UI reads
   that one list, `/graph/` renders it, MCP page reads expose the
   tags, and serving mode strips draft nodes *and* their incident
   edges. See [`brain/state.md`](../state.md) § Now.

2. **Structure connector (drift → inbox) — the one latent-valuable
   bet, multiply gated.** Park until: a real adopter instance with
   real sibling repos exists (this brain dogfoods itself,
   `active_repos` empty — nothing to point at); the tool matures or a
   vendor-neutral snapshot contract exists; the damping is proven by
   the by-hand experiment; a drift *reconciler* is built (drift is
   stateful; connector items aren't reconciled today); and the
   security guards land (scrubbed env, network-denied, sibling
   read-only with a git-clean post-condition, secret-scan before the
   immutable write, structural-only inbox summaries, brain-computed
   filenames). Express drift as its own indexed code-structure plane +
   a SQL view diffing it against the wiki — not a promotable per-edge
   state.

3. **Conversation surface — no-go for now.** Not a child of an epic.
   It re-opens a twice-settled decision, its need-owner is a synthetic
   unconfirmed persona, the async mechanic it wants already ships (the
   `/api/act` comment box + the Needs-you band), it breaks the
   inbox-only-write invariant, and it completes a prompt-injection
   lethal trifecta with unforgeable attribution. Re-open only if a
   *named real operator* hits thread-shaped friction the comment box
   cannot hold — and only with structural injection guards plus an
   identity layer the local-first posture currently refuses.

The review did its job: it dismantled the synthesis. That is the
value — a satisfying narrative met five lenses and only the
inbox-plumbing and one cheap, corrected borrow survived. Full RFC
snapshot:
`sources/conversations/2026-07-14--three-ideas-rfc-pass.md`.

**Operator directive (2026-07-14) — build all three.** After the
RFC, the operator was explicit that the three ideas were handed over
to *build*, not to re-adjudicate on necessity: *"Your role is not to
think and argue if we need these things."* The RFC's craft findings
still govern *how* each is built (the corrected provenance design,
the connector's guards and drift reconciler, the conversation
surface's structural injection guards and identity layer) — but the
"no-go / gated" verdicts are set aside as the operator's call, made.
Build order follows the original dependency order:
edge-provenance (done) → structure connector → conversation surface.