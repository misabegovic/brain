---
persona: .claude/personas/users/noor-cold-start-adopter.md
scenario: README quickstart on a fresh clone
version: 0.15.0
date: 2026-07-12
executed_by: claude (fable 5)
---

# Playthrough — Noor walks the README quickstart (0.15.0)

First protocol run of the playthrough skill (dogfood, same session
the skill shipped). Real execution: fresh `git clone` of the repo
into a scratch directory, README followed verbatim, servers
actually started, pages actually fetched. Machine side-effects
(timer unit, PATH symlink) were removed after the walk.

## Step 1 — clone

`git clone file://<repo> brain && cd brain` — clean. Noor skims the
README first screen: pitch, screenshot, three ideas, quickstart.
*In character:* "I know what this claims to be inside ninety
seconds. Good start."

## Step 2 — `python3 tools/brain.py setup`

Ran with piped (non-tty) stdin to emulate scripted/CI use, empty
answers for org/repos, `n` for the optional installs.

**Finding A (defect, fixed in-session).** `confirm()` returned its
default — `True` — whenever stdin was not a tty and `--yes` was
absent. The run *silently installed* a systemd user timer
(`brain-brain-2c1a58-schedule.timer`), a `~/.local/bin/brain`
symlink, and npm dependencies, while the piped answers were
consumed by the org/repos questions only. Observed output:

    Created symlink .../brain-brain-2c1a58-schedule.timer ...
    ✓ accumulation timer
    ✓ `brain` on PATH
    ✓ browse-UI dependencies

A tool that mutates the machine (timer, PATH) on piped stdin
without consent is a trust-breaker for exactly this persona. Fixed:
non-interactive `confirm()` without `--yes` now skips with a
visible hint ("re-run with --yes to accept"). Verified:

    − install the daily accumulation timer? — skipped (non-interactive; re-run with --yes to accept)
    − put the `brain` command on your PATH (~/.local/bin)? — skipped ...

The org/active-repos questions themselves behaved well for Noor:
empty answers skip cleanly with "edit brain.config.yml later" — she
was not forced to answer things she can't know on minute two.

## Step 3 — `brain` (open the app)

**Finding B (defect, fixed in-session).** On a fresh clone no UI
build exists (`ui/.build-cache` is gitignored; setup installs deps
but does not build). The app page's knowledge pane — and a direct
visit to `/` — rendered a raw JSON error:

    {"error": "unknown endpoint (and no UI build to serve — run tools/ui-build.sh)"}

This is Noor's named giving-up point ("an app that opens to nothing
and no obvious next move"). The status poll does kick a background
first build (self-heal from 0.14.2), but for up to a minute the
main pane was a JSON blob with no explanation. Fixed: when the app
is mounted and no build exists, unknown paths render a
self-refreshing "Building the knowledge site for the first time…"
placeholder until the build lands. Verified on the fresh clone:
placeholder renders with no build; rendered home serves once the
kicked build completes.

**Finding C (hypothesis → insight).** The quickstart's third
command assumes `brain` reached the PATH: the setup step is
optional (consent), targets `~/.local/bin` (not on PATH on all
platforms — macOS notably), and a skipped or failed step leaves
the README's third command a dead end with no fallback shown.
Routed to `wiki/insights/quickstart-third-command-fragility.md`
(`confidence: low` — needs a real cold-start human to confirm).

## Give-up verdict (in character)

"Pre-fix: I'm gone at step 3 — a JSON error where the product
should be. Post-fix: the placeholder tells me the machine is
working for me and the page becomes the site within a minute; I'd
stay. The setup questions I couldn't answer let me skip them,
which I appreciated. If `brain` isn't found after setup I'd need
the README to tell me what to type instead."

## Disposition

- Finding A — fixed in-session (consent default), transcript-only.
- Finding B — fixed in-session (first-run placeholder), transcript-only.
- Finding C — insight page at `confidence: low`, awaiting human
  confirmation on a real machine.
