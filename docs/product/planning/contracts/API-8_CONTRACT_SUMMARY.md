# API-8 Contract Summary

**Agent:** 2  
**Dependency ID:** API-8  
**Date:** 2026-06-07  
**Status recommendation:** `INTEGRATED` (Agent 4, 2026-06-07 — 48/48 tests; build OK)

---

## Endpoint

```
POST /api/v1/catalogs/{catalog_id}/product-layouts/bulk
```

## Request

```json
{
  "layout_id": "string|null",
  "master_ids": ["uuid"]
}
```

- `layout_id: null` clears overrides for listed masters.

## Response

```json
{
  "applied": 0,
  "cleared": 0,
  "skipped": [
    { "master_id": "uuid", "reason": "human-readable string" }
  ]
}
```

`skipped` is **always present** (may be empty).

## Stable skip reasons (confirmed)

| Reason | When |
|--------|------|
| `"Product not in catalog"` | Master has no lines in catalogue |
| `"Layout single_standard is not compatible with variant products"` | Incompatible layout (from `LayoutConfigError`; exact wording may vary slightly) |

No `reason_code` field in v1 — UI should display `reason` text.

## Breaking changes

None.

## Tests

```bash
pytest tests/test_catalog_bulk_layouts_api.py
```

3 integration tests — not-in-catalog skip, incompatible layout skip, successful apply.

## Agent 4 integration scope

- `apps/desktop/src/lib/api.ts` — types already include `skipped[]`
- `apps/desktop/src/components/catalog-builder/CatalogPresentationBuilder.tsx` — surface `skipped[].master_id` + `reason` in bulk feedback

## Catalog UI agent polish scope (post-INTEGRATED)

Bulk skip reason display styling in presentation builder.
