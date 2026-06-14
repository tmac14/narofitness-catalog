# ProductDetail UX v2 — Contract Summary

**Track ID:** PROD-DETAIL-UX-V2  
**Date:** 2026-06-07  
**Phase:** Development — no production data; **no legacy compatibility**.

**Base track:** **PROD-DETAIL-UX-1** — **APPROVED / CLOSED** (prior hero/cards/gallery shell).

**Owner:** App UX agent (UI phases A/B/C/D/B2 UI); Agent 4 (Phase C0 types); Agent 2 (Phase B2 backend).

**Registry:** [TRANSVERSAL_BACKLOG.md](../TRANSVERSAL_BACKLOG.md)

---

## Status summary

| Phase | Scope | Status | Tests |
|-------|-------|--------|-------|
| **A** | Variants panel layout + detail aside | **IMPLEMENTED / QA_PENDING** | 227 |
| **B** | Unified `ProductMediaCard` local upload | **IMPLEMENTED / QA_PENDING** | 239 |
| **C0** | Price history types (`api.ts`) | **COMPLETE** | 248 |
| **C/D** | `PriceEvolutionCard` + master PVP summary | **IMPLEMENTED / QA_PENDING** | 259 |
| **B2 backend** | External URL image ingest | **IMPLEMENTED / INTEGRATION_TESTS_PENDING** | 19 unit |
| **B2 api.ts** | `createMaster/VariantImageFromUrl` | **COMPLETE** | 264 |
| **B2 UI** | Inline external URL panel | **IMPLEMENTED / QA_PENDING** | 268 |

**Current frontend baseline:** **268/268** passed; build OK.

**Block NOT closed:** Combined manual QA pending (dataset + media + price history).

---

## Phase A — Variants panel restructure

| Deliverable | Detail |
|-------------|--------|
| `ProductVariantsPanel` | Restructured table; detail **outside** row `colSpan` |
| Scroll | Removed local `max-h-[55vh]`; **horizontal scroll only** on wide table |
| `ProductVariantDetailPanel` | Aside **22/24rem**; separated cards |
| `VariantDetailHeader` | New |
| `VariantImageGallery` | Improved |
| `VariantPriceHistoryBlock` | Better hierarchy + empty states |

**Out of scope:** backend, `api.ts`, PDF, importer, jobs, schema.

---

## Phase B — Local media upload

| Deliverable | Detail |
|-------------|--------|
| `ProductMediaCard` | Unified master + variant |
| Interaction | Click preview/placeholder → file picker; **Enter/Space** → file picker |
| Dropzone | Drag-active state |
| Validation | MIME `image/*`; visible error `role="alert"` |
| Uploading | Overlay + `aria-busy` |
| Loaded | Overlay “Cambiar imagen” |
| Thumbs | Principal / delete preserved |
| Removed | Redundant primary CTA “Subir imagen” |

---

## Phase C0 — Price history contract (Agent 4 — COMPLETE)

### `VariantPriceHistoryItem`

| Field | Type |
|-------|------|
| `list_id` | string |
| `imported_at` | string |
| `effective_date` | string \| null |
| `price_amount` | string |
| `source_filename` | string \| null |
| `delta_pct_vs_previous` | number \| null |

### Helpers

- `getPriceHistoryPointDate()`
- `getPriceHistorySourceLabel()`

**Out of scope:** UI, backend changes in this phase.

---

## Phase C/D — Price evolution UI

| Deliverable | Detail |
|-------------|--------|
| `PriceEvolutionCard` | Auto-fetch on variant expand |
| Cache | Per `variantId` |
| States | `loading` \| `loaded` \| `error` |
| 0 points | Friendly empty |
| 1 point | “Primer precio registrado” — no chart |
| 2+ points | Monthly CSS chart + delta + collapsible milestone table |
| `buildMonthlyPriceSeries` | `effective_date` > `imported_at`; YYYY-MM grouping; last hit per month; parse `price_amount` |
| `ProductSummaryCard` | Textual PVP: none / single / min–max range |

**No external chart libraries.**

---

## Phase B2 — External URL images

### Backend — IMPLEMENTED / INTEGRATION_TESTS_PENDING

**Migration:** `007_product_image_source`

| Field | Values |
|-------|--------|
| `ProductImage.source_type` | `upload` \| `external_url` |
| `ProductImage.external_url` | Original URL metadata |

**Endpoints:**

```
POST /api/v1/product-masters/{id}/images/from-url
POST /api/v1/product-variants/{id}/images/from-url?set_primary=true
```

**Strategy (approved):**

- **Ingest-on-create** — download to local storage
- `external_url` preserved as metadata
- `file_path` remains **NOT NULL**
- `ProductImageOut.url` remains `/api/v1/media/...`
- SSRF guards; max **5MB**; `image/*`

**Unit tests:** 19 passed  
**Integration tests:** 19 **pending** — PostgreSQL unavailable at `localhost:5433`

**Before final closure:**

1. `alembic upgrade head`
2. `RUN_INTEGRATION=1` + PostgreSQL

**Contract:** [PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md](./PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md)

### api.ts — COMPLETE (Agent 4)

```typescript
ProductImage {
  source_type: "upload" | "external_url"
  external_url: string | null
}
```

**Helpers:**

- `createMasterImageFromUrl(masterId, url)`
- `createVariantImageFromUrl(variantId, url, { setPrimary? })`
- `isExternalProductImage(image)`

**Variant endpoint verified:** `/api/v1/product-variants/{variantId}/images/from-url`

### B2 UI — IMPLEMENTED / QA_PENDING

| Feature | Detail |
|---------|--------|
| Inline panel | “Usar URL externa” on `ProductMediaCard` |
| Validation | Client `http://` or `https://` |
| Actions | Master → `createMasterImageFromUrl`; variant → `createVariantImageFromUrl` |
| Success | Clear input, close panel, reload |
| Badge | “URL externa” |
| Link | “Ver origen” |
| Primary image | `apiBase + image.url` unchanged |

---

## Manual QA pending (not closed)

See [PRODUCT-DETAIL-UX-V2-QA.md](../tasks/PRODUCT-DETAIL-UX-V2-QA.md):

- **A** — Combined frontend (VARIANT-REP + v2 phases) — needs FDL masters in DB
- **B** — Media: upload, drag/drop, URL, errors, keyboard
- **C** — Price history: 0/1/2+ points, errors, multi-expand, master range
- **D** — PDF/preview visual (VARIANT-REP + PDF-TABLE-FIX-1)
- **E** — B2 integration tests with PostgreSQL

---

## Agent handoff

| Agent | Next |
|-------|------|
| App UX agent | Support QA; no new phases until QA sign-off |
| Agent 4 | B2 api.ts **COMPLETE** — idle unless contract change |
| Agent 2 | Run B2 integration tests when PostgreSQL available |
| Agent 6 | PDF visual QA only if ingest QA finds gap |
| User | Load QA dataset; execute checklists |

---

## Related documents

- [VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md](./VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md)
- [PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md](./PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md)
- [PRODUCT-DETAIL-UX-V2-QA.md](../tasks/PRODUCT-DETAIL-UX-V2-QA.md)
