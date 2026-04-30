---
name: path-resolver
description: Resolve subproject paths from .claude/paths.json. Never hardcode paths in other skills.
---

# Path Resolver

## Why
Workspace layout differs between dev and prod. Skills must resolve paths through this layer.

## Method
1. Read `.claude/paths.json`.
2. Treat values as relative to workspace root unless absolute.
3. For each requested key, check that the path exists on disk:
   - Exists → return resolved absolute path.
   - Missing + `_optional` lists it as optional → return null, log warning.
   - Missing + not optional → return error; instruct user to update `paths.json`.

## Keys
- `veniss_app` — required
- `rs_source` — optional (read-only RS reference)
- `query_vault` — required (created at workspace root by default)
- `audit_log_dir` — required
- `rs_notes_dir` — required

## Rules
- Never hardcode `apps/VeNiss` or `researchspace` in any other skill — always go through this resolver.
- If `paths.json` is missing → halt, instruct user to copy from the generated default.
- If a required path is absent → report clearly, do not guess.

## Output
```
veniss_app: <abs path>
rs_source: <abs path | absent>
query_vault: <abs path>
audit_log_dir: <abs path>
rs_notes_dir: <abs path>
```
