// Astro config — substrate for the brain UI.
// Pairs with ../wiki via the src/content/docs symlink. See
// wiki/brain/adrs/successor-ssg-for-ui.md for the substrate decision
// and wiki/brain/adrs/home-content-shape.md for the home page that
// renders at `/`.

import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import remarkRewriteLinks from './remark-rewrite-links.mjs';

export default defineConfig({
  // Astro defaults: outDir './dist', publicDir './public'. We use the
  // defaults — collision-free, idiomatic — and ui/serve.mjs's one
  // string ("public" → "dist") is the substrate ADR's allowed
  // "alias it (one-line config)" tweak.
  trailingSlash: 'always', // matches Quartz's /<repo>/<page>/ shape
  build: {
    format: 'directory', // /<repo>/<page>/ rather than .html
  },
  markdown: {
    // remarkRewriteLinks rewrites cross-links at build time:
    //   - intra-wiki `[text](file.md)` → `[text](/path/)` clean URL.
    //   - out-of-wiki refs (sources/, log/, AGENTS.md, .claude/) →
    //     GitHub blob URLs that resolve to the canonical source.
    // See ui/remark-rewrite-links.mjs for the precise rules.
    //
    // BARE FUNCTION REGISTRATION, not tuple. Astro 5 / Starlight
    // 0.30 silently drops the tuple form (`[[plugin, {}]]`) for
    // content-collection markdown — the module loads but the
    // factory never runs. Bare form (`[plugin]`) does run.
    remarkPlugins: [remarkRewriteLinks],
  },
  integrations: [
    starlight({
      title: 'Brain',
      description: 'A Karpathy-pattern LLM-maintained markdown wiki. The home page is an agent-maintained dashboard; everything else is per-repo or per-org pages.',
      logo: undefined,
      sidebar: [
        // Sidebar starts minimal — the wayfinding lives on wiki/index.md
        // § Where to find things, not duplicated here. Future iterations
        // can grow this if the dashboard's wayfinding section proves
        // insufficient on mobile.
        { label: 'Home', link: '/' },
        {
          label: 'Onboarding',
          link: '/onboarding/',
          badge: { text: 'start here', variant: 'tip' },
        },
        {
          label: 'Views',
          autogenerate: { directory: '_views/custom' },
        },
        {
          label: 'Brain — self-tracking',
          collapsed: true,
          items: [
            { label: 'State', link: '/brain/state/' },
            { label: 'Roadmap', link: '/brain/roadmap/' },
            { label: 'Decisions (ADRs)',
              autogenerate: { directory: 'brain/adrs' } },
            { label: 'Initiatives (PRDs)',
              autogenerate: { directory: 'brain/prds' } },
            { label: 'Pitches',
              autogenerate: { directory: 'brain/pitches' } },
          ],
        },
        {
          label: 'Org',
          collapsed: true,
          autogenerate: { directory: 'org' },
        },
        {
          label: 'AI suggestions (drafts for review)',
          link: '/_views/ai-suggestions/',
          badge: { text: 'review', variant: 'caution' },
        },
        // Active repos: add one entry per repo declared in
        // brain.config.yml as its wiki/<repo>/ shelf lands, e.g.
        // { label: 'app', link: '/app/' }.
        {
          label: 'Active repos',
          items: [],
        },
      ],
      // Starlight bundles Pagefind end-to-end: builds the index after
      // `astro build` AND surfaces the search UI in the header. We
      // previously disabled this (pagefind: false) and ran pagefind
      // ourselves post-build — that left us with an index but no UI,
      // i.e. no search bar at all. Letting Starlight handle the full
      // loop is the simpler path and the substrate ADR's
      // "Pagefind as substrate-independent search layer" still holds
      // (Pagefind is the underlying tool either way).
      pagefind: true,
      components: {
        // Customisations land here later (404, breadcrumbs, popovers)
        // when scope-hammer #2 (theme parity) gets touched.
      },
    }),
  ],
});
