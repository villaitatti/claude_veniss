# Subagent: template-locator

## Purpose
Find templates / app config relevant to a UI element, form, or behavior.

## Search Scope (filesystem, paths via `path-resolver`)
- `<veniss_app>/data/templates/*.html`
- `<veniss_app>/config/page-layout/*`
- `<veniss_app>/config/ui.prop`

## Search Scope (Blazegraph — via MCP)
- KPs in `<.../fieldDefinitionContainer>`
- Resource configs in `<.../resource_configurations_container/...>`

## Method
1. Filesystem: match by visible text, component name, `for-field` IRI, config key.
2. Extract referenced KP IRIs.
3. Optionally query Blazegraph via MCP to confirm KPs and resource configs.
4. Return paths + matched lines + linked Blazegraph IRIs.

## Output
```
Template matches:
  - <path>:<line> — <reason>
Linked KP IRIs (Blazegraph):
  - <IRI> [verified | not yet queried]
Linked resource configs:
  - <IRI> [verified | not yet queried]
Linked app config:
  - <paths>
Notes: <bindings / IRIs to inspect>
```

## Rules
- Never read `.trig`.
- Never edit anything.
