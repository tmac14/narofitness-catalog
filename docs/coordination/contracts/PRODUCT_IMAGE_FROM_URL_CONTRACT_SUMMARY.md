# PRODUCT-IMAGE-FROM-URL — External URL Image Ingest (B2)

**Track ID:** PROD-DETAIL-UX-V2-B2  
**Date:** 2026-06-07  
**Agent:** 2 (backend) · 4 (`api.ts`) · 1B (UI)  
**Phase:** Development — **no legacy compatibility**.

**Parent:** [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md)

---

## Status summary

| Layer | Status |
|-------|--------|
| Backend | **IMPLEMENTED / INTEGRATION_TESTS_PENDING** |
| `api.ts` | **COMPLETE** |
| UI | **IMPLEMENTED / QA_PENDING** |

---

## Schema (migration 007)

| Column | Type | Notes |
|--------|------|-------|
| `ProductImage.source_type` | enum | `upload` \| `external_url` |
| `ProductImage.external_url` | string \| null | Original URL metadata |

`file_path` remains **NOT NULL** — ingest downloads to local storage on create.

---

## HTTP contract

### Master image from URL

```
POST /api/v1/product-masters/{master_id}/images/from-url
Content-Type: application/json

{ "url": "https://..." }
```

### Variant image from URL

```
POST /api/v1/product-variants/{variant_id}/images/from-url?set_primary=true
Content-Type: application/json

{ "url": "https://..." }
```

### Success

| Field | Value |
|-------|-------|
| Status | `200` or `201` (per implementation) |
| Body | `ProductImageOut` |

### `ProductImageOut` (response)

| Field | Type |
|-------|------|
| `url` | `/api/v1/media/...` — always local served path |
| `source_type` | `"upload"` \| `"external_url"` |
| `external_url` | string \| null — original when `external_url` |

### Errors

| Case | Expected |
|------|----------|
| Invalid URL / SSRF blocked | `4xx` with `{ "detail": "..." }` |
| Not an image / too large | `4xx` — max **5MB**, `image/*` |
| Download failure | `4xx`/`5xx` with detail |

---

## Ingest strategy (approved)

1. Client sends external URL.
2. Server validates URL (SSRF guards).
3. Server downloads image → local storage.
4. `file_path` populated; `external_url` stores original.
5. API consumers use `ProductImageOut.url` (`/api/v1/media/...`) for display.

**PDF / preview:** With local ingest, Agent 6 needs **no changes** unless QA proves otherwise.

---

## Frontend contract (`api.ts` — COMPLETE)

```typescript
interface ProductImage {
  source_type: "upload" | "external_url"
  external_url: string | null
  // ...existing fields
}

createMasterImageFromUrl(masterId: string, url: string): Promise<ProductImage>
createVariantImageFromUrl(variantId: string, url: string, options?: { setPrimary?: boolean }): Promise<ProductImage>
isExternalProductImage(image: ProductImage): boolean
```

**Verified path:** `/api/v1/product-variants/{variantId}/images/from-url`

---

## UI contract (IMPLEMENTED / QA_PENDING)

| Rule | Detail |
|------|--------|
| Entry | Inline “Usar URL externa” on `ProductMediaCard` |
| Client validation | `http://` or `https://` only |
| Success UX | Clear input, close panel, reload images |
| Badge | “URL externa” when `source_type === "external_url"` |
| Link | “Ver origen” → `external_url` |
| Primary display | `apiBase + image.url` |

---

## Verification

| Layer | Result |
|-------|--------|
| Unit tests (backend) | **19 passed** |
| Integration tests | **19 pending** — PostgreSQL not available `localhost:5433` |
| Frontend tests | **264** (api.ts) → **268** (with UI) |

### Required before closure

```bash
alembic upgrade head
RUN_INTEGRATION=1 npm run test:api:integration   # or project equivalent
```

PostgreSQL must be running and reachable.

---

## Out of scope

- PDF templates
- `catalog_builder` / preview pipeline changes
- Importer / page 15
- Jobs / ProcessRegistry
- Legacy upload path removal beyond current contract

---

## Related documents

- [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md)
- [UI_BACKEND_CONTRACTS.md](../UI_BACKEND_CONTRACTS.md)
- [PRODUCT-DETAIL-UX-V2-QA.md](../tasks/PRODUCT-DETAIL-UX-V2-QA.md)
