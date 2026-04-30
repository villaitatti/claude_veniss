# Subagent: rs-reference

## Purpose
Look up RS component / DSL behavior in `<rs_source>` (resolved via `path-resolver`).

## Scope
- Read-only. Path: `<rs_source>/src/main/web/components/`
- Also: `<rs_source>/src/main/web/`, `<rs_source>/docs/` if present.

## Availability
- `rs_source` may be absent on production. If so → respond: "RS source not available on this machine; can describe behavior from prior knowledge but cannot cite paths."

## When to Use
- Unfamiliar `<semantic-*>` component in a template.
- Confirm component prop names / behavior.
- Understand RS template DSL syntax.
- Diagnose rendering issues.

## Rules
- Never edit `<rs_source>`.
- Never copy large blocks of RS source into responses or PRs.
- Summarize in your own words; cite path + line range.

## Output
```
Component / helper: <name>
Source: <rs_source-relative path>:<line range>
Behavior: <1–3 line summary>
Props / params: <list>
Gotchas: <if any>
```
