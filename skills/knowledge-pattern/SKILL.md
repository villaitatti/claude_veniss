---
name: knowledge-pattern
description: Fetch RS Knowledge Patterns from Blazegraph via MCP/LDP container.
---

# Knowledge Pattern (Field Definition)

## Source of Truth
- KPs are in Blazegraph, not in `.trig` files.
- LDP container: `<.../fieldDefinitionContainer>`. Local dev example: `<http://localhost:10214/container/fieldDefinitionContainer>`. Production: confirm with user if different.

## List all KPs
```sparql
PREFIX ldp:      <http://www.w3.org/ns/ldp#>
PREFIX Platform: <http://www.metaphacts.com/ontologies/platform#>

SELECT ?kp WHERE {
  ?container a Platform:fieldDefinitionContainer ;
             ldp:contains ?kp .
}
```

## Fetch one KP by name
```sparql
PREFIX ldp:      <http://www.w3.org/ns/ldp#>
PREFIX Platform: <http://www.metaphacts.com/ontologies/platform#>

CONSTRUCT { ?kp ?p ?o }
WHERE {
  ?container a Platform:fieldDefinitionContainer ;
             ldp:contains ?kp .
  FILTER(STRENDS(STR(?kp), "/"))
  ?kp ?p ?o .
}
```

## Inspect KP structure
```sparql
SELECT ?p ?o WHERE { <KP_IRI> ?p ?o . }
```

## Rules
- **Never read `data/field-definitions/*.trig`.** Not authoritative.
- KPs are edited through the RS admin UI. Do not instruct user to edit `.trig`.
- All KP queries → use `mcp__sparql__select` or `__construct` and log via `audit-log`.

## Output
```
KP: <IRI>
Container: <container IRI>
Properties: <insertPattern, selectPattern, label, domain, range, ...>
Used by templates: <grep result from veniss_app/data/templates/>
Log: <audit log path>#<anchor>
```
