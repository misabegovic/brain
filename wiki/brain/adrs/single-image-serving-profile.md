---
title: "Deployment is one infra-agnostic image with an env-selected surface; instances isolate by env ports and hashed unit names; Railway is a reference target, not a dependency"
kind: decision
status: accepted
updated: 2026-07-10
confidence: medium
summary: >
  One infra-agnostic container image; BRAIN_SURFACE selects ui/mcp/datasette on the platform port; per-instance isolation via env ports and hashed timer units. Railway is a reference target, not a dependency.
sources:
  - ../prds/composable-role-views.md
  - ../../../sources/conversations/2026-07-10--self-hosting-roadmap-intent.md
  - ../roadmap.md
---

# Deployment is one infra-agnostic image with an env-selected surface; instances isolate by env ports and hashed unit names; Railway is a reference target, not a dependency

**Decision.** The 0.7 hosting slice ships as one container image built
from the repo with a two-stage build (the UI compiled in a Node stage,
served from a Python stage that carries the kernel, the corpus, and the
derived index baked at build time). The image exposes the three read-only
surfaces — static UI, the MCP server in serving mode, and the Datasette
browse tier — and an environment variable selects which one binds the
platform-injected port; the other two start on internal ports for private
networking. Serving mode is forced on in the image: ai-suggestions
excluded, query audit log active, and the workbench structurally refused.
**Railway is the reference target** (a repo-root build config points at
the deployment Dockerfile) **but nothing depends on it**: the entrypoint
reads only generic environment variables, runs unchanged directly on a
host for local emulation, and a compose file starts all three surfaces on
deliberately non-default local ports. Content updates are redeploys —
state is git; there is no database to migrate.

The same decision covers **multi-instance isolation on one machine**,
because local emulation must never disturb another brain running on the
same host: serve and MCP ports honour instance-level environment
variables with unchanged defaults, and the accumulation timer's systemd
unit name embeds the instance directory name plus a short hash of its
absolute path — two checkouts named alike (a projects-root brain and a
client brain in a subfolder) get distinct units, and the installer
migrates the older shared-name unit when it points at the same repo.

## Context

The operator set the frame: assume Railway on a single instance, stay
infra-agnostic, and prove locally that a second brain can run without
hurting the one already on the machine. The serving software (0.6) was
already deployment-shaped — read-only processes, no auth of their own,
identity handled by whatever fronts them — so the remaining questions
were packaging, port ownership on platforms that inject a single public
port, and host-level collisions between instances.

The single-injected-port constraint drove the surface selector: platforms
in this class route one port per service, so the image must answer
"which surface is public here?" per deployment rather than baking a
multiplexer. Running the same image once per desired public surface
composes cleanly on any platform with private networking, and the
compose file demonstrates exactly that shape locally. Baking the corpus
and index at build time (rather than mounting) matches the brain's
substrate: the repo is the deployable artifact, a merge is a release,
and rollback is a git operation. The isolation half surfaced a live
near-miss: the timer installer's original shared unit name would have
collided the moment the client brain adopted the kernel, since both
checkouts share a directory basename — the hash suffix closes that class
of collision permanently.

## Alternatives

- **One image, env-selected surface** *(chosen)* — one artifact to
  build, test, and emulate; per-platform behaviour reduces to
  environment variables.
- **One image per surface** — three Dockerfiles drifting apart for no
  isolation gain; rejected.
- **An in-image reverse proxy multiplexing all surfaces on one port** —
  adds a proxy dependency and configuration surface the platforms in
  scope already provide at their edge; rejected for the kernel, open to
  an operator's own compose override.
- **Mount-the-repo instead of baking** — enables live content updates
  without redeploys, but reintroduces host coupling (volumes, sync) and
  loses the merge-is-a-release property; rejected as the default, and
  the compose file documents it as the local-development variant.
- **Railway-specific configuration throughout** (their service schema,
  private-network names) — rejected: the reference target earns a
  root-level build pointer and documentation, nothing more.
- **Do nothing (localhost only)** — leaves the serving slice
  permanently theoretical. Rejected by the bet.

## Consequences

- **Closes** the packaging question: one Dockerfile, one entrypoint,
  every knob an environment variable (`BRAIN_SURFACE`, `PORT`, internal
  port overrides, `BRAIN_BIND`).
- **Closes** the host-collision class: per-instance ports
  (`BRAIN_PORT`, `BRAIN_MCP_PORT`) and hashed timer unit names; the
  health checklist reports the instance-specific unit.
- **Opens** deployment to any container platform unchanged, and local
  emulation as a first-class, collision-free operation (compose on
  non-default ports, or the entrypoint run directly).
- **Costs** a redeploy per content update in the baked default —
  accepted; the corpus changes at git pace, not request pace.
- **Costs** image weight from carrying Node output plus Python plus
  Datasette (~hundreds of MB); acceptable for a single-instance target,
  and slimming is an optimisation left until it matters.

## Build notes

Shipped 2026-07-10. Verified by local emulation: the image built from a
clean context, all three surfaces answered on compose's non-default
ports, and the development brain's own server ran simultaneously on its
default port throughout — no port, unit, or file contention. The
inherited dockerignore (from the origin deployment's UI-only image) was
rewritten: this image needs the kernel and sources, excludes secrets,
local state, and tests.
