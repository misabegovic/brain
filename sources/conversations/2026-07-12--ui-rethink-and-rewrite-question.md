---
title: "Conversation capture: rewrite question + the human-legible UI direction"
kind: source
captured: 2026-07-12
participants: operator (Muhamed), claude (fable 5)
context: >
  Same-day follow-up to 0.16.0. The operator asked whether the brain
  should be rewritten in Ruby (Herb, html.erb, ViewComponents) or
  Rust, and in the same breath redefined what the UI layer should
  become. The rewrite was recommended against; the UI direction
  became a pitch.
---

# Conversation capture — UI rethink + rewrite question (2026-07-12)

**Operator:** should we rewrite the brain in Ruby or Rust or
similar? For Ruby: Herb tooling, html.erb + ViewComponents,
replacing the UI layer — and redefining what the UI layer is for:
the brain as a place for human and agent collaboration; humans
can't read all of this text all the time; they need components,
graphs, executive summaries — while keeping the verbose stuff for
agents as real sources. We might need to rebuild and rethink the
UI layer.

**Agent position (summarised):** no to the language rewrite — the
kernel's product is the methodology; stdlib-only Python is
load-bearing for the cold-start story (python3 preinstalled
everywhere; Ruby needs version-manager bootstrapping, Rust a
toolchain or binary releases); no performance problem exists; a
rewrite restarts test/trail/unattended-days maturity for zero new
capability; the regenerative thesis makes a *future* rewrite cheap
if ever justified. Yes — strongly — to the UI-layer rethink as its
own initiative: keep the verbose wiki as the agent's layer, add an
agent-maintained presentation synthesis for humans (summaries as
schema, components and graphs on the existing Astro stack, driven
by the derived index). Operator agreed to shape it as a pitch, with
the build held for the betting decision.

**Operator (direction for the pitch, verbatim intent):** "the UI
should breathe the Shape Up philosophy and should be highly
opinionated as to what it shows and when. the UI layer should bring
to attention what needs to be attended to. it needs to show where
we are, where we were and where we are going. bets, ideas,
pitches... also if I connect to an external source and consume
errors or state within Langfuse for example, the agent processing
that should know if I need to take a look at that or not, if it's
important etc. making the brain my true partner"

Two threads in that direction: (1) an opinionated, Shape
Up-native presentation layer (lifecycle-aware rendering; the
betting table; past/now/target orientation; attention-first home);
(2) attention *judgement* as part of the tend loop — the agent
triages ingested connector signal (needs-operator / fyi / routine)
and the UI's attention surface renders exactly that verdict. "The
brain as true partner" = opinionated attention, not neutral
rendering.
