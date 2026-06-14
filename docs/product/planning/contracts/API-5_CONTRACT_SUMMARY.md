# API-5 Contract Summary

**Agent:** 2  
**Dependency ID:** API-5  
**Date:** 2026-06-07  
**Status recommendation:** `INTEGRATED` (Agent 4, 2026-06-07 — 55/55 tests; build OK)

---

## Endpoint

```
PATCH /api/v1/catalogs/{catalog_id}/items/reorder
```

## Request

```json
{
  "items": [
    { "id": "uuid", "sort_order": 0 },
    { "id": "uuid", "sort_order": 1 }
  ]
}
```

- `items` may be empty (no-op).
- Partial subsets are allowed (only listed items are updated).

## Response

```json
{ "updated": 42 }
```

`updated` is the number of items in the request (all persisted atomically).

## Validation rules (confirmed)

| Case | Status | `detail` |
|------|--------|----------|
| Catalog not found | `404` | `"Catalog not found"` |
| Duplicate `id` in request | `422` | `"Duplicate item ids in reorder request"` |
| Unknown or foreign item `id` | `422` | `"One or more item ids are not in this catalog"` |
| Empty `items` | `200` | `{ "updated": 0 }` |

## Atomicity

**All-or-nothing.** The server validates the full payload (catalog exists, no duplicate ids, all ids belong to the catalog) before applying any `sort_order` updates. A single database commit persists all changes; invalid requests leave existing order unchanged.

## `sort_order` policy

- Server persists values as sent.
- Gaps and duplicate `sort_order` values are allowed (no uniqueness enforcement).
- Cross-page DnD semantics remain a frontend UX limitation until API-4 + dedicated UX exist.

## Breaking changes

None — existing `PATCH /catalogs/{id}/items/{item_id}` remains for single-field edits.

## Tests

```bash
pytest tests/test_catalog_items_reorder_api.py
```

5 integration tests — 60-item reorder, catalog not found, foreign item id, duplicate ids, empty list.

## Agent 4 integration scope

- `apps/desktop/src/lib/api.ts` — add `reorderCatalogItems(catalogId, items)`
- `apps/desktop/src/lib/catalogLines.ts` — replace `applySortOrderUpdates()` sequential `patchCatalogItem` loop with single reorder call
- `apps/desktop/src/lib/catalogLines.test.ts` — update tests for bulk reorder
- `apps/desktop/src/pages/CatalogEditorPage.tsx` — wire `saveLineOrder()` to new API

## Catalog UI agent polish scope (post-INTEGRATED)

Save/discard order UX, toasts, loading state on "Guardar orden".
