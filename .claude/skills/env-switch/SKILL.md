---
name: env-switch
description: Detect dev vs prod profile from .claude/settings.local.json and apply environment-specific rules.
---

# Env Switch

## Detect
- `prod` if `.claude/settings.local.json` exists and is a copy of `.claude/settings.prod.json` (it denies `Edit`/`Write`).
- Otherwise `dev`.
- Announce: `env: <dev|prod>`.

## dev
- Edits, commits, branch ops allowed (commits and PRs ask first).
- SPARQL writes via MCP require typed confirmation per query.
- Traffic still hits production Blazegraph.

## prod
- Read-only on filesystem.
- Only `git pull` for git ops.
- SPARQL read-only via MCP, no exceptions.
- If user requests a fix → propose, suggest doing on dev, ask before deviation.

## Switching
- prod: `cp .claude/settings.prod.json .claude/settings.local.json`, restart session.
- dev: `rm .claude/settings.local.json`, restart session.
- User does this manually. Never auto-switch.
