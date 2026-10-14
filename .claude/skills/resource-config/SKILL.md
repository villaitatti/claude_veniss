---
name: resource-config
description: Fetch RS Resource Configurations from Blazegraph via MCP.
---

# Resource Configuration

## Source of Truth
- Container: `<http://www.researchspace.org/resource/system/resource_configurations_container/...>`
- Example: Primary Sources → `<.../resource_configurations_container/data/Source_Primary>`

## List
```sparql
PREFIX ldp: <http://www.w3.org/ns/ldp#>

SELECT ?config WHERE {
  <http://www.researchspace.org/resource/system/resource_configurations_container/> ldp:contains ?config .
}
```
(Confirm container IRI with user if structure differs.)

## Fetch one
```sparql
CONSTRUCT { <CONFIG_IRI> ?p ?o . ?o ?p2 ?o2 . }
WHERE {
  <CONFIG_IRI> ?p ?o .
  OPTIONAL { ?o ?p2 ?o2 . }
}
```

## Rules
- Edited via RS UI, not git.
- No SPARQL `update` against these unless user confirms per query.
- All queries → MCP + `audit-log`.

## Output
```
Config: <IRI>
Type: <e.g. Source_Primary>
Properties: <key fields>
Linked KPs: <IRIs>
Linked templates: <if any>
Log: <audit log path>#<anchor>
```
