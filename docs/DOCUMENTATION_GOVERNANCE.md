# Documentation governance

## Scope

This repo documents the NaroCatalog PIM product. Command reference lives at repo root:

- `COMMANDS.md`
- `scripts/commands.catalog.json`

Validate sync: `npm run help:validate` · `npm run help:coverage`.

## Lifecycle

| Label | Meaning |
|-------|---------|
| ACTIVE | Current product documentation |
| CORE | Stable reference spec |
| ARCHIVED | Historical; do not extend |

## English canonical policy

Active technical docs use English. Archived Spanish originals live under `docs/archive/product/es/`.

## Adding or changing npm scripts

1. Add script to root `package.json`.
2. Document in `COMMANDS.md` and `scripts/commands.catalog.json`.
3. Run `npm run help:validate`.

## Link audit

`python scripts/audit_docs_links.py --check` scans active docs for broken relative links.
