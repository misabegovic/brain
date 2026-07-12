---
title: "The workbench is a loopback browser page over a stdlib PTY bridge; harness launches and config adapters are data tables; it never ships in serving mode"
kind: decision
status: superseded
superseded_by: brain/adrs/mcp-cli-surface.md
updated: 2026-07-12
confidence: medium
summary: >
  Superseded: the embedded terminal ran the operator's shell over a stdlib PTY-websocket bridge, loopback-only with token and Host checks. Removed 0.15.0 — layout was load-bearing, the component was not.
sources:
  - ../prds/harness-workbench.md
  - ../../../sources/research/2026-07-10--openknowledge-terminal-architecture.md
---

# The workbench is a loopback browser page over a stdlib PTY bridge; harness launches and config adapters are data tables; it never ships in serving mode

**Decision.** The workbench lands as a page on the brain's existing local
server, not a desktop application. A minimal PTY bridge in the kernel —
standard library only — owns terminal sessions keyed by id with a small
message vocabulary (create, input, resize, kill, data, exit), spawns the
operator's own login shell, and speaks to the browser over a
loopback-bound websocket carrying a per-process session token, with the
host header checked against rebinding. The browser side renders with the
established terminal component from the UI package's dependency tree, in
a resizable split beside the rendered brain. Harness launches are **rows
in a data registry** (binary, fixed arguments, prompt-flag shape): the
launch command is baked into the shell invocation so it never enters
shell history, the one user-influenced token is quoted, and the tab
drops back to a plain shell when the harness exits. Per-harness
configuration is a second data table — one row per harness naming its
config file and nesting key — applied idempotently with the same
sentinel-fence discipline the sibling installer established. The
rendered side refreshes off a cheap server-side change signal driven by
file-modification polling; git remains the only synchronisation layer.
The workbench is **structurally absent from serving deployments**: the
serving mode never mounts the bridge, and the bridge itself refuses
non-loopback binds.

## Context

The pitch's deepdive studied open-knowledge's shipped implementation
rather than guessing. Their terminal is Electron-only — a per-window
utility process owning the PTYs, bytes over process IPC, no websocket —
which is exactly the part that does not transfer to a browser-served
brain; everything around it does. Their message vocabulary and
session-per-id shape is clean and battle-tested; their launch registry
covers the same harnesses this brain targets and encodes two lessons
worth keeping verbatim — keep launch lines out of shell history, and
quote the prompt; their config generation is a fan-out table per
harness; and their security posture separates the human's full shell
from the agent-facing sandboxed surface entirely. Their loopback
websocket (used for the collaboration layer this brain doesn't need)
demonstrates the token-plus-host-check pattern this decision adopts for
the PTY bridge.

Two local constraints shaped the rest. The brain's server is standard
library Python by design (no framework, no dependency for the kernel),
so the bridge implements the small slice of the websocket protocol it
needs rather than importing one; the terminal client is the only new
UI-package dependency. And the agent-independence principle demands the
harness integrations be data, not code paths — a new harness should
cost one row in two tables.

## Alternatives

- **Browser page + stdlib PTY bridge on the local server** *(chosen)* —
  no new runtime, no packaging, works over the server that already
  exists; the studied message shape ports directly.
- **An Electron/desktop app** (open-knowledge's actual shape) —
  rejected: a packaged desktop product is a different maintenance
  category (updaters, signing, per-OS builds) for zero gain over a
  local page, and it contradicts the shell's zero-install posture.
- **A terminal multiplexer integration instead** (tmux/screen panes
  launched by a CLI verb) — cheapest possible build and screen-native,
  but it cannot put the *rendered* brain beside the terminal, which is
  the actual ask; kept as the everything-fancier escape hatch the pitch
  named.
- **Reuse the Astro UI as the host** (embed the terminal in the
  Starlight site) — rejected: the UI is a static build, the bridge is a
  live process; coupling them re-opens the substrate decision for no
  reason when the live server already serves the dashboard.
- **A third-party Python websocket/PTY dependency** — rejected for the
  kernel: the protocol slice needed is small, and the kernel's
  zero-dependency property is load-bearing for the shell's portability.
- **Do nothing** — the two-window loop persists; harness wiring stays
  manual. Rejected by the bet.

## Consequences

- **Closes** the desktop-app question (explicitly unasked going
  forward), the transport question (websocket at loopback with token +
  host check), and the security boundary: the human terminal is a full
  shell on the operator's machine only; agents keep reaching the brain
  through MCP and files; serving deployments structurally cannot mount
  the terminal.
- **Opens** one-command harness onboarding (`install-agent`) and
  one-click harness sessions from the workbench; a new harness is one
  registry row plus one adapter row.
- **Opens** the workbench as the shell's demonstration surface — the
  first-session experience becomes "open the workbench, click your
  harness".
- **Costs** a hand-rolled websocket slice to maintain (bounded: text
  frames, masking, ping/pong) and one new UI dependency; both are
  contained in the bridge and the page.
- **Costs** browser-terminal ergonomics versus a native terminal
  (copy/paste, scrollback); accepted — the native terminal remains fully
  supported, the workbench is additive.

## Build notes

Shipped 2026-07-10. The bridge landed inside the existing serve command
as an opt-in flag rather than a separate daemon, keeping one local
server; the change signal landed as a lightweight endpoint the page
polls (modification-time scan), deferring push signalling until polling
proves insufficient. The launch registry shipped with four rows
(claude, codex, cursor-agent, opencode); the adapter table with the
matching four, writing MCP registration per harness config shape.
