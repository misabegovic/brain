---
persona: priya-non-terminal-pm
scenario: reading-journeys
version: 0.19.3
date: 2026-07-12
executed_by: claude subagent
---

# Priya — reading-only journeys through the rendered product

Real execution: `ui/` deps installed (`npm install`), site built via
`tools/ui-build.sh` into `ui/.build-cache/`, served with
`BRAIN_PORT=8802 python3 tools/brain.py serve`, every page below
fetched with curl against `http://localhost:8802`. Priya never opens
a terminal; the setup steps above are the harness standing in for
"a teammate deployed this for her" — everything from here on is
what she sees in a browser.

## Journey A — the briefing at `/`: the 10-second test

**Expectation (Priya):** land on the front page and know, before my
coffee cools, what needs my attention and why.

**What actually happened:** fetched `/` (HTTP 200, 21 KB). Real
excerpt of the visible text, top of page:

> Briefing — The brain's judgement of what matters right now · v0.19.3
>
> **Needs you 1** — hypothesis — confirm or refute · insight · today
> "The quickstart's third command (`brain`) is fragile on cold-start
> machines — Playthrough-born hypothesis … Awaiting human
> confirmation."
>
> **In flight 0** — No bets in flight. Shape one: tell your agent
> "let's explore \<idea\>" and a pitch lands on the table below.
>
> **On the table 3** — open discussion · 2 days old · "What stands
> between this repo and being a credible market entrant?" …

**Verdict: pass.** Within ten seconds I know: one thing needs a
human (clearly labelled as an unconfirmed hypothesis, not a fact),
nothing is in flight, three discussions are open. The orientation
strip below (Where we were / are / going) is dated and readable.
The one thing I noticed: the "In flight 0" empty state tells me to
"tell your agent" — that works for me (chat, not terminal), and it's
honest that this surface expects an agent wired up.

**Friction (small, stays here):** the band label "hypothesis —
confirm or refute" plus the `insight` chip is the right idea, but
the chips (`insight`, `topic`, `confidence: …`) carry no tooltip or
legend anywhere on the page — I learned what "insight" means from
the onboarding deck, not from the surface using the word.

## Journey B — trace a decision: why was the embedded terminal removed?

**Expectation:** starting from the briefing/trail, following links
only, find the *why* without asking an engineer.

**Path actually walked:** `/` → nav "Trail" → `/trail/` → clicked
the accepted decision "The kernel's interaction surfaces are MCP and
the CLI — the embedded terminal retires with the chat pane" →
`/brain/adrs/mcp-cli-surface/`. **Two clicks.**

The trail showed the chain honestly (real excerpt):

> decision · superseded · "The workbench is a loopback browser page
> over a stdlib PTY bridge …" → superseded by **mcp-cli-surface**
>
> decision · accepted · "The kernel's interaction surfaces are MCP
> and the CLI — the embedded terminal retires with the chat pane"
> ⬅ supersedes **mcp-cli-terminal-surface**

The ADR page itself answered my question in plain narrative (real
excerpt from `/brain/adrs/mcp-cli-surface/`):

> "…the deletion test cut the other way on inspection: the embedded
> terminal is an arrangement of windows, not a capability — the
> operator's own terminal emulator beside a browser tab reproduces
> it exactly, with better ergonomics. What the kernel was actually
> paying for it: the largest remaining maintenance surface relative
> to value, and the one component a security review of a public
> release flags first…"

**Verdict: pass, genuinely good.** I could put that paragraph in a
meeting doc verbatim. The Alternatives section even names the prior
rejected position and why it flipped.

**Friction (decision-worthy, see suggestion):** the trail's
supersedes links render raw slugs as the link text — "⬅ supersedes
`mcp-cli-terminal-surface`", "➡ superseded by `state`". I clicked
"state" not knowing what I'd get. Everywhere else the product gives
me human titles; here, at exactly the trust-critical junction
(which record replaced which), it hands me machine names.

## Journey C — `/dashboard/`, `/trail/`, `/graph/`: meeting prep

**`/dashboard/`** (real excerpt): "53 pages · 143 links · 0 orphans ·
0 pages >30d old · 0 inbox pending · 60 audited ops · — verdicts
graded useful". Pages by kind/status/confidence bars, most-linked
hubs. **Verdict: half-useful.** "0 pages >30d old" is a sentence I
can say in a meeting ("nothing here is stale"). But "orphans",
"audited ops", "verdicts graded useful" are internal mechanics with
no translation — I skip them, which means the dashboard is speaking
to the operator, not to me. Usable, not built for me.

**`/trail/`** — the best meeting-prep surface of the three. Newest
first, kind + status chips on every row, supersedes chains visible.
The story of the week (chat pane removed, then the terminal,
presentation layer shipped) is readable top to bottom.

**`/graph/`** — "53 pages, 143 links — grouped by shelf, ordered by
inbound degree." A build-time SVG. Pretty, tells me which pages are
hubs; I would not open it before a meeting. No friction, no value
for me either.

## Journey D — `/search/` and the PM view

**`/search/`:** the static HTML is an empty shell — the Pagefind UI
is JavaScript-mounted. In a browser it works; verified the index is
real by decompressing the built Pagefind fragments: 71 pages
indexed; a query for "embedded terminal" has 16 candidate pages and
`/brain/adrs/mcp-cli-surface/` is among the top fragments with its
full title. So search would have found my Journey B decision
directly. **Verdict: pass** (noting there is no no-JS fallback or
"search requires JavaScript" notice — blank page if scripts fail).

**`/_views/custom/pm/` — the view with my name on it.** Real excerpt:

> PM view · meta · living · confidence: high · updated 2026-07-12
>
> Auto-generated by `brain.py views` from `views/pm.yml` — edit the
> spec, not this page. Audience: team/pm.
>
> Open initiatives — (no rows)
> Pitches awaiting a bet — (no rows)
> Insights — `insights/quickstart-third-command-fragility.md` · The
> quickstart's third command (brain) is fragile… · draft · low · 2026-07-12
> Ingest queue — (no rows)

**Verdict: the content is right, the voice is wrong.** This is
supposed to be *my* brief, and its first sentence is an instruction
to people who edit YAML specs with a CLI. The first column of the
one populated table is a raw file path (`insights/….md`), the empty
sections say "(no rows)" with no hint of what would fill them, and
"Ingest queue" is pipeline jargon. Decision-worthy — see suggestion.

## Journey E — `/brain/`, a project shelf home: does the Project overview onboard me?

The shelf home is the hand-written index (readable, well-linked, if
dense with slash-command references), and below it the generated
**Project overview**: "41 pages · freshest 2026-07-12", a "Start
here — the reading path", Open work (the three topics), Recent
decisions, and an honest gap line ("Not written yet: purpose,
architecture — an ingest pass (`/in brain`) starts them").

**Verdict: mostly yes — with one trust-breaking defect.** The
"Recent decisions" list renders four ADRs with only date chips
(real excerpt, order as shown):

> 2026-07-12 · The workbench is a loopback browser page over a
> stdlib PTY bridge … *(superseded — but nothing on this row says so)*
> 2026-07-12 · Playthroughs are executed skills with immutable transcripts …
> 2026-07-12 · The kernel's interaction surfaces are MCP, **CLI, and
> the terminal** — no first-party chat pane *(superseded)*
> 2026-07-12 · The kernel's interaction surfaces are MCP **and the
> CLI** — the embedded terminal retires with the chat pane *(accepted)*

Two of the four are superseded, and the last two *directly
contradict each other* in their titles — same date chip, no status
chip, nothing to tell a reader which one is the record. The trail
page gets this right (status chips + supersedes arrows); the
overview — the section explicitly built to onboard someone —
doesn't. If I'd skimmed only the overview before a meeting I could
have cited "MCP, CLI, and the terminal" as current. Decision-worthy
— see suggestion.

Also noted: the honest-gaps line speaks agent (`/in brain`) on a
reading surface — small, stays here.

## The AI-draft vs approved-record test

The distinction *did* survive everywhere I could test it today:

- The one insight is banner-labelled on its own page ("Playthrough-
  born hypothesis … capped at confidence: low until a human
  cold-start run confirms or refutes it") and card-labelled on the
  briefing ("Awaiting human confirmation").
- The shelf home has an explicit "AI suggestions (drafts for human
  review) — (none yet)" section.
- **Untestable as-found:** the corpus contained zero
  `ai-suggestions/` pages at walk time, so the page-level
  AI-suggestion banner could not be observed rendering. (The
  suggestions this very playthrough files will end that state.)

The counterexample is Journey E: not an AI draft mislabelled, but a
*superseded human decision* presented undifferentiated from the
current one. My trust requirement is "what I read is the approved,
current record" — status honesty and authorship honesty are the same
promise to me.

## "Would I have given up here?"

Asked honestly at the PM view (Journey D): **on the product, no** —
the briefing and the trail carried me to real answers an engineer
would otherwise have had to give me, and the terminal-removal "why"
was two clicks and genuinely well-written. **On the PM view itself,
yes** — I'd have closed the tab at "edit the spec, not this page,"
concluded that view belongs to whoever owns `views/pm.yml`, and not
returned. And Journey E's contradictory decision pair is my
nightmare-scenario seed: cite the wrong one in a meeting once, and
I stop trusting every generated list on the site.

## Findings by disposition

| # | Finding | Disposition |
|---|---------|-------------|
| 1 | Project overview "Recent decisions" shows superseded ADRs with no status — contradictory titles side by side | AI-suggestion PRD: `wiki/brain/ai-suggestions/prds/status-honest-generated-reading-lists.md` |
| 2 | PM view opens with spec-editor instructions, raw paths, "(no rows)" | AI-suggestion PRD: `wiki/brain/ai-suggestions/prds/pm-view-reads-like-a-brief.md` |
| 3 | Trail supersedes links render slugs, not titles | folded into PRD #1 (same promise: reading surfaces speak human) |
| 4 | Kind/status/confidence chips have no tooltip/legend anywhere | transcript-only |
| 5 | `/search/` blank without JS, no notice | transcript-only |
| 6 | Dashboard jargon ("audited ops", "verdicts graded useful") untranslated | transcript-only |
| 7 | Shelf-home gap line speaks slash-command (`/in brain`) | transcript-only |
| 8 | AI-suggestion page banner unobservable — no drafts in corpus at walk time | transcript-only (state note) |

Server killed at end of session; no machine state mutated outside
the worktree.
