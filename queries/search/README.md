# Keyword search queries

Read-only queries behind the runtime keyword search in `apps/VeNiss/data/templates/…ResourceSearchTemplate.html`.

- `<entity>_classscan.rq`: the runtime search, one per resource config. Each concatenates the subject's displayed fields into `?hay` and requires every typed word in it (case-insensitive substring). These mirror the per-config branches in the template; keep them in sync.
- `<entity>_current.rq`: the old mechanism (cron `search_term` or `rdfs:label`, plus `bds:search`), kept as a baseline.
- `__TOKEN__` is the token as RS builds it (`SparqlUtil.makeLuceneQuery`: "certosa 1564" → `certosa* 1564*`). In the template it is `?__token__`.
- The other files are diagnostics on `search_term` quality and coverage, the resource configs and their list columns.

Entities: `ps` Source_Primary, `ss` Source_Secondary, `person`, `group`, `event`, `island`, `bw` Builtwork.
