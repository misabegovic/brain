---
title: "RFC pass: five personas review the three-ideas-compose topic"
kind: source
captured: 2026-07-14
participants: PM agent, Tech Lead agent, Developer agent, Viktor (operator), Sam (security) — via parallel deepdive agents
context: >
  The operator asked to run the three-ideas-compose synthesis topic
  through team personas with a 10+ minute multi-agent deepdive. Five
  personas each did a real exploration; this snapshots their verdicts.
---

# RFC pass — five-persona deepdive of three-ideas-compose (2026-07-14)

Unanimous, cross-validated verdict: the "one loop bound by
provenance" framing is an overfit narrative. The pieces are three
independent bets connected by the inbox (which already exists), not
by shared provenance vocabulary.

- **PM:** the packaging would smuggle a big, twice-killed UI surface
  in on the coattails of two cheaper ideas. Three graphs, three data
  paths; the shared vocabulary is a naming coincidence. Only the
  connector targets a real need (drift) — but it's blocked because
  the brain has no active repos to point at. Conversation surface:
  decisive no. Verdict: no on the arc; three separate calls.
- **Tech Lead:** "provenance is connective tissue" is a lexical pun.
  EXTRACTED means opposite things (Enola: AST-parsed = opposite of
  judgment; the PRD: hand-authored = most intentional). The enum
  collides with itself; drift's AMBIGUOUS lives on code→code edges
  that don't exist in the brain's graph. The real bus is the inbox.
  The loop needs mutable per-edge state the disposable-index ADR
  forbids. Fix: split the enum; express drift as its own SQL-view
  plane.
- **Developer (verified the code):** the SVG graph today holds only
  authored links (all already EXTRACTED); the INFERRED tier lives in
  a duplicate Python graph impl that never reaches the UI. AMBIGUOUS
  is a node property — smearing it onto edges is the noise the PRD
  fears; cut it. Connector substrate: small. Drift→inbox: medium and
  stateful, and connector items aren't reconciled (drift won't
  auto-clear). Conversation surface: thread-append breaks
  inbox-only-write; unread-state has no home; threading is a schema
  change.
- **Viktor (operator):** drift-to-inbox is the one I'd fight for —
  it catches rot I fear — but value and abandon-trigger are the same
  knob; three noise items a week and I stop opening the inbox.
  Conversation surface: delete without blinking. Provenance tags:
  don't care, keep anyway. Build one damped connector experiment,
  not a three-child epic.
- **Sam (security):** read as an arc these re-open the two things
  the kernel deleted (a subprocess + a conversation surface) and
  wire untrusted text from both into the one agent with wiki-write +
  sibling-read + act. Conversation surface = lethal-trifecta
  prompt-injection completion; topics/inbox aren't sources-immutable
  and topic/state.md edits aren't human-gated; attribution is
  unforgeable on the anonymous local endpoint. Connector
  re-introduces the deleted subprocess with env/secret-leak risk.
  Edge-provenance: lowest risk but the GraphML/Cypher export must
  honor serving-mode exclusion at node+edge level.
