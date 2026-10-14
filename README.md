# claude_veniss

Shared Claude Code configuration for the VeNiss team workspace.

The repo sits in its own folder inside the workspace. `setup.sh` symlinks its config into the workspace root, which is where Claude Code looks for it. Every teammate runs Claude with the same rules, skills and guardrails.

```
<workspace>/                     ← workspace root: launch `claude` here (any name, any location)
├── claude_veniss/               ← this repo
│   ├── CLAUDE.md                workspace rules for Claude
│   ├── .mcp.json                no MCP servers configured
│   ├── .claude/
│   │   ├── settings.json        shared permissions, sandbox, hooks (dev profile)
│   │   ├── settings.prod.json   prod profile
│   │   ├── hooks/guard.py       PreToolUse guard: keeps Claude inside the workspace folders
│   │   ├── skills/              sparql-query, template-edit, commit-pr, …
│   │   └── agents/              config-auditor, rs-reference, template-locator
│   ├── docs/                    team notes; docs/audit/ holds local SPARQL logs (gitignored)
│   ├── queries/                 reusable SPARQL queries
│   ├── scripts/sparql.py        SPARQL client for Blazegraph (reads .env)
│   ├── veniss.code-workspace    editor workspace and Claude's scope
│   └── setup.sh                 creates the root symlinks and .env
├── CLAUDE.md  -> claude_veniss/CLAUDE.md
├── .claude    -> claude_veniss/.claude
├── .mcp.json  -> claude_veniss/.mcp.json
├── .env                         your credentials (local only)
├── apps/VeNiss/                 ← villaitatti/VeNiss
├── metapolis-xdtiler/           ← villaitatti/metapolis-xdtiler
└── researchspace/               ← researchspace/researchspace
```

## Setup

Requirements: [Claude Code](https://docs.claude.com/en/docs/claude-code), `python3` (hook and `scripts/sparql.py`).

```sh
mkdir <workspace> && cd <workspace>
git clone git@github.com:villaitatti/claude_veniss.git
git clone git@github.com:villaitatti/VeNiss.git apps/VeNiss
git clone git@github.com:villaitatti/metapolis-xdtiler.git
git clone git@github.com:researchspace/researchspace.git
./claude_veniss/setup.sh      # symlinks + .env from .env.example
```

Fill in `<workspace>/.env` (ask a teammate for the values), then run `claude` from `<workspace>`.

The folder paths in `veniss.code-workspace` are relative. Keep the layout above, or update the paths in that file.

`setup.sh` is safe to re-run. It skips anything that already exists as a real file.

## Using it

- **Editor:** open `claude_veniss/veniss.code-workspace` in VS Code or VSCodium. The `claude_veniss` folder is where you view and edit the config.
- **Starting Claude:** use the task **Terminal → Run Task… → Claude Code (workspace root)**, or run `cd <workspace> && claude` in any terminal. Always start it from the root, never from a subfolder.
- **Checking what's active:** `/memory` (CLAUDE.md files), `/permissions`, `/hooks` and `/sandbox`.

## How confinement works

Claude may only work in the folders listed in `veniss.code-workspace`. Three layers enforce this:

1. **`permissions.deny`** in `.claude/settings.json` keeps Claude's file tools away from `.env` files and stale `.trig` field definitions. It also denies `git push`, `rm -rf` and `psql`.
2. **Sandbox** (macOS Seatbelt or Linux bubblewrap) limits what Bash commands can read and write.
3. **`.claude/hooks/guard.py`** blocks any file-tool path outside the workspace folders. It also blocks risky Bash patterns, such as `git -C x push` or curl to the SPARQL endpoint.

**To add a folder to Claude's scope**, add it to `veniss.code-workspace` and commit, so the whole team gets it.

Each folder's own `CLAUDE.md` holds its rules. Claude Code loads it the first time it touches a file in that folder. The root `CLAUDE.md` only carries cross-cutting rules and the few folder rules that must apply before that happens.

## Personal overrides

Put personal tweaks in `.claude/settings.local.json`. It is gitignored, and its arrays merge with the shared settings. Typical uses:

- extra local folders at the root that Claude must not read, under `permissions.deny` and `sandbox.filesystem.denyRead`
- a stricter `"defaultMode": "default"`
- sandbox paths your tooling needs, such as a package cache in `sandbox.filesystem.allowWrite`

Changes that help everyone belong in `settings.json`, through a PR.

## Production server

```sh
cp claude_veniss/.claude/settings.prod.json claude_veniss/.claude/settings.local.json
```

This makes Claude read-only: no edits, commits or SPARQL updates. `env-switch` detects the prod profile from this file.

## Contributing

- Skills go in `.claude/skills/<name>/SKILL.md`, and agents in `.claude/agents/<name>.md`.
- Reusable SPARQL goes in `queries/`.
- Keep `CLAUDE.md` short. Folder-specific rules belong in that folder's own `CLAUDE.md`, in its own repo.
- Never commit `.env`, `settings.local.json` or `docs/audit/` logs.
