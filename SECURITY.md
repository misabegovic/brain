# Security

Report vulnerabilities privately via **GitHub's private
vulnerability reporting** (Security tab → "Report a vulnerability"
on this repository) — please do not open public issues for security
reports. For anything non-sensitive, a regular GitHub issue is
fine. You should receive a response within a few days.

Scope notes for reporters:

- The serving surfaces (`BRAIN_SERVING=1`: MCP over HTTP, Datasette,
  static UI) are designed to run read-only behind an identity-aware
  proxy and carry no auth of their own — reports about missing auth
  on deliberately-proxied surfaces are working as designed, but
  bypasses of the read-only guarantees are very much in scope.
- The app page (rendered knowledge + health strip) executes no
  shell and carries no websocket; it is structurally excluded from
  serving deployments (`BRAIN_SERVING=1`). Since 0.15.0 the kernel
  ships no PTY bridge and spawns no harness subprocesses.
- Both local HTTP surfaces (`brain.py serve` and `brain-mcp.py
  --http`) apply the same loopback `Host`-header allow-list to block
  DNS-rebinding, and the MCP surface additionally checks `Origin`.
  Neither is a substitute for the identity-aware proxy a serving
  deployment puts in front.
- The `ai-suggestions/` draft shelf is excluded from every read
  surface in serving mode (`BRAIN_SERVING=1`) — the MCP tools, the
  `brain.py serve` JSON API (`/pages/`, `/pages.json`, `/views/*`),
  the `brain.py search` CLI, and a serving-mode static UI build. A
  draft leaking through any serving surface is in scope.
- Connector credentials are expected to be read-only-scoped.
