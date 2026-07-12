// Astro config — substrate for the brain UI.
// Pairs with ../wiki via the src/content/docs symlink.
//
// The UI is a purpose-built Astro app (no docs theme) per
// wiki/brain/adrs/human-legible-presentation-layer.md: the root is
// the briefing; wiki pages render at their existing paths with
// lifecycle-aware chrome; Pagefind indexes the build for search
// (the CLI runs post-build in package.json's build script and
// tools/ui-build.sh). Substrate history:
// wiki/brain/adrs/successor-ssg-for-ui.md.

import { defineConfig } from 'astro/config';
import remarkRewriteLinks from './remark-rewrite-links.mjs';

export default defineConfig({
  trailingSlash: 'always', // /<repo>/<page>/ — the pre-rewrite URL shape survives
  build: {
    format: 'directory',
  },
  markdown: {
    // remarkRewriteLinks rewrites cross-links at build time:
    //   - intra-wiki `[text](file.md)` → `[text](/path/)` clean URL.
    //   - out-of-wiki refs (sources/, log/, AGENTS.md, .claude/) →
    //     GitHub blob URLs that resolve to the canonical source.
    // BARE FUNCTION REGISTRATION, not tuple — Astro 5 silently drops
    // the tuple form for content-collection markdown.
    remarkPlugins: [remarkRewriteLinks],
  },
});
