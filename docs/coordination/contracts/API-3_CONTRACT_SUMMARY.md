# API-3 Contract Summary

**Agent:** 2  
**Dependency ID:** API-3  
**Date:** 2026-06-07  
**Status recommendation:** `INTEGRATED` (Agent 4, 2026-06-07 — 48/48 tests; build OK)

---

## Endpoint

```
GET /api/v1/product-masters?q={optional}&page={int}&page_size={int}
```

## Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "brand": "string|null",
      "category_id": "uuid|null",
      "category_name": "string|null",
      "master_key": "string|null",
      "notes": "string|null",
      "variant_count": 0
    }
  ],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

## Validation rules (confirmed)

| Param | Rule |
|-------|------|
| `page` | Default 1, min 1 |
| `page_size` | Default 50, min 1, max 200 |
| `q` | Case-insensitive filter on `name` and `master_key` |
| `total` | Full filtered count, not `len(items)` |

## Breaking changes

None — omitting `page`/`page_size` returns first page (50 items).

## Tests

```bash
pytest tests/test_product_masters_pagination.py
```

5 integration tests — pagination defaults, page 2, search filter, max page_size, rejection over max.

## Agent 4 integration scope

- `apps/desktop/src/lib/api.ts` — `listMasters()` pass `page`, `page_size`, `q`
- `apps/desktop/src/pages/ProductsPage.tsx` — server-driven pagination

## Known frontend gap

Products page currently loads full list client-side; Agent 4 wires pagination after `CONFIRMED`.
