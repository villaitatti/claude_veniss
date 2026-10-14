---
name: template-edit
description: Edit VeNiss HTML templates (RS semantic-form DSL) without breaking bindings.
---

# Template Edit

## Context
- Path: `apps/VeNiss/data/templates/*.html`.
- Format: URL-encoded HTML with RS `<semantic-form>`, `<semantic-form-text-input>`, `<semantic-form-autocomplete-input>`, `<bs-row>`, `<bs-col>`.
- Each `for-field` references a KP IRI in Blazegraph.

## Rules
- Preserve URL-encoding.
- Preserve field IRIs.
- Preserve `for-field` / `for-iri` / `template-id`.
- Keep `<bs-row>` / `<bs-col>` structure.
- Minimal diff. No reformatting.
- Verify unfamiliar components in `researchspace/src/main/web/components/` (if available).

## Before Edit
- Use `template-locator` to find template + linked KPs.
- For each `for-field` IRI: fetch KP via `knowledge-pattern` to confirm existence and shape.
- Identify the resource config that uses this template via `resource-config`.

## After Edit
- Diff: changed / preserved / bindings touched.
- For new field IRIs: verify KP exists in Blazegraph **before** committing.
- For removed field IRIs: confirm with user.
- Suggest local test: reload local RS, open form, submit a non-critical record.
