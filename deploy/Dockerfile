# brain — infra-agnostic serving image (per
# wiki/brain/adrs/single-image-serving-profile.md).
#
# One image, three read-only surfaces; BRAIN_SURFACE picks which one
# binds the platform's $PORT (Railway/Fly/Render all inject PORT):
#   ui        static Astro site           (default)
#   mcp       brain-mcp --http (serving mode)
#   datasette faceted browse + SQL over the derived index
# The other two start on internal ports for private networking.
# The workbench is structurally absent: serving mode refuses it.

FROM node:22-slim AS ui-build
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY ui/ ./
COPY wiki/ /app/wiki/
RUN npm run build

FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyyaml tiktoken datasette
WORKDIR /brain
COPY . .
COPY --from=ui-build /app/ui/dist /brain/ui/dist
RUN python3 tools/brain.py index
ENV BRAIN_SERVING=1
EXPOSE 8080
ENTRYPOINT ["bash", "deploy/entrypoint.sh"]
