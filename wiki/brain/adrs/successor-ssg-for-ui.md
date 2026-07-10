---
title: "Adopt Astro + Starlight + Pagefind as the successor SSG for the UI"
kind: decision
status: accepted
updated: 2026-07-10
confidence: high
sources:
  - ../../../sources/research/2026-07-10--hub-adr-verification.md
  - ../../../AGENTS.md
  - ../../../ui/astro.config.mjs
  - ../../../ui/README.md
---

Records the substrate bet behind the UI at `ui/`: Astro 5 with the
Starlight docs preset and Pagefind for lexical client-side search.

## Context

The previous UI was a vendored copy of the Quartz 4 static-site
generator. Three forces drove the replacement.

First, the mobile rule. The UI's design principles make
mobile-native rendering non-negotiable, and Quartz shipped roughly
705 KB of client JavaScript to every reader on first paint — one
combined bundle covering graph, search, popovers, and navigation.
Measured with Lighthouse's mobile preset under simulated
throttling, the home page scored 54 on performance and a
representative repo state page scored 64, with first paint above
five seconds. Astro's islands architecture ships zero client
JavaScript by default, and Starlight's stock responsive theme
clears the bar out of the box. The mobile gap closes structurally
on Astro; on Quartz it stays open absent per-component override
work.

Second, maintenance burden. A vendored generator is an open-ended
cherry-pick obligation with discarded upstream history. Moving to
pinned npm dependencies (`astro`, `@astrojs/starlight`, `pagefind`
in `ui/package.json`, nothing vendored) turns upgrades into a
one-line version bump.

Third, the substrate must not block the content-shape work that
follows (recorded in [home-content-shape.md](home-content-shape.md)).
That work needs bespoke server-rendered components that consume the
generated pages index cheaply. Astro components import build-time
data with no ceremony and hydrate only the interactivity that needs
it, so editorial surfaces stay cheap to build. Against a
Python-templated or slot-based substrate the same work would cost
several times the appetite.

Non-negotiable constraints inside the swap: no vendoring; the serve
layer stays SSG-agnostic (the static server does not change beyond
trivial configuration — the UI is local-first, and any origin
deployment is out of scope for this decision); anchor slugs stay
byte-stable across the swap via the same slugger, because downstream
consumers treat section URLs as contract; the URL shape (directory
paths, no file extensions) is preserved; the generated pages index
schema is preserved, with additions allowed and removals or renames
forbidden; and mobile Lighthouse scores must hold parity or better
against the measured baseline.

The decision carries an exit ramp with three signals: future work
demands persistent server state (evaluate Astro's SSR adapters
versus a heavier framework), the upstream stalls (no minor releases
for twelve months, or the docs preset is archived), or mobile
performance regresses below 85 for two consecutive minor releases
without a fix. Any signal re-opens the substrate decision via a new
recorded comparison, not silent drift.

## Alternatives

- **Astro + Starlight + Pagefind** *(chosen)* — mobile-native by
  construction, cheap bespoke components for future editorial work,
  npm-managed with no vendoring. Accepted costs: growing into SSR
  requires an adapter, and the opinionated theme may need minor
  overrides to match the prior reading experience.
- **Eleventy with a wiki-link plugin, Pagefind, and a bespoke
  theme** — smallest payload and best double-bracket link
  semantics, but the brain uses plain relative markdown links, so
  that headline strength is not load-bearing, and building a
  reading layout from scratch blows the small appetite. Rejected.
- **Next.js with a docs framework** — maximum flexibility for
  future server-rendered work, but the heaviest mobile bundle of
  the set, ongoing app-router churn, and no present need for server
  state. Astro reaches SSR via adapters if the need ever fires;
  buying that flexibility now is paying for unused capacity.
  Rejected.
- **MkDocs Material** — excellent mobile defaults and maintenance
  story, but Python templating is the wrong substrate for the
  bespoke component work the next pitch needs; the cost would land
  on the follow-up rather than this one. Rejected.
- **Status quo (stay on vendored Quartz)** — fails all three
  forces, and is dangerous precisely because it is workable enough
  to defer indefinitely while the costs accumulate silently.
  Rejected.

## Consequences

- *Closes:* the vendored cherry-pick obligation (upgrades become a
  dependency bump); the implicit tolerance of desktop-shrunk mobile
  rendering (parity-or-better is now a substrate constraint); the
  question of where future editorial components live (they are
  Astro components, not slots in a vendored generator).
- *Opens:* the Starlight theme and plugin ecosystem, opt-in without
  re-platforming; selective hydration, so the bundle cost of new
  interactivity scales with the interactivity rather than the page
  count; a clean SSR exit ramp via adapters; Pagefind as a
  substrate-independent search layer that would survive another
  SSG change.
- *Costs:* theme-parity work porting the prior reading experience
  (sidebar, breadcrumbs, popovers, 404 styling) — the most cuttable
  scope item; two framework dependency surfaces where there were
  none; slug-stability work if the new default slugger had
  diverged.

## Build notes

The cutover shipped as a sibling scaffold brought to parity and
then swapped in with a single cutover change; the vendored
generator and its config files were deleted in the same change, and
`tools/ui-build.sh` plus the UI README were rewritten for the new
build command. One planned constraint bent: pointing the build
output at the static server's expected folder collides with Astro's
separate static-assets folder (the two directories may not be
equal), so the default `dist` output was kept and the serve layer
changed by exactly one configuration line — the allowed
alternative. The serve layer still does not know which SSG runs
upstream of it.

Post-swap Lighthouse on the same mobile method: performance 100 on
both measured pages (from 54 and 64), accessibility 100 (from 82),
first paint 0.9 s (from 5.3 s), client JavaScript 4 KB transferred
(from 705 KB). None of the accepted costs surfaced as material: no
SSR adapter was needed, the stock theme was acceptable without
per-component overrides, and the pinned slugger was already a
transitive dependency, so anchor stability cost nothing. Hover
popovers and 404 styling were cut per the scope hammers and left to
a follow-up if reading needs raise them again.
