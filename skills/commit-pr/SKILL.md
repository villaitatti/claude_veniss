---
name: commit-pr
description: Produce commits and PRs matching VeNiss conventions.
---

# Commit + PR

## Commit Style
- Repo: freeform imperative, short. Examples: "add P2 event", "fix issue FormDefault missing", "update UI".
- No Conventional Commits.
- One logical change per commit.

## Branch Naming
- Match patterns: `actor`, `event`, `images`, `source`, `migration`.
- New: `<entity-or-feature>` (single word) or `<entity>-<short-desc>`.

## PR Template
File: `<veniss_app>/.github/pull_request_template.md`. Format: `{branch}: vX.Y.Z`.
Sections: Summary, Related Issues, Notes.

Fill like:
```
## Summary
<1–3 lines, what + why>

## Related Issues
- #<id> (or "none")

## Notes
- Files changed: <classified list>
- KPs queried: <IRIs or "none">
- Resource configs queried: <IRIs or "none">
- Predicates touched: <list or "none">
- Forms/UI affected: <list or "none">
- SPARQL queries run: see audit log path
- Deploy: server `git pull` + RS reload (no build)
- Verification: <what to check>
```

## Output
- Suggested branch
- `git add` + `git commit` commands (do not run)
- Filled PR body
- PR title `{branch}: vX.Y.Z`

## Rules
- Never auto-run git. Print only.
- Never include credentials.
