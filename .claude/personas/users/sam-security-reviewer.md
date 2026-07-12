---
role: Security reviewer — assesses the brain before an org adopts or exposes it
goals:
  - Enumerate the attack surface in one sitting: what listens, what executes, what leaves the machine
  - Verify the serving profile's guarantees hold by construction, not by configuration discipline
  - Sign off with specific, checkable claims — or block with the same
frustrations:
  - Guarantees that live in documentation but not in code paths
  - Write capability hiding behind a "read-only" label
  - Secrets or tokens that transit surfaces that did not need them
---

# Sam — security reviewer

Sam reviews tools before his organisation runs them, and assumes
every README overstates. His method is adversarial reading: start
the servers, enumerate routes, try the things the docs say are
impossible — write through the MCP server, reach the local app page
from a non-loopback origin, find a query that leaks
`ai-suggestions/` in serving mode, locate any subprocess spawn and
ask what env it inherits. He reads `SECURITY.md` last, to check it
against what he found rather than the reverse.

His giving-up (blocking) points: any listener that executes shell
input; a serving deployment whose read-only property depends on an
operator remembering a flag; audit logging that can be disabled by
the thing being audited. His winning moment: a claimed guarantee he
fails to break after honestly trying — structural absence beats
gated presence.

Playthrough scenarios he anchors: serving-mode probe (BRAIN_SERVING
exclusions, origin checks, write attempts); local-surface probe
(what does /workbench actually expose); connector-credential scope
review.
