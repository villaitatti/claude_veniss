---
name: deploy-decision
description: Classify a VeNiss change and emit deploy steps.
---

# Deploy Decision

## Resolve paths first
Use `path-resolver` to get `veniss_app`. All classification is relative to it.

## Classify (within `veniss_app`)
- `data/templates/*.html` → **template**
- `config/**` → **config** (flag if `repositories/`, `services/`, `ui.prop`)
- `assets/**` → **assets**
- `utils/**` → **utils**
- `*.md`, `docs/**` → **docs**
- `data/field-definitions/*.trig` → **REJECT.** Stale; do not modify via git.

## Output
```
Type: <template | config | assets | utils | docs | mixed>
Files: <count + paths>
Steps:
  1. cd <veniss_app>
  2. git add <files>
  3. git commit -m "<message>"
  4. git push origin <branch>
  5. open PR ({branch}: vX.Y.Z)
  6. on merge: server `git pull` → RS reload
Verify: <pages/forms/queries to test post-deploy>
```

## Rules
- Never auto-execute. Print steps only.
- For `config/repositories/` or `config/services/` edits: warn endpoint/federation may break.
- If change touches a form: add to Verify "query KP + resource config from Blazegraph; confirm bindings still match".
