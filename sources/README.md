# sources/ — raw, immutable inputs

Everything under this directory is **additive only**: agents may add
new files but never modify or delete existing ones. Snapshots land
here before the wiki synthesises them — external planning pages,
prep notes, user-feedback batches, web captures.

Conventional subfolders (created on first use, not preemptively):

- `notion/` — external planning-tool snapshots (`<slug>--<shortid>.md`)
- `conversations/` — `/capture` snapshots
- `ai_user_feedback/` — summarised feedback batches
- `web/` — web captures, including `web/competitors/<competitor>/`
- `research/` — deepening-run findings (`/tend` research items)
- `github/`, `slack/` — connector snapshots (releases, PR batches,
  channel transcripts)
