---
name: sparql-query
description: Run SPARQL via the MCP server safely, with versioning and logging.
---

# SPARQL Query

## How
- Use the MCP `sparql` server. Tools: `mcp__sparql__select`, `__ask`, `__construct`, `__describe`, `__update`.
- Never use curl. Never construct HTTP requests by hand.
- The server is defined in `.mcp.json` (workspace root). `server.py` reads endpoint and credentials from the root `.env`.

## Rules
- **Read-only by default.** Use `select` / `ask` / `construct` / `describe`.
- Always set `LIMIT` on exploration (default 100).
- `update` requires typed user confirmation per query, plus dry-run plan (count via SELECT first).
- Never include credentials anywhere.

## Workflow
1. State intent (one line).
2. Check `queries/` for an existing query. Reuse if possible.
3. Otherwise draft. If reusable → save to `queries/<name>.sparql`.
4. Call the appropriate MCP tool.
5. Log via `audit-log` before reporting.
6. Report: row count + ≤5 sample rows.

## Predicate Verification
```sparql
SELECT (COUNT(*) AS ?n) WHERE { ?s <PREDICATE> ?o } LIMIT 1
```
Zero → flag as missing or wrong namespace.

## Output
```
Intent: <...>
Tool: mcp__sparql__<select|ask|construct|describe|update>
Query: <path or inline>
Rows: <n>
Sample: <≤5>
Log: <audit log path>#<anchor>
```
