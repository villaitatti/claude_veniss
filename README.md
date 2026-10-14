# claude_veniss

Claude Code configuration for the VeNiss workspace (`veniss.code-workspace`). This repo **is** the workspace root; the workspace folders are independent repos cloned inside it and ignored here.

```
veniss/                      ← this repo
├── CLAUDE.md                workspace rules + per-folder summaries
├── .mcp.json                SPARQL MCP server (Blazegraph)
├── .claude/
│   ├── settings.json        permissions, sandbox, hooks (dev profile)
│   ├── settings.prod.json   prod profile (copy to settings.local.json on the server)
│   ├── hooks/guard.py       PreToolUse guard: keeps Claude inside the workspace folders
│   ├── mcp-sparql/          MCP server source
│   ├── skills/              sparql-query, template-edit, commit-pr, …
│   └── agents/              config-auditor, rs-reference, template-locator
├── docs/                    RS notes; docs/audit/ = local SPARQL logs (gitignored)
├── queries/                 reusable SPARQL queries
├── veniss.code-workspace
├── apps/VeNiss/             ← villaitatti/VeNiss        (ignored)
├── metapolis-xdtiler/       ← villaitatti/metapolis-xdtiler (ignored)
└── researchspace/           ← researchspace/researchspace   (ignored)
```

## Setup on a new machine

```sh
git clone git@github.com:villaitatti/claude_veniss.git veniss
cd veniss
git clone git@github.com:villaitatti/VeNiss.git apps/VeNiss
git clone git@github.com:villaitatti/metapolis-xdtiler.git
git clone git@github.com:researchspace/researchspace.git
cp .env.example .env          # fill in SPARQL credentials
claude                        # always launch from this directory
```

Requirements: Claude Code, `python3` (hook), `uv` (MCP server).

On the production server, additionally:

```sh
cp .claude/settings.prod.json .claude/settings.local.json
```

## How confinement works

Claude may only work in the folders listed in `veniss.code-workspace` plus this repo's own files. Three layers enforce it:

1. **`permissions.deny`** in `.claude/settings.json`: Claude's file tools can't read or edit `[Deprecated]/`, `apps/map-uploader/`, `.env` files or stale `.trig` field definitions. `git push`, `rm -rf` and `psql` are denied.
2. **Sandbox** (macOS Seatbelt / Linux bubblewrap): Bash can't read `~/projects` (except this workspace), `~/Documents`, `~/Desktop` or `~/Downloads`, nor the excluded paths above.
3. **`.claude/hooks/guard.py`**: blocks file-tool paths outside the folders listed in `veniss.code-workspace`, and blocks risky Bash patterns (e.g. `git -C x push`, curl to the SPARQL endpoint).

To add a folder to Claude's scope, add it to `veniss.code-workspace` and to `.gitignore` here.

Per-folder rules live in each folder's own `CLAUDE.md`, which Claude Code loads the first time it touches a file there. The root `CLAUDE.md` summarises them.
