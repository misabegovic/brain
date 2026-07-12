---
description: Open a PR for current changes (creates feature branch, runs validate, fills structured body)
---

Apply the `pr` skill to: $ARGUMENTS

`$ARGUMENTS` is the one-line summary of the change (used for branch
name and PR title). If empty, ask the user.

Run the full protocol: pre-flight (feature branch, restricted-paths
honesty), local validate + check-sources, commit, push, `gh pr
create` with structured body. Return the PR URL.
