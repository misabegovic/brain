# Security

Report vulnerabilities privately to **m.isabegovic@hotmail.com** —
please do not open public issues for security reports. You should
receive a response within a few days.

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
- Connector credentials are expected to be read-only-scoped.
