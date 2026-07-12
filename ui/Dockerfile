# syntax=docker/dockerfile:1
#
# Production container for the brain UI.
#
# Build context MUST be the brain repo root (so the build can pull in
# both ui/ and wiki/):
#
#   docker build -f ui/Dockerfile -t brain-ui .
#
# Railway is configured to do this via railway.toml at the repo root.
#
# Two stages:
#   1. builder  — install Astro+Starlight+Pagefind deps, run
#                 `npm run build` (astro build + pagefind index).
#   2. runtime  — alpine + only `serve-handler`. ~200MB final image.

FROM node:22-slim AS builder
WORKDIR /app

# Install build deps from the lockfile only — fast, deterministic.
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copy the rest of the UI source.
COPY ui/ ./

# The repo's src/content/docs is a symlink to ../../../wiki. Docker
# can't follow symlinks outside the build context, so replace it with
# a real copy of wiki/ for the build.
RUN rm -f src/content/docs
COPY wiki/ ./src/content/docs/

# Build the static site → /app/dist (Astro's default outDir).
# `npm run build` runs `astro build && pagefind --site dist`, so
# Pagefind's search index lands inside dist/pagefind/.
RUN npm run build

# ---

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production

# serve.mjs only imports `serve-handler`. Install just that — skip the
# Astro build deps (which are not needed at runtime, only at build).
# Keeps the runtime image small (~200MB).
RUN echo '{"name":"brain-ui-runtime","version":"0.0.0","private":true,"type":"module","dependencies":{"serve-handler":"6.1.6"}}' > package.json && \
    npm install --no-audit --no-fund --omit=dev --no-package-lock

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/serve.mjs ./serve.mjs

EXPOSE 8080
CMD ["node", "serve.mjs"]
