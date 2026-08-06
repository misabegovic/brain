#!/bin/bash
# Intent-first hooks — the mechanical half of AGENTS.md § Working
# inside a sibling repo, rule 6 (intent first).
#
# Modes (all read the Claude Code hook JSON from stdin):
#   gate    PreToolUse on Edit|Write|MultiEdit — block the first edit
#           into each sibling repo *per piece of work* (re-armed on
#           every user prompt), surfacing the file's governing specs
#           (brain.py enola govern). The retry proceeds: the gate
#           forces the reading, never the verdict. Absent graph
#           degrades to a named skip.
#   record  PostToolUse on Edit|Write|MultiEdit — record what moved
#           this turn: sibling code vs brain wiki pages (specs).
#   reset   UserPromptSubmit — a new user message begins a new piece
#           of work: clear gate acks and the turn record.
#   debt    Stop — if sibling code moved this turn and no spec moved,
#           block the stop once and demand the accounting: amend the
#           governing page, or state why the work is already aligned.
set -u

mode="${1:-}"
input=$(cat 2>/dev/null || true)
sid=$(jq -r '.session_id // "nosession"' <<<"$input" 2>/dev/null)
statedir="${TMPDIR:-/tmp}/brain-intent-first"
mkdir -p "$statedir"

brain_dir=$(cd "${CLAUDE_PROJECT_DIR:-.}" && pwd -P)

classify() {
  local f="$1" probe top
  case "$f" in
    "${BRAIN_PROJECTS_ROOT:-$HOME/projects}"/*) ;;
    *) return 1 ;;
  esac
  probe=$(dirname "$f")
  while [ ! -d "$probe" ] && [ "$probe" != "/" ]; do
    probe=$(dirname "$probe")
  done
  top=$(git -C "$probe" rev-parse --show-toplevel 2>/dev/null) || return 1
  top=$(cd "$top" && pwd -P)
  if [ "$top" = "$brain_dir" ]; then
    case "${f#"$top"/}" in
      wiki/_views/*|wiki/_archive/*|wiki/_state/*) return 1 ;;
      wiki/*.md) printf 'spec\t%s\t%s\n' "$top" "${f#"$top"/}"; return 0 ;;
      *) return 1 ;;
    esac
  fi
  printf 'code\t%s\t%s\n' "$top" "${f#"$top"/}"
}

case "$mode" in
  gate)
    f=$(jq -r '.tool_input.file_path // empty' <<<"$input" 2>/dev/null)
    [ -z "$f" ] && exit 0
    line=$(classify "$f") || exit 0
    kind=$(cut -f1 <<<"$line")
    [ "$kind" = "code" ] || exit 0
    top=$(cut -f2 <<<"$line")
    rel=$(cut -f3 <<<"$line")
    repo=$(basename "$top")
    ack="$statedir/${sid}-${repo}.ack"
    [ -e "$ack" ] && exit 0
    touch "$ack"

    govern=$(cd "$brain_dir" && timeout 30 python3 tools/brain.py enola govern "$rel" 2>&1 | head -40)
    [ -n "$govern" ] || govern="(enola govern unavailable — named skip; consult the wiki/<repo>/ shelves manually)"

    cat >&2 <<EOF
intent-first gate (${repo}): first edit for this piece of work.

The contract is intent first. Before this code moves: read the
governing specs below and check the intended change against them. If
the work deviates from what the PRD/ADR/build-notes record, amend the
page first (then 'brain.py intent stamp'); if nothing governs this
work, surface that and ask whether it should be shaped.

Governing intent for ${rel}:
${govern}

Retrying the edit proceeds. This gate re-arms on every user message;
within one piece of work it will not fire again.
EOF
    exit 2
    ;;

  record)
    f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' <<<"$input" 2>/dev/null)
    [ -z "$f" ] && exit 0
    line=$(classify "$f") || exit 0
    printf '%s\n' "$line" >> "$statedir/${sid}.turn"
    exit 0
    ;;

  reset)
    rm -f "$statedir/${sid}"-*.ack "$statedir/${sid}.turn" "$statedir/${sid}.debt-blocked"
    exit 0
    ;;

  debt)
    turn="$statedir/${sid}.turn"
    [ -f "$turn" ] || exit 0
    [ -e "$statedir/${sid}.debt-blocked" ] && exit 0
    grep -q '^code' "$turn" || exit 0
    grep -q '^spec' "$turn" && exit 0
    touch "$statedir/${sid}.debt-blocked"

    summary=$(awk -F'\t' '$1 == "code" { n = split($2, a, "/"); print "  " $3 " (" a[n] ")" }' "$turn" | sort -u | head -15)

    cat >&2 <<EOF
intent debt: sibling code moved this turn, and no governing page did.

Changed without a spec moving:
${summary}

Before finishing: either amend the governing PRD/ADR/build-notes to
match what was just built (then 'brain.py intent stamp'), or state
explicitly — in your reply — why the change is already covered by the
specs as written. This check blocks once per turn.
EOF
    exit 2
    ;;

  *)
    printf 'usage: %s {gate|record|reset|debt}\n' "$0" >&2
    exit 64
    ;;
esac
