---
title: "Research — Datasette as a read-only serving surface"
captured: 2026-07-10
kind: research-note
method: web research (agent)
---

# Datasette over the derived index

**State.** Stable 0.65.2 (2025-11); 1.0 alphas active (1.0a35,
2026-06) with a rewritten permissions system landed — deploy 0.65.x
today, defer alphas. Pure-Python ASGI, single process, light.
<https://docs.datasette.io/en/stable/>

**Fit.** Derived read-only SQLite is Datasette's exact design
center. Immutable mode (`-i`) disables mutation at the SQLite level
and unlocks aggressive HTTP caching. Canned queries in metadata.yaml
(`:named` params → auto forms + JSON APIs) are literally
"SQL-in-YAML view specs served". Facets, FTS5 auto-detection
(`?_search=`), CSV export, `.json` everywhere with `_shape` params.

**Write guarantees.** Three independent layers: 0.x core has no
write paths (except canned queries explicitly marked write, which
fail on immutable dbs); write plugins are opt-in installs; `-i` is
the hard backstop.

**Auth.** Deploy behind an identity-aware proxy (Cloudflare Access /
Tailscale / oauth2-proxy) — the canonical pattern;
datasette-auth-existing-cookies maps proxy identity to actors.
`allow` blocks per instance/db/table/query; `allow_sql` gates
arbitrary SQL. No built-in rate limiting — do it at the proxy.

**Operational notes.** Immutable mode caches counts at startup —
index refresh = write-new-file + atomic rename + ~1 s process
restart (or blue/green behind the proxy). Plugins of interest:
datasette-render-markdown, datasette-search-all, datasette-graphql,
datasette-dashboards (third-party, active). Caveat: one-maintainer
core; many plugins single-maintainer.

**Downsides.** Outgrown when you need writes, per-row authz, >10M
rows, or a branded product UI — it always looks like a data tool.

**Recommendation.** Pilot on 0.65.2 behind the IAP as the
power-user/API tier of the serving slice; not the polished
end-user chat surface.
