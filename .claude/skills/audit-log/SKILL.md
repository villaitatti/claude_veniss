---
name: audit-log
description: Append every SPARQL query to a session audit log.
---

# Audit Log

## When
- Every MCP SPARQL call (read or write).
- Every KP / resource config fetch.
- Every hypothesis check during debugging.

## Where
`claude_veniss/docs/audit/YYYY-MM-DD/<task-name>.md` — one folder per day, one file per task.
Multiple concurrent tasks get separate `.md` files under the same day folder.

## Entry Format
```
### <HH:MM> — <intent>
- env: <dev|prod>
- endpoint: $VENISS_SPARQL_ENDPOINT (referenced by name only)
- mcp tool: <mcp__sparql__select | __ask | __construct | __describe | __update>
- type: read | write
- query path: <claude_veniss/queries/... or "inline">
- query:
` ` `sparql
    <query — credentials NEVER inline>
` ` `
- result: <row count / summary / error>
- notes: <interpretation, follow-ups>
```

## Rules
- Append-only.
- Reusable queries → save to `claude_veniss/queries/` and reference path.
- **Never** log credentials, full result dumps, or PII.
- Reference env vars by name only.
- Log **before** reporting results to user.

## Session End
- Append `## Summary`: queries by tool, KPs/resource configs touched, key findings, files changed.
- Reference log path in PR body Notes.
