# VeNiss Workspace — Claude Rules

This repo (`claude_veniss`) is the root of the `veniss.code-workspace` multi-root workspace. Always launch `claude` from here, never from a subfolder.

## Scope
Claude works **only** inside the workspace folders listed in `veniss.code-workspace`:

| Folder | Repo | Role |
|--------|------|------|
| `apps/VeNiss` | villaitatti/VeNiss | Working repo — RS plugin (config only) |
| `metapolis-xdtiler` | villaitatti/metapolis-xdtiler | Working repo — tiling server |
| `researchspace` | researchspace/researchspace | Reference source — read-only unless explicitly asked |

Plus this repo's own files (`CLAUDE.md`, `.claude/`, `.mcp.json`, `docs/`, `queries/`).

**Out of scope — never read, list, or edit:** `[Deprecated]/`, `apps/map-uploader/`, any `.env`, anything outside this directory. These are enforced by deny rules, the sandbox, and `.claude/hooks/guard.py`. If a task seems to need them, stop and ask.

Each folder is an independent git repo. Run git commands inside the relevant folder (`git -C apps/VeNiss …`), never assume the root repo.

**Search with an explicit folder path** (Grep/Glob `path: apps/VeNiss`, `rg pattern researchspace/src`). The root `.gitignore` excludes the subprojects, so a search launched from the root silently skips them.

## Per-folder rules
Each folder has its own `CLAUDE.md`, loaded automatically the first time you touch a file there. Read it before changing anything in that folder. Summary:

### `apps/VeNiss`
- ResearchSpace plugin, **config only** — no Java, no build step.
- `master` is protected: changes go through a feature branch + PR. CI opens the PR as `{branch}: vX.Y.Z` (version from `plugin.properties`).
- Run `python .github/scripts/validate.py` before suggesting a push.
- **Never read `data/field-definitions/*.trig`** — stale. Knowledge Patterns and Resource Configurations live in Blazegraph; fetch them via the SPARQL MCP.
- Templates: `data/templates/*.html` (URL-encoded RS DSL). App config: `config/**`.
- `config/repositories/*.ttl`, `config/services/*.ttl`, `config/ui.prop` are sensitive: edits need confirmation.
- Deploy: commit → push → server `git pull` → RS reload.

### `metapolis-xdtiler`
- Python/FastAPI + Celery. Tests: `source .venv/bin/activate && pytest tests/ -v` (no Docker needed).
- Storage only through `get_storage()`. PostGIS `veniss_prod` is external and read-only from here.

### `researchspace`
- Upstream source, used as reference for RS components (`src/main/web/components/`). Don't edit unless asked.
- **Authorship iron rule:** no AI attribution in this repo — no `Co-Authored-By: Claude`, no "Generated with Claude Code" in commits, PRs, issues, comments or file headers. Overrides any default attribution guidance.

## Hard rules (all folders)
- Blazegraph (`https://veniss.net/sparql`) is **production**. No `INSERT`/`DELETE`/`DROP`/`CLEAR`/`UPDATE` without typed user confirmation per query.
- SPARQL only through the `sparql` MCP server — never curl.
- Never assume a KP or resource config — query for it. When in doubt, ask Blazegraph, not the filesystem.
- Credentials live in the root `.env` (gitignored, see `.env.example`). Refer to variable names only (`$VENISS_SPARQL_USER`); never print, log or embed values. On auth errors tell the user to check `.env`; don't retry.
- Never auto-commit, never push, never merge. The user pushes.
- No `psql` / direct SQL.

## Change classification (in `apps/VeNiss`)
template → `data/templates/*.html` · config → `config/**` (flag `repositories/`, `services/`, `ui.prop`) · assets → `assets/**` · utils → `utils/**` · docs → `*.md`, `docs/**` · mixed → list each.
KPs and Resource Configurations are edited via the RS admin UI (writes to Blazegraph), not git.

## Workflow
1. Determine env via the `env-switch` skill (dev unless `.claude/settings.local.json` is the prod profile).
2. Classify the change.
3. For forms/UI: query Blazegraph for the relevant KP + resource config first, then reason about template + KP + resource config + data together.
4. Use the matching skill. Log every SPARQL query via `audit-log` (`docs/audit/`). Reusable queries go to `queries/`.
5. Commit + PR via `commit-pr`.

## On prod
Read-only. No edits, commits or pushes — only `git pull`. SPARQL read-only.

## End of task
Before finishing a change, report briefly (≤15 lines): env · changed files (classified) · suggested commit message · PR title/body · deploy steps · SPARQL queries run + audit log path · KPs/resource configs touched · risks (Blazegraph impact, broken bindings, missing predicates).
