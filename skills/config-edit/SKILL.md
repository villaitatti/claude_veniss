---
name: config-edit
description: Edit RS app config files with awareness of cross-cutting impact.
---

# Config Edit

## Files (sensitivity high → low; relative to `veniss_app`)
1. `config/repositories/*.ttl` — endpoint definitions. Highest risk.
2. `config/services/*.ttl` — service wiring.
3. `config/ui.prop` — preferredLabel / thumbnail SPARQL CONSTRUCTs.
4. `config/environment.prop` — sessions, auth filter, CORS.
5. `config/proxy.prop` — Mapbox token, proxies.
6. `config/page-layout/*` — header, footer, login, main.
7. `config/namespaces.prop` — prefix definitions.

## Rules
- (1)(2): explicit confirmation. Print diff first.
- Credentials: use existing `${default.username}` placeholder pattern. Never inline.
- `ui.prop` SPARQL: validate via MCP before commit.
- `namespaces.prop`: removing a prefix can silently break templates. Grep before removing.
- Never edit `.env`. Direct user.

## Output
- Diff preview
- Downstream consumers (templates, KPs, queries) affected
- Verification queries (read-only via MCP)
- Confirmation prompt for sensitive files
