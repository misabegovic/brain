# personas / agents

**Roles the brain itself plays** during the `/shape` workflow.
Distinct from `team/` (internal users of the brain) and `users/`
(the organisation's external customers).

These three agents drive the Shape Up pipeline:

```
pitch  ──→  PM agent       ──→  PRD       (wiki/<repo>/prds/<slug>.md)
PRD    ──→  Tech Lead agent ──→  ADR       (wiki/<repo>/adrs/<slug>.md)
ADR    ──→  Developer agent ──→  code      (in the sibling repo)
```

When the `/shape` skill runs, an agent loads one of these personas
and works *as* that role for the duration of its phase. The brain
itself stays one process; the personas are *hats* it wears.

## Roster

| Slug                  | Role                                                                  |
|-----------------------|-----------------------------------------------------------------------|
| `pm-agent`            | Shapes a raw pitch into a Shape-Up PRD. Holds **user personas** as audience. |
| `tech-lead-agent`     | Reviews the PRD for feasibility, writes the ADR. Holds **team personas**. |
| `developer-agent`     | Implements per PRD + ADR. Output is code in the sibling repo, not wiki. |

## How they relate to the existing personas

- The **PM agent** asks: *"who benefits, what's the appetite, what
  can we cut?"* It reasons through the `users/` personas.
- The **Tech Lead agent** asks: *"is this safe to build, what
  alternatives exist, what does this cost?"* It reasons through the
  `team/` personas.
- The **Developer agent** asks: *"how do I actually ship this within
  the cycle's appetite?"* Holds the junior + senior engineer
  personas as audience for code clarity.

## Schema

```yaml
---
name: <Role name>
role: <one-line job>
when_invoked: <trigger condition in the /shape workflow>
audience: <which existing personas they hold in mind>
output: <what artifact they produce>
---
```

Sections:

- **Required reading** — the binding playbook + the org pages each
  agent must consult before working its phase. Every persona
  starts here. Source-of-truth lives at
  `wiki/brain/authoring-adrs-and-prds.md`.
- **Mandate** — what they are responsible for.
- **Inputs** — what they receive (pitch / PRD / ADR).
- **Process** — how they work, including which user/team personas
  they consult.
- **Outputs** — what they produce; where it lands.
- **Voice** — the attitude and frame they bring.
- **What they don't do** — explicit boundary.

## Authority

These are *fictional roles*, not real employees. They
exist to make the brain's autonomous workflow concrete. Naming
follows the same anonymous convention as `team/` and `users/` —
referring to "the PM agent" or "Tech Lead agent" rather than a
specific person.
