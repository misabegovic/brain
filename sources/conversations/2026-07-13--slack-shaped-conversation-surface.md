---
title: "Conversation capture: a Slack-shaped conversation surface in the brain UI"
kind: source
captured: 2026-07-13
participants: operator, claude (fable 5)
context: >
  The operator, looking at a team chat app on mobile (channels,
  threads, an Activity/notifications tab, reminders), asked whether
  the brain UI should offer a similar way to hold an extended
  conversation with the agent through the brain, and requested an
  AI-suggestion.
---

# Conversation capture — Slack-shaped conversation surface (2026-07-13)

**Operator intent:** a team-chat app organises work as channels and
threads, with an Activity tab surfacing what needs attention and
reminders for follow-ups. The operator wants to explore a similar
surface in the brain UI — somewhere to hold an extended, ongoing
conversation with the agent, not just a one-shot comment.

**Agent framing (recorded for the suggestion):** the brain settled
*against* a first-party synchronous chat pane twice
(chat-surface-necessity topic → mcp-cli-surface ADR): live chat is
the harness's job, and no LLM runs on a schedule. So the honest
shape is not live chat. It is an *asynchronous, threaded surface
over the existing inbox*: the operator posts to a channel (a topic)
or comments on a page, it becomes an inbox item, and the agent
replies into the thread during the next tend session. Channels map
to topics, the Activity tab maps to the briefing's Needs-you band
plus attention verdicts, and reminders map to snoozed inbox items.
This reuses the human↔agent seam the architecture already blessed
rather than reintroducing the rejected chat pane.
