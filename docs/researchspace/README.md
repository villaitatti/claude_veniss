# ResearchSpace Reference (workspace-local notes)

Notes on RS internals as they relate to VeNiss. Authoritative source: `<rs_source>` (resolved via `paths.json`).

## Quick Pointers (when `rs_source` is available)
- Components: `<rs_source>/src/main/web/components/`
- Semantic-form DSL: `components/forms/`
- LDP / containers: search RS source for `LdpContainer` / `fieldDefinitionContainer`

## Add Files Here As You Learn
- `forms.md` — `<semantic-form>` `for-field` IRI ↔ KP mapping
- `templates.md` — URL-encoding quirks, allowed components, helpers
- `knowledge-patterns.md` — KP shape + LDP queries
- `resource-configs.md` — resource configuration container, examples
- `endpoints.md` — Blazegraph access notes (no creds)

## Rule
Treat as VeNiss's local ground truth for "how RS behaves here". Update as you learn.
