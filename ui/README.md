# ui — Astro + Starlight over brain/wiki

The production UI layer for the brain. Lives inside the brain repo
at `ui/`, sibling to `wiki/`, `tools/`, `sources/`, and `log/`.

Astro 5 + Starlight 0.30 + Pagefind, all npm-installed (no
vendoring). Renders `wiki/` directly via the `src/content/docs`
symlink. The home page (`wiki/index.md`) is an agent-maintained
dashboard — see
[`wiki/brain/adrs/home-content-shape.md`](../wiki/brain/adrs/home-content-shape.md).

## Layout

```
ui/
├── src/
│   ├── content.config.ts            (extends Starlight's docsSchema with brain frontmatter)
│   └── content/
│       └── docs           -> ../../../wiki   (symlink, tracked)
├── astro.config.mjs                 (Starlight integration; default outDir ./dist)
├── package.json                     (astro, @astrojs/starlight, pagefind, github-slugger)
├── package-lock.json
├── tsconfig.json                    (extends astro/tsconfigs/strict)
├── Dockerfile
├── serve.mjs                        (production static server; serves ./dist)
├── .gitignore                       (node_modules, dist, .astro, pagefind, .build-cache)
└── README.md                        (this file)
```

The `src/content/docs` symlink lets Starlight read the brain corpus
without copying. Edit pages in `wiki/`; rebuild here.

## Build

```bash
cd ~/projects/brain/ui
npm install                    # first run only
npm run build                  # astro build + pagefind --site dist
npm run dev                    # dev server with hot reload at :4321
```

A successful build emits ~80 pages into `dist/` from the current
corpus (2026-04-30: 78 pages + 404.html + Pagefind index in
`dist/pagefind/`).

The default Astro dev server runs at `http://localhost:4321`. To
preview the production-shaped output (what the Dockerfile ships):

```bash
PORT=8080 node serve.mjs
```

## Substrate decisions

- **Astro + Starlight + Pagefind, npm-installed, no vendoring.**
  See [`wiki/brain/adrs/successor-ssg-for-ui.md`](../wiki/brain/adrs/successor-ssg-for-ui.md)
  for the bet, four rejected alternatives, constraints, and exit
  ramp.
- **Astro's default output dir** (`./dist`) is preserved;
  `serve.mjs` was updated by one line (`public: "public"` →
  `public: "dist"`) per the substrate ADR's "alias it (one-line
  config)" rule.
- **`trailingSlash: 'always'` + `format: 'directory'`** preserves
  the `/<repo>/<page>/` URL shape (the agents' URL-stability contract).
- **`github-slugger@2`** pinned for anchor stability (the agents'
  anchor-stability contract).
- **Pagefind** as the substrate-independent search layer — runs
  post-build in `npm run build`, indexes `public/`, and emits to
  `public/pagefind/`. Survives a future SSG change without
  re-platforming the search layer.

## Lighthouse (mobile, simulated throttling)

Measured 2026-04-30 against the Quartz baseline in the substrate
ADR's § Baseline (pre-swap):

| metric            | Quartz  | Astro+Starlight | Δ          |
|-------------------|---------|-----------------|------------|
| Performance       | 54/64   | **100/100**     | +46/+36    |
| Accessibility     | 82      | **100**         | +18        |
| Best Practices    | 96      | 96              | 0          |
| SEO               | 100     | 100             | 0          |
| FCP               | 5.3s    | **0.9s**        | -4.4s      |
| LCP               | 6.2s    | **0.9s**        | -5.3s      |
| JS transferred    | 705 KB  | **4 KB**        | -701 KB    |

## Deploy (Railway)

The brain repo is set up to deploy this UI to Railway out of the
box:

- `railway.toml` at the repo root tells Railway to build from
  `ui/Dockerfile`.
- `ui/Dockerfile` is a multi-stage build whose context is the brain
  repo root: stage 1 installs deps + replaces the
  `src/content/docs` symlink with a real copy of `wiki/` + runs
  `npm run build`; stage 2 carries over `public/` + `serve.mjs` +
  the single `serve-handler` runtime dep, and runs `node serve.mjs`
  (which binds to `$PORT`).
- `ui/serve.mjs` is a ~25-line static server using `serve-handler`.
- `.dockerignore` at the repo root keeps the build context lean.

To deploy:

1. Connect the brain GitHub repo as a Railway service.
2. Railway picks up `railway.toml` automatically; no extra
   configuration required.
3. Railway exposes a public URL. The healthcheck path is `/`.

Local container check:

```bash
docker build -f ui/Dockerfile -t brain-ui .
docker run --rm -p 8080:8080 -e PORT=8080 brain-ui
curl http://127.0.0.1:8080/
```

## Auto-refresh

`tools/ui-build.sh` is the build wrapper invoked by:

- The Claude Code hook (`.claude/settings.json` PostToolUse on
  Edit/Write to `wiki/**`) — smoke-builds into `ui/.build-cache/`
  so a wiki edit immediately surfaces any breakage.
- CI smoke step (`.github/workflows/validate.yml`) — same wrapper.

See [`wiki/brain/adrs/ui-auto-refresh-hook.md`](../wiki/brain/adrs/ui-auto-refresh-hook.md).

## Customising the UI

- **Sidebar** — edit `astro.config.mjs` § sidebar. Currently seeded
  with the active repos + brain self-tracking; the wayfinding
  catalog lives in `wiki/index.md` § Where to find things.
- **Layout / theme overrides** — Starlight component overrides
  via `astro.config.mjs` § components. None set today.
- **Frontmatter additions** — extend the schema in
  `src/content.config.ts`. The schema is permissive (every field
  is optional) so it never over-constrains pages that are valid
  per `tools/brain.py validate`.
