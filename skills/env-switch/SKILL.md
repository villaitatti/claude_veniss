---
name: env-switch
description: Read .claude/env.md and apply environment-specific rules.
---

# Env Switch

## On Session Start
1. Read `.claude/env.md`.
2. Read `.claude/paths.json` (via `path-resolver`).
3. Announce: `env: <dev|prod>` + resolved paths.

## dev
- Edits, commits, branch ops allowed (with `ask` mode).
- SPARQL writes via MCP require typed confirmation per query.
- Traffic still hits production Blazegraph.

## prod
- Read-only on filesystem.
- Only `git pull` for git ops.
- SPARQL read-only via MCP, no exceptions.
- If user requests a fix → propose, suggest doing on dev, ask before deviation.

## Switching
- Edit `.claude/env.md`, restart session. Never auto-switch.
