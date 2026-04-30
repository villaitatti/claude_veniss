# VeNiss / ResearchSpace — Workspace Rules

## Read First (in order)
1. `.claude/env.md` — current env (dev | prod)
2. `.claude/paths.json` — subproject locations on this machine
3. This file — global rules
4. Skill-specific files load on demand

## Workspace
- Root may differ between dev and prod. **Never hardcode paths in skills.** Resolve via `paths.json`.
- In scope: `paths.veniss_app` (working repo), `paths.rs_source` (read-only reference, may be absent).
- Out of scope: every other sibling directory at the root.

## Project Reality
- VeNiss is a **ResearchSpace plugin (config-only)**. No Java in the working repo.
- Branch model: `master` + feature branches. No `build` branch.
- Single data store: **Blazegraph** at `https://veniss.net/sparql` (production, basic auth).
- **SPARQL only**, accessed via the **MCP server** configured in `.claude/mcp.json`. Never use curl.
- `default.ttl` points directly at production. No dev/staging endpoint exists.

## Source of Truth
- **Knowledge Patterns** (field definitions): Blazegraph, LDP container `<.../fieldDefinitionContainer>`. Fetch via SPARQL. **Never read `data/field-definitions/*.trig`** — stale.
- **Resource Configurations**: Blazegraph, container `<.../resource_configurations_container/...>`. Fetch via SPARQL.
- **Templates**: filesystem at `paths.veniss_app/data/templates/*.html` (URL-encoded RS DSL).
- **App config**: filesystem at `paths.veniss_app/config/**`.

When in doubt: ask Blazegraph, not the filesystem.

## Hard Rules
- Blazegraph is **production**. No `INSERT`/`DELETE`/`DROP`/`CLEAR`/`UPDATE` without typed user confirmation per query.
- Never read `.trig` field-definition files.
- Never assume a KP or resource config — query for it.
- Never embed credentials in skills, prompts, logs, queries, or PR bodies.
- Treat `config/repositories/*.ttl`, `config/services/*.ttl`, `config/ui.prop` as sensitive: edits require confirmation.
- Never auto-commit, auto-push, or auto-merge.

## Credentials
- Live in `.env` (workspace root, gitignored). See `.env.example` for variable names.
- Claude references env vars by name (`$VENISS_SPARQL_USER`, `$VENISS_SPARQL_PASS`, `$VENISS_SPARQL_ENDPOINT`), never values.
- The MCP server reads credentials from its `env` block in `mcp.json`, which expands `${...}` from `.env`.
- If a query fails with auth error → tell user to check `.env`, do not retry.

## Change Classification (in `paths.veniss_app`)
- **template** → `data/templates/*.html`
- **config** → `config/**` (flag if `repositories/`, `services/`, `ui.prop`)
- **assets** → `assets/**`
- **utils** → `utils/**`
- **docs** → `*.md`, `docs/**`
- **mixed** → list each

KPs and Resource Configurations are edited via the **RS admin UI** (writes to Blazegraph), not git.

Deploy for git-tracked changes: commit → push → server `git pull` → RS reload. **No build step.**

## Workflow
1. Read `env.md` and `paths.json`. Announce env + resolved paths.
2. Classify the change.
3. For anything touching forms/UI: query Blazegraph for the relevant KP + resource config first. Reason about template + KP + resource config + data together.
4. Use the matching skill. Log every SPARQL query via `audit-log`.
5. Commit + PR via `commit-pr`.

## On `prod` env
- Read-first. No edits unless user explicitly says "edit on prod".
- No commits, no pushes. Only `git pull`.
- SPARQL: read-only via MCP, no exceptions.

## References (resolved via paths.json)
- Query vault: `paths.query_vault`
- RS source: `paths.rs_source` (may be null/absent on this machine)
- Session logs: `paths.audit_log_dir` (local only, gitignored)
- RS notes: `paths.rs_notes_dir`
