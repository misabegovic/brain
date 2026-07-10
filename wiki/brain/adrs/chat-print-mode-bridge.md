---
title: "The chat is a per-harness print-mode bridge: conversation as the interface, terminal demoted to a toggle, bare `brain` opens the app"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
sources:
  - ../prds/chat-first-app.md
  - ../adrs/workbench-pty-bridge.md
---

# The chat is a per-harness print-mode bridge: conversation as the interface, terminal demoted to a toggle, bare `brain` opens the app

**Decision.** The app's primary interaction is a chat pane whose backend
is a **print-mode registry**: one data row per harness naming its
non-interactive text-in/text-out invocation and its session-continuation
form, spawned per message in the repo on the operator's existing
subscription — no API-key billing path enters the kernel, and a chat
message is interactive use in exactly the cost sense a terminal keystroke
is. The chat endpoint lives beside the PTY route under the same
per-process token, host check, and structural exclusion from serving
deployments. The embedded terminal is **demoted, not removed**: the PTY
bridge stays shipped and reachable behind an advanced toggle, amending
the workbench decision's layout claim while preserving its transport,
security posture, and launch registry unchanged. The **surface
collapses**: bare `brain` opens the app; the dashboard's glanceable
content becomes an ambient attention strip in the app; documentation
leads with the conversation. The CLI surface is not reduced — it is
re-labelled as the power layer the chat drives on the user's behalf.

## Context

The operator's direction was simplification by abstraction, with a chat
replacing the terminal as the face. The load-bearing insight: the
harness already speaks the entire mechanism — skills, commands, MCP,
governance — so the conversation is the abstraction layer for free;
teaching the app any mechanism vocabulary would be reimplementation.
The constraint field was already fixed by prior decisions: no scheduled
model runs and no API billing (queue-and-tend), harness integrations as
data tables (workbench bridge), serving deployments never carry
operator surfaces. Print modes thread all three: modern harness CLIs
expose non-interactive invocations that bill to the same subscription
as interactive use and honour the repo's project configuration, so the
chat inherits permissions and skills without any new governance
surface. The operator picked the registry over a single-harness wire,
the toggle over removal, and the full collapse over a partial sweep.

## Alternatives

- **Print-mode registry** *(chosen)* — agent-independent by data row;
  a harness without a print mode simply has no chat row (it keeps a
  terminal launch row); never scrape a TUI.
- **Single-harness wire first** — faster, but plants harness coupling
  in the app's core exactly where the independence principle says data
  must live; rejected by the operator.
- **Parse the PTY stream into bubbles** — reuses the existing bridge
  but means scraping an interactive TUI, brittle against every harness
  redraw; rejected as the pitch's named rabbit hole.
- **An SDK/API chat of our own** — best streaming UX, but introduces
  API billing and a model dependency into a kernel whose cost and
  independence constraints both forbid it; rejected.
- **Remove the terminal outright** — simplest surface, but deletes a
  shipped, tested escape hatch hours after its decision for zero
  carrying cost; rejected by the operator for the toggle.

## Consequences

- **Closes** the interface question: conversation first, ambient
  status, knowledge beside it; the mechanism's vocabulary becomes a
  power-user concern.
- **Closes** the cost boundary again: subscription print modes only;
  the kernel still has no API-key path.
- **Opens** streaming (print modes offer streaming output formats),
  transcript capture into sources, and chat-led onboarding as named
  follow-ups.
- **Costs** blocking latency per message in v1 (an agent turn can run
  minutes; the UI shows progress and the terminal toggle remains for
  impatient power use), and permission friction — print-mode sessions
  inherit project permissions, so deep write actions may route users
  to the terminal until permission rows are tuned.
- **Amends** the workbench decision's layout (chat primary, terminal
  toggled) while leaving its transport, token/host gating, launch
  registry, and serving exclusion untouched.

## Build notes

Shipped 2026-07-10 — see the roadmap's 0.12 entry for the shapes:
CHAT_CLIS rows for the four harnesses (claude, codex, cursor,
opencode), a blocking chat endpoint with per-session continuation
tracking, the attention strip fed by the doctor and inbox sources,
bare `brain` opening the app, README restructured to lead with the
conversation.
