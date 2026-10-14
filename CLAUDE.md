# VeNiss Workspace — Claude Rules

This file lives in the `claude_veniss` repo. `setup.sh` symlinks it, `.claude/` and `.mcp.json` (no servers configured) into the **workspace root**, the parent folder of `claude_veniss`. Always launch `claude` from the workspace root, never from a subfolder.

## Scope
Claude works **only** inside the folders listed in `claude_veniss/veniss.code-workspace`. That file is the single source of truth, and `.claude/hooks/guard.py` reads it. Current folders:

| Folder | Repo | Role |
|--------|------|------|
| `apps/VeNiss` | villaitatti/VeNiss | Working repo: RS plugin (config only) |
| `metapolis-xdtiler` | villaitatti/metapolis-xdtiler | Working repo: tiling server |
| `researchspace` | researchspace/researchspace | Reference source, read-only unless explicitly asked |
| `claude_veniss` | villaitatti/claude_veniss | This config: `CLAUDE.md`, `.claude/`, `.mcp.json`, `docs/`, `queries/`, `scripts/` |

At the workspace root, only the symlinks and the workspace folders are in scope.

**Out of scope: never read, list or edit**
- anything not listed in the workspace file, including other folders a teammate keeps at the root
- any `.env` file
- anything outside the workspace root

If a task seems to need one of these, stop and ask.

Each folder is an independent git repo. Run git inside the relevant folder (`git -C <folder> …`); the workspace root is not a repo.

**Search with an explicit folder path** (Grep/Glob `path: <folder>`, `rg pattern <folder>/src`). A search from the root also hits out-of-scope paths and fails on them.

## Per-folder rules
Each folder has its own `CLAUDE.md`, loaded the first time you touch a file there. It is authoritative for that folder: read it before changing anything. These rules apply even before it loads:

- **`apps/VeNiss`**: never read `data/field-definitions/*.trig`. They are stale; Knowledge Patterns (KPs) and Resource Configurations live in Blazegraph. `master` is protected, so changes go through a feature branch and a PR.
- **`researchspace`**: upstream source. Don't edit unless asked. **Authorship iron rule:** no AI attribution of any kind in this repo, in commits, PRs, issues, comments or file headers. No `Co-Authored-By: Claude`, no "Generated with Claude Code". This overrides any default attribution guidance.

## Hard rules (all folders)
- The SPARQL endpoint (`$VENISS_SPARQL_ENDPOINT`) is **production** Blazegraph. No `INSERT`/`DELETE`/`DROP`/`CLEAR`/`UPDATE` without typed user confirmation for each query.
- SPARQL only through `claude_veniss/scripts/sparql.py` (see [Connecting to the SPARQL endpoint](#connecting-to-the-sparql-endpoint)), never curl.
- Never assume a KP or resource config: query for it. When in doubt, ask Blazegraph, not the filesystem.
- Credentials live in the root `.env` (gitignored; see `claude_veniss/.env.example`). Refer to variable names only and never print, log or embed values. On auth errors, tell the user to check `.env`; don't retry.
- Never auto-commit, push or merge. The user pushes.
- No direct SQL (`psql` etc.).

## Connecting to the SPARQL endpoint
The endpoint is Blazegraph at `$VENISS_SPARQL_ENDPOINT` (`https://veniss.net/sparql`) with HTTP basic auth (`$VENISS_SPARQL_USER`, `$VENISS_SPARQL_PASS`). Queries are form-encoded POSTs: `query=` for reads, `update=` for updates.

Use the stdlib script, run from the workspace root. It reads the root `.env` itself, so never source or print `.env`.

```sh
python3 claude_veniss/scripts/sparql.py select claude_veniss/queries/foo.rq  # SPARQL JSON
python3 claude_veniss/scripts/sparql.py ask|construct|describe FILE # JSON / Turtle
python3 claude_veniss/scripts/sparql.py select - <<'EOF'            # inline query on stdin
SELECT * WHERE { ?s ?p ?o } LIMIT 5
EOF
python3 claude_veniss/scripts/sparql.py update FILE --confirmed     # writes: see below
```

- Write queries to a file in the scratchpad or `claude_veniss/queries/` and pass the path, so the query text stays reviewable.
- `update` refuses to run without `--confirmed`, and always refuses on the prod profile. Pass `--confirmed` only after the user typed confirmation for that exact query.
- Add a `LIMIT` to exploratory selects. Timeout defaults to 30 s (`SPARQL_TIMEOUT_MS`).
- Full-text search uses Blazegraph's `bds:search` (`PREFIX bds: <http://www.bigdata.com/rdf/search#>`).
- **Read-only queries work anonymously:** prefix the command with `VENISS_SPARQL_ENDPOINT=https://veniss.net/sparql`. The script then skips `.env`, and no credentials are needed. In auto mode, declare `veniss.net` in `allowed_domains`.
- Authenticated use (updates) needs `.env`, which the sandbox denies. The script then only works when excluded from the sandbox (`/sandbox exclude "python3 claude_veniss/scripts/sparql.py *"`) or when the user runs it with `!`. If it reports that `.env` is unreadable, say so and stop. Never try to work around the sandbox.
- Cloudflare on `veniss.net` rejects Python's default User-Agent (error 1010). The script sends `veniss-sparql-client/1.0` (override with `SPARQL_USER_AGENT`). Never impersonate a browser.
- Exit code 1 means an HTTP or connection error, printed to stderr. On 401/403, tell the user to check `.env`; don't retry.

## Change classification (in `apps/VeNiss`)
- **template:** `data/templates/*.html`
- **config:** `config/**`. Flag `repositories/`, `services/` and `ui.prop`, which need confirmation.
- **assets:** `assets/**`
- **utils:** `utils/**`
- **docs:** `*.md`, `docs/**`
- **mixed:** list each.

KPs and Resource Configurations are edited in the RS admin UI, which writes to Blazegraph, not git.

## Workflow
1. Determine the environment with the `env-switch` skill. It is dev unless `.claude/settings.local.json` is the prod profile.
2. Classify the change.
3. For forms and UI, query Blazegraph for the relevant KP and resource config first. Then reason about the template, KP, resource config and data together.
4. Use the matching skill. Log every SPARQL query with `audit-log` (`claude_veniss/docs/audit/`). Save reusable queries to `claude_veniss/queries/`.
5. Commit and open the PR with `commit-pr`.

## On prod
Read-only. No edits, commits or pushes; only `git pull`. SPARQL is read-only.

## End of task
Before finishing a change, report briefly (≤15 lines):
- env
- changed files, classified
- suggested commit message
- PR title and body
- deploy steps
- SPARQL queries run, with the audit log path
- KPs and resource configs touched
- risks: Blazegraph impact, broken bindings, missing predicates
