---
description: Review a brain PR; auto-merge if every guardrail passes (different session from author)
---

Apply the `review` skill to: $ARGUMENTS

`$ARGUMENTS` is the PR number. If empty, list open PRs with `gh pr
list` and pick the oldest unreviewed one.

Run the full protocol: two-agent rule, validate + check-sources,
restricted-paths gate, sources/ immutability, confidence floor,
content-quality pass, approve + merge — or refuse with a posted review
comment on any guardrail failure. After merge, append the audit line
to `log/log.md` on `main`.
