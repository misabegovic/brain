# Personas

Three folders, three audiences. `agents/` ships with the kernel;
`team/` and `users/` are authored per-organisation when you adopt
the shell.

```
personas/
├── agents/           # roles the brain plays during /shape (PM, Tech Lead, Developer)
├── team/             # internal employees / roles — drive brain UX requirements
└── users/            # the organisation's customers — anchor /feedback attribution
                      # and PRD persona references
```

1. **`agents/`** — fictional roles the brain itself plays during the
   `/shape` workflow: the PM agent shapes PRDs, the Tech Lead agent
   shapes ADRs, the Developer agent drives Phase 3 builds. Generic;
   part of the kernel.
2. **`team/`** — archetypes of the people *inside* the organisation
   who use the brain (engineers, designers, PMs, leadership). They
   drive brain UX requirements and are surfaced in `/rfc` audience
   pools. Author ~5–10 of them once you know the org.
3. **`users/`** — archetypes of the organisation's *customers* and
   external stakeholders. They anchor `/feedback` attribution and
   the "Affected personas" sections of PRDs and insights.

## Authoring convention

One file per persona, kebab-case, named `<first-name>-<role>.md`
(e.g. `dana-support-lead.md`). Fictional first names; never real
people. Each file opens with YAML frontmatter (`role:`, `goals:`,
`frustrations:`) followed by a short narrative profile — enough
texture that an `/rfc` pass can argue from their point of view.

Keep the sets small and load-bearing: a persona earns its file when
some skill (`/rfc`, `/feedback`, `/shape` Phase 1) would cite it.
