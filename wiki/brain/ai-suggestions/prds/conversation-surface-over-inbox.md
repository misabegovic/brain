---
title: "A conversation surface over the inbox — Slack-shaped channels for talking to the agent through the brain, asynchronously"
kind: initiative
status: superseded
ai_suggestion: true
superseded_by: brain/state.md
updated: 2026-07-14
team: "(inferred)"
division: "(inferred)"
repos:
  - brain
appetite: big
confidence: low
summary: >
  A threaded, async surface where you post to a channel (a topic) or
  comment on a page and the agent replies during the next tend — with
  an Activity tab for what needs you and reminders for follow-ups. Not
  live chat (that stays the harness); it's the inbox write-channel
  grown into threads, reusing topics, attention verdicts, and the
  briefing.
sources:
  - ../../../../sources/conversations/2026-07-13--slack-shaped-conversation-surface.md
  - ../../adrs/mcp-cli-surface.md
  - ../../topics/chat-surface-necessity.md
  - ../../adrs/human-legible-presentation-layer.md
---

# A conversation surface over the inbox — Slack-shaped channels for talking to the agent through the brain, asynchronously

> **Built (0.23.0, 2026-07-14) — superseded by
> [`brain/state.md`](../../state.md) § Now.** The operator directed
> this build. The RFC had marked it *no-go* on prompt-injection and
> settled-decision grounds; per the operator's direction those
> verdicts are set aside, and the RFC's craft conditions are met
> instead of vetoing: it ships **async through the inbox** (no live
> chat, inbox-only-write intact), attribution is **server-stamped**
> (unforgeable by a browser page), post text is **fenced as untrusted
> data** before reaching the tending agent, and the write endpoint is
> withheld in serving mode. The live capability is described in
> `state.md`.

## Why the agent suggests this

The operator lives in a team-chat surface — channels, threads, an
Activity tab for what needs attention, reminders — and asked whether
the brain could offer a similar way to hold an ongoing conversation
with the agent (source: the 2026-07-13 capture).

The naive answer is "add a chat pane," and it is wrong. The brain
settled *against* a first-party chat surface twice: the
[chat-surface-necessity topic](../../topics/chat-surface-necessity.md)
concluded, and the [mcp-cli-surface ADR](../../adrs/mcp-cli-surface.md)
recorded, that live conversation is the harness's job and the kernel
should not ship a worse renderer of it. No LLM runs on a schedule
(queue-and-tend). Any suggestion here has to respect both.

The observation that makes this worth exploring anyway: what the
operator is describing is not *live* chat. It is an **asynchronous,
threaded organiser** — and the brain already has every part of that
except the threaded UX. Channels are topics. The Activity tab is the
briefing's Needs-you band plus the agent's attention verdicts.
Posting and replying is the interactive channel we already built
(`/api/act` → inbox item). Reminders are snoozed inbox items
(`inbox ack` already suppresses-until). What is missing is the
surface that renders those pieces as conversations.

## Inferred objective

If the brain grew an async conversation surface over the existing
inbox and topics, the operator (and non-terminal colleagues) could
hold ongoing, threaded exchanges with the agent — post a question or
task to a channel, get a reply *in the thread* the next time a
session tends — without a live chat pane and without the agent ever
running on a schedule.

## Affected personas (agent-inferred)

- [Viktor — daily operator](../../../../.claude/personas/users/viktor-daily-operator.md)
  — lives in chat-shaped surfaces; a familiar async model lowers the
  barrier to "talk to the brain" between tend sessions. The reviewer
  should confirm real operators want conversation threads, not just
  the current briefing + comment box.
- [Priya — non-terminal PM](../../../../.claude/personas/users/priya-non-terminal-pm.md)
  — a reader who never opens a terminal; threaded channels + an
  Activity tab would let her ask and follow up without an engineer.

## Now / Perceived / Target (agent's read)

- **Now** — the human↔agent exchange is one-shot: you comment on a
  page or queue an item, the next tend session acts, and the reply
  lands as a page edit or an inbox clear. There is no thread, no
  "the agent replied to *you*," no channel to return to.
- **Perceived** — the brain records (mcp-cli-surface,
  human-legible-presentation-layer) that its surfaces are MCP + CLI +
  a read-mostly briefing with a narrow inbox write-channel; a
  conversational surface is not currently part of that picture. The
  agent cannot know whether the team wants to revise that without
  human testimony.
- **Target** *(hypothesis)* — a threaded, async surface where
  channels are topics, messages are inbox items, replies are dated
  entries the agent appends during tend, and an Activity tab shows
  unread agent replies plus needs-operator verdicts. Live chat stays
  the harness; this is message-passing through the inbox, made legible.

## Scope (suggested)

- **Channels = topics.** Render a topic as a channel: its dated
  discussion entries are the thread, newest at the bottom. Posting to
  the channel appends an operator entry *and* queues an inbox item so
  a tend session picks it up.
- **Replies land in the thread.** When a session tends a
  channel-posted item, the agent's response is appended to the topic
  as a dated entry (provenance-over-diffs — the topic kind already
  works this way) and the item clears.
- **An Activity tab.** Aggregate: unread agent replies since your
  last visit, items judged `needs-operator`, and human gates
  (pitches awaiting a bet, unconfirmed insights). This is the
  briefing's Needs-you band, re-cut as a notification feed.
- **Reminders.** A "remind me" on any item = a scheduled/snoozed
  inbox item that resurfaces on a date (extends the `inbox ack`
  suppress-until mechanism).
- **Comment-to-thread.** A page comment (existing) starts or
  continues a thread attached to that page.

## No-gos (suggested)

- **No live/synchronous chat.** The agent replies when a human
  tends, never on a timer or a socket. This is the line that keeps
  it distinct from the rejected chat pane and inside queue-and-tend.
- **No second content store.** Threads are topics; messages are
  inbox items; nothing new to persist.
- **No competing with the harness.** For real-time back-and-forth
  the operator uses their harness; this surface is for durable,
  async, attributable exchanges that belong in the brain.
- **No notifications that leave the machine** (email/push) in the
  local-first build; the Activity tab is pull, not push.

## Rabbit holes (suggested)

- **Re-opening a settled decision by accident.** If the surface
  drifts toward synchronous chat it becomes the thing that was
  removed twice. The async-through-inbox constraint must be load-
  bearing, not aspirational.
- **Reply latency as UX.** "The agent replies next time you tend"
  may feel dead to someone expecting Slack immediacy. Needs an
  honest affordance (e.g. "queued — the agent replies on the next
  tend") so the async model is legible, not broken-feeling.
- **Topic sprawl.** Channels-as-topics could multiply low-value
  threads; the groom/half-life machinery would need to cover them.
- **Attribution and audit.** Every message (human and agent) must
  carry `by:` attribution and stay in the git-audited trail, or the
  conversation becomes ungovernable.

## Appetite (estimated)

Big — on the technical-complexity dimension only. It is a new
primary UI surface plus threading semantics over topics and the
inbox, and it touches the tend loop (replies-into-threads). It would
land in slices: channel-render of a topic → post-to-channel → Activity
tab → reminders. The agent has no read on the team's capacity or
strategic weight; the human owns that.

## Suggested success metrics

- The operator starts and returns to threads instead of only glancing
  at the briefing — repeat visits to a channel over days.
- Agent replies land in-thread and are found there (not re-asked).
- The Activity tab's "needs you" precision holds (the calibration
  loop from the attention-grades work applies).
- No regression of the settled invariants: no scheduled LLM, no
  synchronous chat, read-mostly UI with the inbox as the only write.

## Suggested next step

Don't build the whole surface. Bet a *small* experiment first:
render one existing topic as a channel (thread of dated entries) with
a compose box that posts an operator entry and queues an inbox item.
If operators return to the thread and the reply-during-tend model
feels alive rather than dead, graduate this to a full initiative
through `/shape`; if not, the async-conversation direction is
answered cheaply. The load-bearing question — does this re-open the
removed chat pane — should be settled by the human before any build.

## Open questions for the human reviewer

- Does async-through-the-inbox count as genuinely distinct from the
  chat pane the brain removed, or does it re-open that decision? This
  is the load-bearing question; a bet should answer it explicitly.
- Is "the agent replies on the next tend" acceptable UX, or does the
  value depend on faster turnaround than queue-and-tend allows?
- Scope of channels: topics only, or also per-repo and 1:1 "DM with
  the agent" threads?
- Does this overlap with in-flight work the agent can't see?
- Is "big" the right appetite, or should it start as a small
  channel-render-of-a-topic experiment to test whether operators
  actually want threads?
