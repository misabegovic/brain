---
title: "Operator direction — simplify/abstract for great UX; chat in the app instead of the embedded terminal"
captured: 2026-07-10
kind: conversation-snapshot
participants: [operator, brain-agent]
---

# Operator direction (2026-07-10, verbatim intent)

> I think we need to simplify this as much as possible and abstract
> as much as possible from the user to be able to build great UX.
> also, instead of the terminal embedded, we should probably have a
> chat in the app

Agent's read at capture: the chat IS the abstraction — the harness
already speaks the whole mechanism (skills, commands, MCP), so a
chat pane wired to a harness's print mode (subscription-based, e.g.
`claude -p --continue`) abstracts the CLI vocabulary without
reimplementing anything. Load-bearing forks for the operator:
chat-backend shape (per-harness print-mode registry vs single
harness), and the embedded terminal's fate (demote to power-user
toggle vs remove).
