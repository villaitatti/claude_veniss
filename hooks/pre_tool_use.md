# Pre-Tool-Use Hook

## Block / Stop
- `git push` → STOP. User runs manually.
- `rm -rf`, `git reset --hard`, `git clean -fd` → STOP.
- `mcp__sparql__update` (or any SPARQL `INSERT`/`DELETE`/`DROP`/`CLEAR`/`UPDATE`) → STOP, typed confirmation per query.
- Any `psql` / SQL command → STOP. Out of scope.
- Any `curl` against the SPARQL endpoint → STOP. Use the MCP server.
- Any read of `data/field-definitions/*.trig` → STOP. Use SPARQL via MCP instead.
- Edits to `config/repositories/*.ttl`, `config/services/*.ttl` → STOP, confirm.
- Any command that includes a credential value literally → STOP, replace with `$VAR` reference.

## Remind (one line)
- Editing template? → preserve `<semantic-form>` field IRIs + URL-encoding.
- Need a KP? → query Blazegraph LDP container via MCP, not git.
- Need a resource config? → query container IRI via MCP, not git.
- Running SPARQL? → log via `audit-log`.
- Path question? → resolve via `paths.json`, never hardcode.
- On `prod` env? → read-only, no commits.

## Output
One-line classification: `[<env>] <change-type>: <action>`
