---
name: blazegraph-debug
description: Debug VeNiss UI/data issues across SPARQL, KP, resource config, and template layers.
---

# Blazegraph Debug

## Layers (check in order)
1. **Data** — does SPARQL return expected triples?
2. **Knowledge Pattern** — fetch from Blazegraph (NOT `.trig`); does insert/select pattern match?
3. **Resource Configuration** — does it wire the right KPs to the right form?
4. **App Config** — `ui.prop`, `repositories/`, `services/`?
5. **Template** — does the form reference correct KP IRIs and components?

## Rules
- Each hypothesis verified against Blazegraph or a config file.
- All queries via MCP, read-only.
- Never read `.trig`.
- Reproduce the failing page first; capture URL/IRI.
- Distinguish: missing data vs wrong KP vs wrong resource config vs broken template binding vs RS component bug.
- Unfamiliar RS component → check `<rs_source>/src/main/web/components/` if available.

## Output
```
Symptom: <what user sees>
Layer: <data | KP | resource-config | app-config | template>
Evidence: <query result / KP property / config line / template line>
Fix: <minimal change + which layer>
Edit path: <git-tracked file | RS admin UI (Blazegraph)>
Deploy impact: <template | config | none-via-git (UI edit)>
Log: <audit log path>
```
