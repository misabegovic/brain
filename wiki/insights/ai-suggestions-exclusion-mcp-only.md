---
title: "Serving-mode ai-suggestions exclusion is enforced on the MCP surface only"
kind: insight
status: superseded
superseded_by: brain/adrs/sam-uniform-loopback-host-guard.md
updated: 2026-07-12
confidence: low
affected_personas:
  - .claude/personas/users/sam-security-reviewer.md
summary: >
  Playthrough-born hypothesis: under BRAIN_SERVING=1 the ai-suggestions
  exclusion holds on the MCP server but not on the brain.py serve JSON API,
  the search CLI, or the static-UI build — three read surfaces an adopter
  would expect to behave identically. Drafts carry a visible banner and sit
  behind a proxy, so impact is bounded; awaiting a human security confirm.
sources:
  - sources/playthroughs/2026-07-12--sam-security-reviewer--serving-mode-guarantees.md
---

# Serving-mode ai-suggestions exclusion is enforced on the MCP surface only

**Playthrough-born hypothesis** — synthetic finding from the Sam
security-reviewer walk; capped at `confidence: low` until a human
security reviewer confirms or refutes it.

## Pattern

`BRAIN_SERVING=1` marks a deployment that serves people outside the
product. The governance rule is that ai-suggestion drafts (path
signal `ai-suggestions/`) are unreviewed and must not be part of the
serving corpus. That exclusion is implemented in `tools/brain-mcp.py`
(`tool_brain_search` filters results, `tool_brain_get_page` refuses
the path) and the Sam playthrough verified it holds there — a planted
draft was excluded from search and refused on read.

The same exclusion is **absent** on the other reachable read
surfaces that also react to `BRAIN_SERVING`:

- `tools/brain.py serve` honours `BRAIN_SERVING=1` for the workbench
  gate (line 1275) but its `/pages.json`, `/pages/<path>`, and
  `/views/*` handlers apply no ai-suggestions filter — a planted
  draft was returned in full (HTTP 200, canary body) on the
  serving-mode port.
- `brain.py search` (the CLI the MCP wraps) returns ai-suggestion
  pages even with `BRAIN_SERVING=1`; the MCP filters them only
  afterward, in its own wrapper.
- The static-UI build (`ui/`, a serving surface named in
  `SECURITY.md`) builds a browsable page for every wiki entry —
  `getStaticPaths` in `[...slug].astro` has no filter, and neither
  `content.config.ts` nor `serve.mjs` carries `BRAIN_SERVING`
  handling.

The exclusion is therefore surface-specific where it reads as
surface-wide.

## Evidence

- `sources/playthroughs/2026-07-12--sam-security-reviewer--serving-mode-guarantees.md`
  — §1 (serve JSON API leak of `LEAK_CANARY_9F3B`), §1b (MCP
  exclusion holds), build-time note (static-UI includes drafts).

## Affected personas

- [Sam — security reviewer](../../.claude/personas/users/sam-security-reviewer.md)

## Implications

- Suggests the ai-suggestions exclusion should live in `brain.py`
  itself (a shared serving-mode filter applied by `collect_pages_data`
  / the `/pages*` handlers / `cmd_search`), so the MCP, the JSON API,
  and the search CLI inherit it — rather than being re-implemented per
  consumer.
- Suggests the static-UI build should drop `ai-suggestions/` entries
  from `getStaticPaths` under a serving/build flag, so the named
  static-UI serving surface matches the MCP guarantee.
- Impact is bounded: ai-suggestion pages carry a visible
  "AI-suggested" banner (drafts, not secrets), the serving plane is
  meant to sit behind an identity-aware proxy, and `SECURITY.md`
  scopes the documented exclusion narrowly to the MCP. The gap is one
  of *consistency and adopter expectation*, not a write or
  authentication bypass.
- The structural guarantees `SECURITY.md` does make (workbench
  excluded in serving mode, `/api/act` never mounts in serving mode,
  no write tools, no shell/PTY listener, localhost binding, an audit
  log the client cannot disable) all held under adversarial probing.

## Status

Open — awaiting a human security reviewer to confirm whether the
serving-surface inconsistency warrants a fix (shared serving-mode
filter in `brain.py` + a build-time exclusion in `ui/`) or is
acceptable given the banner + proxy posture.
