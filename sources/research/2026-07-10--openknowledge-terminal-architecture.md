---
title: "Research — open-knowledge's embedded-terminal + harness architecture"
captured: 2026-07-10
kind: research-note
method: local repo study (agent) of ~/projects/open-knowledge
---

# How open-knowledge embeds a terminal and integrates harnesses

**Terminal.** Desktop-only (Electron): node-pty in a per-window
utility process, bytes bridged over Electron IPC (no websocket);
xterm.js v6 + fit/webgl addons in the renderer
(packages/app/src/components/TerminalPanel.tsx,
packages/desktop/src/utility/pty-host.ts). Spawns the **user's own
login shell** (`$SHELL -l -i`), never an agent binary directly.
Message shape keyed by session id: create/input/resize/kill/data/
exit — a clean copy target for a Python PTY↔websocket bridge.

**Harness launches.** A data registry TERMINAL_CLIS
(packages/core/src/handoff/terminal-launch.ts): claude, codex,
cursor (cursor-agent), opencode, pi, antigravity — each row = bin +
fixed args + prompt-flag-vs-positional. "Open in <agent>" bakes the
command as `$SHELL -l -i -c '<cmd>; exec $SHELL -l -i'` so the
launch line never lands in shell history and the tab returns to a
normal shell after the agent exits. Prompts are POSIX
single-quoted against injection.

**Per-harness config generation.** EDITOR_TARGETS
(packages/cli/src/commands/editors.ts): one row per harness mapping
config path + nesting key + skill dir — writes .mcp.json (Claude),
.cursor/mcp.json, .codex/config.toml, OpenCode/OpenClaw JSON, plus
per-editor skill projections.

**Layout.** react-resizable-panels: editor above, collapsible
terminal dock below (or right dock); live PTY sessions are
*portaled* between containers so re-docking never respawns; ⌘J
toggles; multi-tab strip.

**Security.** The human terminal is a full unsandboxed user shell
(local desktop posture). The agent-facing exec is a *separate*
allowlisted read-only sandbox (just-bash: cat/ls/grep/find/…,
fs rooted at cwd, 16 MB cap). Their loopback websocket (the
collab editor) uses a Host-header DNS-rebinding check + JSON token.

**Edit → UI sync.** @parcel/watcher/chokidar detects external .md
writes → applies into the live doc with origin/hash guards against
write-back loops.

**Transferable:** xterm.js + a tiny Python PTY-websocket bridge
(loopback + token + Host check); the launch-registry-as-data
pattern; the config fan-out table; watchfiles → SSE reload for the
rendered side; keep human terminal and agent exec surfaces
distinct.
