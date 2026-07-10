# Serving deployment (0.7)

One infra-agnostic image, three read-only surfaces (per
`wiki/brain/adrs/single-image-serving-profile.md`):

| BRAIN_SURFACE | serves                                             |
|---------------|----------------------------------------------------|
| `ui` (default)| static Astro site of the wiki                      |
| `mcp`         | `brain-mcp --http` in serving mode (POST /mcp)     |
| `datasette`   | faceted browse + SQL over the derived index        |

The selected surface binds the platform-injected `$PORT`; the other
two start on internal ports (`BRAIN_MCP_PORT`/`BRAIN_UI_PORT`/
`BRAIN_DS_PORT`) for private networking. `BRAIN_SERVING=1` is forced:
ai-suggestions excluded, query audit log on, workbench structurally
refused.

**Railway** (reference target): repo root `railway.toml` points the
build at `deploy/Dockerfile`; set `BRAIN_SURFACE`, put your
identity-aware proxy in front. **Anything else**: `docker build -f
deploy/Dockerfile .` and run with `PORT` set — no platform
assumptions exist.

**Local emulation** (safe beside a development brain — non-default
ports): `docker compose -f deploy/docker-compose.yml up --build` →
ui :9080, mcp :9081, datasette :9082. Or without docker:
`PORT=9080 bash deploy/entrypoint.sh` runs the same script directly.

Content updates: the image bakes the corpus at build time — redeploy
on merge (CI hook) or mount the repo and restart. State is git; there
is no database to migrate or back up.
