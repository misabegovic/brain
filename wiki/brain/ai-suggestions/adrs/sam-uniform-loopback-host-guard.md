---
title: Uniform loopback Host-header guard across both HTTP serving surfaces
kind: decision
status: suggested
ai_suggestion: true
updated: 2026-07-12
team: (inferred)
repos:
  - brain
confidence: low
summary: The two HTTP serving surfaces defend against DNS-rebinding differently — brain.py serve validates the Host header against a loopback allow-list, while brain-mcp.py --http validates only Origin (and only when present). Adopt a shared loopback Host-header check on both so the anti-rebinding guarantee is stated once and holds by construction.
sources:
  - sources/playthroughs/2026-07-12--sam-security-reviewer--agent-sweep.md
  - ~/projects/brain/tools/brain.py
  - ~/projects/brain/tools/brain-mcp.py
  - SECURITY.md
---

# Uniform loopback Host-header guard across both HTTP serving surfaces

> **AI-suggested ADR.** Does **not** reflect a human-approved
> decision and does **not** record current product state or
> upcoming product changes. This page is **agent-authored
> synthesis** of observed repo state — a *suggestion* for a human
> to review, iterate on, and either graduate (drop the
> `ai_suggestion: true` flag, change status to `accepted`, move
> the file from `wiki/brain/ai-suggestions/adrs/` to
> `wiki/brain/adrs/`) or supersede with a different framing.
>
> All "Context" / "Considered options" / "Inferred consequences"
> content below is **inference from observed state, not
> testimony from the deciders**. Treat any declarative claim
> about *why* something was decided as hypothesis, not fact.

## Context

The brain exposes two long-lived HTTP surfaces, both intended to
bind to loopback and, in serving deployments, to sit behind an
identity-aware proxy. The security posture the docs claim rests on
two things: the surfaces are read-only by construction, and they
resist the browser-based DNS-rebinding class of attack that lets a
malicious web page reach a service bound to the victim's own
loopback interface.

The Sam security-reviewer playthrough on 2026-07-12 (cited above)
probed both surfaces against a running 0.19.3 instance and found
every documented guarantee holding: the interactive `/api/act`
channel refuses a request that lacks the custom `X-Brain-Act`
header (the header forces a CORS preflight the server never
grants, so a cross-origin page cannot fire it), refuses a forged
non-loopback `Host` header, and is structurally absent in serving
mode (a write attempt returns a read-only refusal because the
write branch is never mounted, not merely flag-gated). The MCP
HTTP transport rejects a cross-origin `Origin` and refuses
non-POST methods, and serving mode excludes ai-suggestions from
both search results and page reads at the path level, with a
path-traversal guard rejecting attempts to escape the wiki root.

The observation that motivates this suggestion is not a broken
guarantee but an *asymmetry between the two surfaces in how the
anti-rebinding defense is implemented*. The reviewer observed
that the app/JSON surface validates the incoming `Host` header
against a loopback allow-list before serving its interactive
routes, whereas the MCP HTTP transport validates the request
`Origin` — and only when an `Origin` header is present — with no
corresponding `Host` check. Each surface therefore relies on a
different single mechanism drawn from the standard toolbox for
loopback-bound services (Host allow-list, Origin validation,
custom-header CSRF). The two mechanisms are individually
reasonable, but because they differ, the anti-rebinding property
cannot be stated once for "the brain's serving plane" — it must be
argued surface by surface, and a future change to one surface
cannot be pattern-matched against the other.

The reviewer's specific concern is that `Origin`-only validation
treats a missing `Origin` as allowed. That is correct for the
common non-browser client, but it means the MCP transport's
rebinding defense leans entirely on browsers reliably attaching an
`Origin` to the cross-origin request, whereas the app surface's
`Host` allow-list does not depend on client-attached provenance at
all. Prevailing guidance for locally-bound developer services
(the reviewer cites the general OWASP position on DNS-rebinding)
treats a `Host`-header allow-list as the belt-and-suspenders
baseline precisely because it does not depend on the client
volunteering an `Origin`.

## Inferred decision

The repo state is consistent with each surface having grown its
own defense independently as it was written, rather than a single
shared helper being applied to both. The suggested decision is to
converge them: adopt one loopback `Host`-header allow-list check,
applied uniformly to both HTTP serving surfaces, so the
anti-rebinding guarantee holds by construction on every route and
can be described in `SECURITY.md` as a single property rather than
two per-surface arguments. Origin validation and the custom-header
CSRF requirement stay where they are as additional layers; the
`Host` allow-list becomes the common floor.

## Considered options (agent surfacing)

- **Option A — shared loopback Host-header check on both surfaces**
  *(the suggestion)*. Factor the loopback allow-list decision the
  app surface already performs into a shared predicate and apply
  it as the first check on the MCP HTTP transport as well. The
  anti-rebinding guarantee becomes uniform and testable once. The
  cost is a small amount of shared plumbing and a decision about
  where a check common to two entry points should live.

- **Option B — leave each surface with its own single mechanism**.
  The status quo. Defensible because both surfaces bind to
  loopback and a serving deployment fronts them with a proxy, so
  neither is directly exposed. The reviewer's honest position is
  that nothing is broken today; the argument for acting is
  future-proofing and legibility, not an open hole.

- **Option C — add Origin validation to the app surface instead**,
  converging on `Origin`-only for both. Rejected in the reviewer's
  framing because it inherits the "missing Origin is allowed"
  property on both surfaces and discards the app surface's
  provenance-independent `Host` check, which is the stronger of
  the two baselines.

- **Do nothing** — the implicit baseline; identical to Option B.

## Inferred consequences

- **Closes** the gap where the two surfaces must be reasoned about
  separately, and removes the MCP transport's dependence on the
  client volunteering an `Origin` for its rebinding defense.
- **Opens** the ability to state one anti-rebinding guarantee for
  the whole serving plane in `SECURITY.md`, and to test it with a
  single shared assertion.
- **Costs** a small refactor touching two restricted-path files
  under `tools/`, plus the ongoing discipline of routing any new
  HTTP entry point through the shared check. There is a risk of
  over-tightening if a legitimate non-loopback deployment topology
  exists that the reviewer did not observe; the allow-list must
  keep the empty-Host and proxy cases working exactly as the app
  surface already does.

## Open questions for the human reviewer

- Is there a supported deployment where either surface is meant to
  answer on a non-loopback `Host` value directly (not via a
  proxy that rewrites `Host`), which a strict allow-list would
  break?
- Should the shared check live beside the two serve entry points
  in `tools/`, or is there a preferred home for cross-surface
  security plumbing?
- Is the MCP transport's "missing Origin is allowed" behaviour a
  deliberate accommodation for a specific non-browser client, and
  if so does adding a `Host` allow-list leave that client working?
- Does `SECURITY.md`'s current wording already intend to promise a
  uniform anti-rebinding property, making this a documentation-vs-code
  alignment fix rather than a new guarantee?

## Suggested next step

- **Iterate** on the framing if the human reader agrees the
  asymmetry is worth closing but wants the mechanism scoped
  differently. Edit in place; the file stays under
  `ai-suggestions/` until graduated.
- **Graduate** if the convergence is accepted as the intended
  posture. Drop the `ai_suggestion: true` flag, set status to
  `accepted`, move to `wiki/brain/adrs/`.
- **Reject** if the loopback-bound-behind-a-proxy deployment model
  makes the per-surface status quo sufficient and the uniformity
  gain does not justify touching restricted paths.

## Sources

- The Sam security-reviewer playthrough transcript at
  `sources/playthroughs/2026-07-12--sam-security-reviewer--agent-sweep.md`
  — the real command output the inferences above rest on.
- The two serving surfaces in `tools/brain.py` (the app/JSON
  server) and `tools/brain-mcp.py` (the MCP HTTP transport).
- `SECURITY.md` — the claimed serving-surface posture.
