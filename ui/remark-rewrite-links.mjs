// Remark plugin that rewrites wiki cross-links at build time.
//
// Two transforms:
//   1. Intra-wiki `.md` paths → clean `/<path>/` URLs that match
//      Astro's `trailingSlash: 'always'` + `format: 'directory'`
//      output. Without this, every `[text](file.md)` link in the
//      wiki renders as a raw `.md` href and 404s on click.
//   2. Out-of-wiki paths (sources/, log/, AGENTS.md, .claude/, etc.)
//      → GitHub blob URLs (`$BRAIN_GITHUB_BLOB/<path>`, e.g.
//      https://github.com/<owner>/<repo>/blob/main). These files exist
//      in the repo but aren't part of the rendered content collection;
//      pointing at GitHub keeps the citations clickable and lands on
//      the canonical source. When BRAIN_GITHUB_BLOB is unset the link
//      is left as-is (no remote to point at).
//
// Anchors (`#section`) are preserved across both transforms.
// Tilde-paths (`~/projects/<repo>/...`) and external URLs are left
// alone — the rendered UI can't help with those.
//
// **Path math is virtual, not filesystem-anchored.** The plugin
// detects the wiki/docs root once (by checking the two known
// shapes: dev = `<repo>/wiki/` (symlinked at `ui/src/content/docs`),
// docker = `<repo>/ui/src/content/docs/` (real copy of wiki/ from
// the Dockerfile's `COPY wiki/ ./src/content/docs/`)), then resolves
// each link's target relative to the source file's wiki-relative
// position. This decouples rewriting from where the wiki actually
// lives on disk in the build environment.
//
// Wired in `astro.config.mjs` § markdown.remarkPlugins as the
// bare function (`[remarkRewriteLinks]`), not the tuple form
// `[[remarkRewriteLinks, {}]]`. Astro 5 / Starlight 0.30 silently
// drops the tuple form for content-collection markdown — the
// module loads but the factory is never called and links render
// raw `.md`. Learned the hard way: see git history of #61–#63.

import { visit } from 'unist-util-visit';
import path from 'node:path';
import url from 'node:url';
import fs from 'node:fs';

const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const GITHUB_BLOB = process.env.BRAIN_GITHUB_BLOB || '';

function realpath(p) {
  try { return fs.realpathSync(p); } catch { return p; }
}

// Detect the wiki/docs root. Two known shapes:
//   - dev:    `<repo>/ui/remark-rewrite-links.mjs` and the docs live
//             at `<repo>/wiki/` (`ui/src/content/docs` is a symlink to it).
//   - docker: `/app/remark-rewrite-links.mjs` and the docs live at
//             `/app/src/content/docs/` (Dockerfile substitutes the symlink
//             with a real copy of `wiki/`).
function detectWikiRoot() {
  // Prefer the in-tree `src/content/docs` path. In dev it's a symlink
  // to `<repo>/wiki/`; in docker it's a real directory copied from
  // wiki/. In both cases `realpath` resolves it to the location
  // Astro will pass as `vfile.path`'s parent. Falling back to a
  // sibling `wiki/` only matters for unusual layouts where neither
  // shape is present.
  const candidates = [
    path.join(HERE, 'src', 'content', 'docs'),
    path.join(HERE, '..', 'wiki'),
  ];
  for (const c of candidates) {
    try {
      const stat = fs.statSync(c);
      if (stat.isDirectory()) return realpath(c);
    } catch { /* keep trying */ }
  }
  return null;
}
const WIKI_ROOT_ABS = detectWikiRoot();

function rewriteOne(currentFile, href) {
  if (!WIKI_ROOT_ABS) return null;

  // External URLs, mailto, anchors-only, root-absolute paths — leave alone.
  if (/^(https?:|mailto:|tel:|slack:)/i.test(href)) return null;
  if (href.startsWith('#') || href.startsWith('/')) return null;
  // Tilde paths (sibling-repo filesystem refs the UI can't render).
  if (href.startsWith('~')) return null;

  // Split anchor.
  const [pathPart, ...anchorParts] = href.split('#');
  const anchor = anchorParts.length ? '#' + anchorParts.join('#') : '';
  if (!pathPart) return null;

  // Source file's path relative to the wiki root. If it's outside
  // the wiki, give up — the plugin only knows how to rewrite for
  // pages inside the content collection.
  const sourceAbs = realpath(currentFile);
  const sourceRel = path.relative(WIKI_ROOT_ABS, sourceAbs);
  if (sourceRel.startsWith('..') || path.isAbsolute(sourceRel)) return null;

  // Compute the link's target relative to the wiki root, virtually.
  // sourceRel is e.g. "<repo>/state.md", so its dir is "<repo>".
  // pathPart is e.g. "../org/way-of-working.md".
  // path.normalize joins them correctly: "org/way-of-working.md".
  // For pathPart that escapes wiki/ (e.g. "../../AGENTS.md"), the
  // result starts with "..".
  const sourceDirRel = path.dirname(sourceRel);
  const targetWikiRel = path.normalize(path.join(sourceDirRel, pathPart));

  // Inside the wiki?
  if (!targetWikiRel.startsWith('..') && !path.isAbsolute(targetWikiRel)) {
    if (/\.mdx?$/i.test(targetWikiRel)) {
      // Markdown page → clean URL.
      let rel = targetWikiRel.replace(/\.mdx?$/i, '').replace(/(?:^|\/)index$/, '');
      return '/' + (rel ? rel + '/' : '') + anchor;
    }
    // Inside wiki/ but not markdown (e.g. wiki/_views/pages.json).
    // The SPA doesn't render it; point at GitHub at wiki/<path>.
    if (!GITHUB_BLOB) return null;
    return `${GITHUB_BLOB}/wiki/${targetWikiRel}${anchor}`;
  }

  // Escapes wiki/. Treat pathPart as repo-relative from wiki/<sourceDir>.
  // path.normalize collapses any "..": "wiki/<repo>/../../AGENTS.md" → "AGENTS.md".
  const targetRepoRel = path.normalize(
    path.join('wiki', sourceDirRel, pathPart)
  );
  // If it still escapes the repo root (e.g., absolute paths or too many ..),
  // we can't help.
  if (targetRepoRel.startsWith('..') || path.isAbsolute(targetRepoRel)) return null;
  if (!GITHUB_BLOB) return null;
  return `${GITHUB_BLOB}/${targetRepoRel}${anchor}`;
}

function stripMdInText(node) {
  // Walk the link's children manually (visit() can be tricky inside
  // a parent visit). Strip `.md` / `.mdx` from any string-valued
  // descendant — covers `text` and `inlineCode` (when authors wrote
  // `[`file.md`](file.md)` — backticks make children code, not text).
  const walk = (n) => {
    if (!n) return;
    if (typeof n.value === 'string') {
      n.value = n.value.replace(/\.mdx?\b/gi, '');
    }
    if (Array.isArray(n.children)) {
      for (const c of n.children) walk(c);
    }
  };
  if (Array.isArray(node.children)) {
    for (const c of node.children) walk(c);
  }
}

export default function remarkRewriteLinks() {
  return function transformer(tree, vfile) {
    const currentFile = vfile.history[0] || vfile.path;
    if (!currentFile) return;

    visit(tree, ['link', 'definition'], (node) => {
      if (typeof node.url !== 'string') return;
      const next = rewriteOne(currentFile, node.url);
      if (next !== null) {
        node.url = next;
      }
    });

    // Second pass: clean visible link text for any inline link whose
    // URL is now either (a) a clean wiki URL or (b) a GitHub blob URL
    // pointing back at our own repo. Authors often wrote
    // `[`some/path.md`](some/path.md)` — the URL got rewritten, but
    // the text mirror still looks like a filename.
    visit(tree, 'link', (node) => {
      if (typeof node.url !== 'string') return;
      const u = node.url;
      const ours = u.startsWith('/') || u.startsWith(GITHUB_BLOB);
      if (ours) stripMdInText(node);
    });
  };
}
