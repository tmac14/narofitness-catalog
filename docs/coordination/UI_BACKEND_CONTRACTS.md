# UI ↔ Backend Contracts

Canonical registry of API contracts between the desktop app and the backend. **Agent 4 integrates** after Agent 2 Contract Summary and `CONFIRMED`. **Agent 1A** polishes catalogue UI after `INTEGRATED`. **Agent 1B** may improve plain-language labels on affected app-wide pages (not `api.ts`).

**Last updated:** 2026-06-11 (Codex — source-catalog dual-path priority)

**Frontend agent split:** Catalogue contract polish → Agent 1A. App-wide page copy/UX around integrated endpoints → Agent 1B (coordinate shared files via Agent 3).

---

## Contract status legend

| Status | Meaning | Who acts |
|--------|---------|----------|
| `PROPOSED` | Agent 1A identified need; Agent 3 drafted shape | Agent 3 records API-X |
| `PENDING_VALIDATION` | Backend appears implemented; Agent 2 must validate | Agent 2 Plan → implement → Contract Summary |
| `CONFIRMED` | Agent 2 validated; formal Contract Summary received | Agent 4 may integrate (`READY_FOR_AGENT4`) |
| `INTEGRATED` | Agent 4 shipped contract wiring; tests pass | Agent 1A catalogue polish; Agent 1B app-wide label UX if applicable |
| `QA_READY` | Backend confirmed; no frontend integration required | User / Agent 1A manual QA |

**File lock during `CONFIRMED` → `INTEGRATED`:** Agent 4 owns `api.ts` and related types. Agent 1A and Agent 1B must not edit those files.

**Current `api.ts` lock:** **Released** — VARIANT-REP types + B2 image helpers **COMPLETE** (Agent 4).

**Coordination note:** ProductDetail / VARIANT-REP / B2 / PDF manual QA and IMPORT-FDL-FULL-QUALITY are **PAUSED / DEFERRED**. **Top priority:** [SOURCE_CATALOG_DUAL_PATH_PLAN.md](./SOURCE_CATALOG_DUAL_PATH_PLAN.md).

---

## Existing contracts (shipped — baseline)

These endpoints are in production use by the current builder UI. Agent 2 changes require backward compatibility or a new dependency ID.

| Surface | Method | Path | Client |
|---------|--------|------|--------|
| Catalog detail | GET | `/api/v1/catalogs/{id}` | `getCatalog()` |
| Catalog patch | PATCH | `/api/v1/catalogs/{id}` | `updateCatalog()` |
| Add/remove line | POST/DELETE | `/api/v1/catalogs/{id}/items[...]` | `addCatalogItem()`, `removeCatalogItem()` |
| Patch line | PATCH | `/api/v1/catalogs/{id}/items/{itemId}` | `patchCatalogItem()` |
| Bulk add | POST | `/api/v1/catalogs/{id}/items/bulk` | `bulkAddCatalogItems()` |
| Layout status | GET | `/api/v1/catalogs/{id}/layout-status` | `getCatalogLayoutStatus()` |
| Bulk layouts | POST | `/api/v1/catalogs/{id}/product-layouts/bulk` | `bulkProductLayouts()` |
| Preview HTML (fallback) | GET | `/api/v1/catalogs/{id}/preview/html` | `catalogPreviewHtmlUrl()` |
| Preview PDF | POST | `/api/v1/catalogs/{id}/preview/pdf?cache_bust=` | `fetchCatalogPreviewPdf()` |
| Export PDF | POST | `/api/v1/catalogs/{id}/export/pdf` | `exportCatalogPdf()` |
| Variant search | GET | `/api/v1/product-variants?q&...` | `searchVariants()` |
| Categories tree | GET | `/api/v1/categories` | `listCategories()` |

**Error shape (all JSON endpoints):** `{ "detail": string }` or FastAPI validation array; client parses via `parseApiError()`.

---

## API-EXPORT-PDF — Catalogue PDF export

| Field | Value |
|-------|-------|
| **Status** | **`PDF_LAYOUT_VISUALLY_ACCEPTED`** · **`PDF_EXPORT_INTEGRATED`** · **`EXPORT_QA_PENDING`** |
| **Owner** | **Agent 6** (rendering pipeline + PDF-table layout); Agent 4 (`api.ts` if contract changes) |
| **Contract Summary** | [PDF_EXPORT_CONTRACT_SUMMARY.md](./contracts/PDF_EXPORT_CONTRACT_SUMMARY.md) |

### Trigger (desktop)

- UI: **Exportar PDF** in `CatalogEditorHeader` and `PreviewWorkspace` → `handleExportPdf()` in `CatalogEditorPage`.
- Export **must not** reload the PDF preview viewer (`refreshPreview()` is not called during export).
- Client blocks export when `orderDirty` or `pendingPreview`; user must save in Productos / Presentación tabs first.
- General-tab edits are persisted via `updateCatalog()` before export when dirty (`skipPreviewRefresh: true`).

### Request

```
POST /api/v1/catalogs/{catalog_id}/export/pdf
Body: none
```

### Response (success)

| Field | Value |
|-------|-------|
| Status | `200` |
| Content-Type | `application/pdf` |
| Body | PDF bytes (magic `%PDF`) |
| Filename | Client: `sanitizePdfFilename(catalogName)` via `triggerPdfDownload()` |

### Response (errors)

| Status | `detail` |
|--------|----------|
| `404` | `Catalog not found` |
| `503` | WeasyPrint unavailable — client shows `Motor PDF no disponible. {detail}` |

### State source

Server DB via `build_catalog_context(catalog_id, for_html_preview=false)`. Preview viewer DOM is **not** used.

### Rendering

| Item | Value |
|------|-------|
| Abstraction | `PdfExportEngine` in `app/services/pdf_engines/` |
| Default engine | `playwright` (Chromium `page.pdf`) |
| Fallback | `weasyprint` |
| Future stubs | `princexml`, `docraptor` (Phase 2) |
| Selection | `PDF_EXPORT_ENGINE=auto\|playwright\|weasyprint` |
| Templates | `catalog_branded`, `catalog_default`, `catalog_supplier_table` |
| Layout shell | `family_variant_table` → `catalog_supplier_table.html` (`catalog_shell=supplier_table`) |
| Layout modes | `simple_product_block` (1 variant) · `family_variant_table` (2+ variants) — same visual system |
| Hierarchy | Category (red) → Brand → Product/family (grey) → detail rows |
| Brand grouping | `section.brand_groups[]` by commercial brand; missing → `"Sin marca"` |
| Columns | SKU · EAN (always dedicated) · P.V.P. (`supplier_price_column_label`, default `"P.V.P."`) · Descripción / Variante |
| Column widths | `<colgroup>` per product table — SKU/EAN equal width; description dominant in simple mode |
| Legacy layouts | `single_standard`, `variant_row_wide`, `variant_grid_50_50` unchanged when not uniform PDF-table |
| Page | A4, 15 mm margins |
| Images | URL mode (preview parity) or filesystem via `set_content` |
| Placeholders | `resolve_placeholder_url()` — no broken image icons |

### Preflight (client)

| Check | Behavior |
|-------|----------|
| `orderDirty` / `pendingPreview` | Block export; toast + navigate to tab |
| Info diagnostics (`no_image`, `no_category`) | Auto-export allowed |
| Warnings / fallbacks | `ExportPdfDialog` modal; export via **Exportar de todos modos** |
| Critical issues | Modal + explicit checkbox ack required |

### Health

```
GET /api/v1/health
  pdf_engine: "playwright" | "weasyprint" | null
  pdf_engine_fallback: string | null
  pdf_engines_available: string[]
  pdf_engine_error: string | null
```

`Layout` shows **Export PDF no disponible** when API is up but `pdf_engine` is null; badge **PDF: {engine}** when active.

### Tests

| Layer | File |
|-------|------|
| Frontend | `apps/desktop/src/lib/exportPdf.test.ts`, `catalogLayout.test.ts` |
| Backend | `test_catalog_export_route.py`, `test_pdf_export.py`, `test_pdf_engines.py`, `test_family_variant_table_layout.py` |

### Manual QA

Full pending checklist: [PDF-EXPORT-PREVIEW-MANUAL-QA.md](./tasks/PDF-EXPORT-PREVIEW-MANUAL-QA.md).

**Smoke (minimum):**

1. FDL catalogue with `uniform_layout_id=family_variant_table` → preview PDF-table layout
2. **Exportar PDF** → `%PDF` download; PDF preview viewer does not reload
3. Verify category headers, brand groups, EAN + P.V.P. columns, images/placeholders
4. Page 11 variant family + pages 3/4/5 simple products (regression fixtures)
5. Stress catalog — legacy layouts still work when presentation not PDF-table

### Agent 6 handoff

| Agent | Role |
|-------|------|
| Agent 6 | Owns export engine, templates, `catalog_builder` supplier context |
| Agent 1A | Optional export modal polish — not `api.ts` |
| Agent 4 | Idle unless export API shape changes |
| Agent 2 | Context/health gaps only |
| Agent 5 | Page audit data as QA fixtures — no export ownership |

---

## API-PREVIEW-PDF — Paginated catalogue preview (PREV-3)

| Field | Value |
|-------|-------|
| **Status** | **`IMPLEMENTED` / `QA_PASS`** |
| **Owner** | **Agent 6** (backend preview PDF + viewer); **Agent 4** (`fetchCatalogPreviewPdf`) |
| **Contract Summary** | [CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md](./contracts/CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md) |

### Request

```
POST /api/v1/catalogs/{catalog_id}/preview/pdf?cache_bust={optional}
Body: none
```

| Param | Notes |
|-------|-------|
| `cache_bust` | Optional query — regeneration / `previewKey` invalidation |

### Response (success)

| Field | Value |
|-------|-------|
| Status | `200` |
| Content-Type | `application/pdf` |
| Body | Raw PDF bytes |
| Header `X-Total-Pages` | Integer (PyMuPDF/fitz) |
| Header `X-Pdf-Engine` | e.g. `playwright`, `weasyprint` |
| Header `X-Preview-Generated-At` | ISO timestamp |

### Response (errors)

| Status | Expected |
|--------|----------|
| `404` | Catalog not found — `{ "detail": "..." }` |
| `503` | PDF engine unavailable — consistent with export |
| Render failure | Error response; no partial PDF |

### Side effects

| Effect | Detail |
|--------|--------|
| Preview file | Ephemeral cache under `data_dir/previews` |
| TTL | Files older than 24h cleaned |
| `CatalogExport` row | **None** |
| Jobs / ProcessRegistry | **None** |

### Frontend viewer (desktop)

| Rule | Contract |
|------|----------|
| Library | `pdfjs-dist` + worker |
| Components | `PaginatedPreviewWorkspace`, `PreviewPageNav`, `PdfPageCanvas` |
| Client helper | `fetchCatalogPreviewPdf(catalogId, previewKey)` |
| Display | **One real PDF page at a time** |
| Navigation | **Anterior**, **Siguiente**, **Página X de Y**, typed page number |
| Scroll | **No internal vertical scroll** inside page box |
| Regenerate | **Regenerar vista previa** via `previewKey`; resets to page 1 |
| Memory | Revoke blob URLs; destroy PDF documents on unmount/reload |
| HTML fallback | Opt-in only — **“Vista aproximada HTML”**; no fake page count |

### Stale / export interaction

| Event | Behavior |
|-------|----------|
| `refreshPreview` start | Does **not** clear stale |
| PDF `onLoad` success | Clears stale after successful readiness |
| PDF `onError` | **Preserves** stale |
| Export-after-preview | **Aborts** if preview regeneration fails |
| Export download | Still **`POST .../export/pdf`** — authoritative |

### Tests

| Layer | Count |
|-------|-------|
| Frontend + backend (post–3C) | **107/107** |

### Manual QA

Validated preview history: [TASK_HISTORY.md](./TASK_HISTORY.md).

**Parity (required):** `X-Total-Pages` = PDF.js total = exported PDF page count for one stress catalogue.

### Agent handoff

| Agent | Role |
|-------|------|
| Agent 6 | Phase 3 implementation **complete** |
| Agent 4 | `fetchCatalogPreviewPdf` **complete** |
| Agent 1A | Optional polish only if QA finds visual issues |
| Agent 2 | Not involved |

---

## VARIANT-REPRESENTATION-1 — Mixed-brand variant families

| Field | Value |
|-------|-------|
| **Status** | Backend **COMPLETE**; frontend **IMPLEMENTED / QA_PENDING**; PDF integrated — visual QA pending |
| **Contract** | [VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md](./contracts/VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md) |
| **Phase** | Development — current contract only; **no legacy** |

### API / model fields (shipped)

| Field | Values / notes |
|-------|----------------|
| `ProductVariant.brand_id` | Nullable FK |
| `brand_mode` | `none` \| `uniform` \| `mixed` |
| `brand_display` | `Varias marcas` when mixed |
| `variant_columns` | Dynamic table columns |
| `variant_label` | Row display name |

### Frontend consumers (Agent 1B)

`ProductsPage`, `ProductDetailPage`, `ProductVariantsPanel` — **QA_PENDING** (dataset).

### PDF consumers (Agent 6)

MARCA/VARIANTE columns integrated — **visual QA pending**.

---

## PROD-DETAIL-UX-V2 — Product detail enhancements

| Field | Value |
|-------|-------|
| **Contract** | [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./contracts/PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md) |
| **Status** | Phases A/B/C/D/B2 UI **IMPLEMENTED / QA_PENDING**; C0 + B2 api.ts **COMPLETE** |

### Price history (`VariantPriceHistoryItem` — COMPLETE)

| Field | Type |
|-------|------|
| `list_id` | string |
| `imported_at` | string |
| `effective_date` | string \| null |
| `price_amount` | string |
| `source_filename` | string \| null |
| `delta_pct_vs_previous` | number \| null |

Helpers: `getPriceHistoryPointDate()`, `getPriceHistorySourceLabel()`.

### External URL images (B2)

| Endpoint | Client helper |
|----------|---------------|
| `POST /api/v1/product-masters/{id}/images/from-url` | `createMasterImageFromUrl()` |
| `POST /api/v1/product-variants/{id}/images/from-url` | `createVariantImageFromUrl()` |

Full contract: [PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md](./contracts/PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md).

**Backend:** **INTEGRATION_TESTS_PENDING** (PostgreSQL).

---

## Dependency contracts

### API-1 — QA/stress catalogue seeder

| Field | Value |
|-------|-------|
| **Status** | Phase 1 **`PASS_WITH_WARNINGS`** (backend `CONFIRMED`; scale QA complete) |
| **Type** | Seeder / CLI (not HTTP) |

**Contract:**

```bash
npm run db:seed:stress          # create or update
npm run db:seed:stress:fresh    # delete stress data and recreate
```

**Output:** Catalogue named `QA Stress Catalog` (UUID printed to CLI). SKUs prefixed `STRESS-`. Master key prefix `STRESS-M`.

**Validated counts:** 350 masters; 946 catalogue lines; 24 categories; 72 layout overrides; contiguous `sort_order` `0..945`.

**Layout modes:** `single_standard`, `variant_grid_50_50`, `variant_row_wide`.

**Manual QA:** `npm run db:seed:stress:fresh` → **Catálogos → QA Stress Catalog**.

**Field stability:** Profile names and counts documented in [STRESS_CATALOG_SEED.md](../STRESS_CATALOG_SEED.md).

---

### API-3 — Product masters pagination

| Field | Value |
|-------|-------|
| **Status** | `INTEGRATED` |
| **Integrated by** | Agent 4 (2026-06-07) — tests 48/48; build OK |
| **Frontend** | [ProductsPage.tsx](../../apps/desktop/src/pages/ProductsPage.tsx), [api.ts `listMasters`](../../apps/desktop/src/lib/api.ts), [listMasters.test.ts](../../apps/desktop/src/lib/listMasters.test.ts) |

**Request:**

```
GET /api/v1/product-masters?q={optional}&page={int}&page_size={int}
```

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "brand": "string|null",
      "category_id": "uuid|null",
      "category_name": "string|null",
      "master_key": "string",
      "notes": "string|null",
      "variant_count": 0
    }
  ],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

**Constraints:** `page` ≥ 1; `page_size` 1–200 (default 50).

**Backward compatibility:** Omitting params returns first page, size 50.

**Integration notes:** `MastersListParams`, `MastersListResponse`; `listMasters({ q, page, page_size })`; Products page uses server-driven pagination.

**Manual QA:** stress seed → Products → multi-page pagination; search `STRESS-M`; change page size.

---

### API-4 — Builder table pagination

| Field | Value |
|-------|-------|
| **Status** | `PROPOSED` |
| **Frontend** | [CatalogEditorPage.tsx](../../apps/desktop/src/pages/CatalogEditorPage.tsx), [CatalogPresentationBuilder.tsx](../../apps/desktop/src/components/catalog-builder/CatalogPresentationBuilder.tsx) |

**Proposed request (catalog items):**

```
GET /api/v1/catalogs/{id}?items_page=1&items_page_size=50
```

**Proposed response extension:**

```json
{
  "id": "uuid",
  "name": "string",
  "items": [],
  "items_total": 0,
  "items_page": 1,
  "items_page_size": 50,
  "product_layouts": []
}
```

**Proposed request (layout-status products):**

```
GET /api/v1/catalogs/{id}/layout-status?products_page=1&products_page_size=50
```

**Proposed response extension:**

```json
{
  "summary": {},
  "diagnostics": [],
  "products": [],
  "products_total": 0,
  "products_page": 1,
  "products_page_size": 50
}
```

**Backward compatibility:** Omitting pagination params returns full arrays (current behavior).

---

### API-5 — Bulk catalog line reorder

| Field | Value |
|-------|-------|
| **Status** | `INTEGRATED` |
| **Integrated by** | Agent 4 (2026-06-07) — 55/55 tests; build OK |
| **Contract** | [API-5_CONTRACT_SUMMARY.md](./contracts/API-5_CONTRACT_SUMMARY.md) |
| **Frontend** | [api.ts](../../apps/desktop/src/lib/api.ts), [catalogLines.ts](../../apps/desktop/src/lib/catalogLines.ts), [CatalogEditorPage.tsx](../../apps/desktop/src/pages/CatalogEditorPage.tsx) |

**Request:**

```
PATCH /api/v1/catalogs/{id}/items/reorder
Content-Type: application/json

{
  "items": [
    { "id": "uuid", "sort_order": 0 }
  ]
}
```

**Response:**

```json
{ "updated": 42 }
```

**Errors:** `404` catalog not found; `422` validation (invalid ids, etc.)

**Backward compatibility:** Existing `PATCH .../items/{itemId}` remains for markup/price override only.

**Integration notes:**

- IDs are `catalog.items[].id` (catalogue line item IDs)
- Atomic all-or-nothing; no per-item errors; no N sequential PATCH fallback
- `reorderCatalogItems()`, `CatalogItemReorderEntry`, `CatalogItemsReorderResult`
- `applySortOrderUpdates()` → single bulk reorder; `filterSortOrderChanges()`, `mapReorderError()`

**Locks:** `api.ts`, `catalogLines.ts`, `CatalogEditorPage.tsx` — **released**.

---

### API-6 — Presentation master reorder

| Field | Value |
|-------|-------|
| **Status** | `PROPOSED` |
| **Frontend** | None yet — future Presentation tab DnD |

**Proposed request:**

```
PATCH /api/v1/catalogs/{id}/masters/reorder

{
  "items": [
    { "master_id": "uuid", "sort_order": 0 }
  ]
}
```

**Response:**

```json
{ "updated": 10 }
```

**Semantics (TBD by Agent 2):** Order affects preview/PDF master sequence within sections. Relationship to line-item `sort_order` to be documented.

---

### API-7 — Category tree reorder

| Field | Value |
|-------|-------|
| **Status** | `PROPOSED` |
| **Frontend** | None yet — future category/section ordering UI |

**Proposed request:**

```
PATCH /api/v1/categories/reorder

{
  "items": [
    { "id": "uuid", "sort_order": 0, "parent_id": "uuid|null" }
  ]
}
```

**Response:**

```json
{ "updated": 5 }
```

**GET /categories:** Siblings sorted by `sort_order` ascending, then `name`.

---

### API-8 — Bulk layout skipped reasons

| Field | Value |
|-------|-------|
| **Status** | `INTEGRATED` |
| **Integrated by** | Agent 4 (2026-06-07) — tests 48/48; build OK |
| **Frontend** | [CatalogPresentationBuilder.tsx](../../apps/desktop/src/components/catalog-builder/CatalogPresentationBuilder.tsx), [catalogLayout.ts](../../apps/desktop/src/lib/catalogLayout.ts), [api.ts `bulkProductLayouts`](../../apps/desktop/src/lib/api.ts), [catalogLayout.test.ts](../../apps/desktop/src/lib/catalogLayout.test.ts) |

**Request:**

```
POST /api/v1/catalogs/{id}/product-layouts/bulk

{
  "layout_id": "string|null",
  "master_ids": ["uuid"]
}
```

**Response:**

```json
{
  "applied": 3,
  "cleared": 0,
  "skipped": [
    { "master_id": "uuid", "reason": "Product not in catalog" }
  ]
}
```

**Known reasons (validate with Agent 2):**
- `"Product not in catalog"`
- Layout incompatibility messages from `LayoutConfigError` (free-text)

**Field stability:** `master_id` and `reason` required on each skipped entry; `skipped` always present.

**Integration notes:** `BulkLayoutSkipped`, `BulkLayoutResult`, `BulkLayoutFeedback`; `buildBulkLayoutFeedback()`; skip list UI in Presentation Builder with product name + reason.

**Manual QA:** stress seed → QA Stress Catalog → Presentation tab → bulk-apply `single_standard` → confirm skipped items visible.

**Risk:** skip reasons are free-text; tests use substring matching, not exact snapshots.

---

# Agent handoff notes

Per-dependency guidance split by role. **Agent 1A** = catalogue visual/UI. **Agent 1B** = app-wide plain-language UX (not `api.ts`). **Agent 4** = contract integration after `CONFIRMED`.

---

## API-1 — QA/stress seeder

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Status** | Phase 1 **`PASS_WITH_WARNINGS`** — complete (2026-06-07) |
| **Do NOT implement** | N/A — no frontend code required |
| **Validated** | Catalog `65096ef9-cb58-4026-b998-c557bf3bd007`; 350 masters, 946 lines; 0 blocking issues |
| **Deferred** | Phase PDF-1 manual sign-off — [PDF-EXPORT-PREVIEW-MANUAL-QA.md](./tasks/PDF-EXPORT-PREVIEW-MANUAL-QA.md) |

### Agent 4 (integration)

No frontend integration. Seeder-only dependency. Agent 4 does not act on API-1.

---

## API-3 — Product masters pagination

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Status** | `INTEGRATED` — Agent 4 complete |
| **No role on ProductsPage** | Agent 1A does not polish `ProductsPage` — see Agent 1B below |
| **Manual QA** | Stress seed → Products → pagination, search `STRESS-M`, page size |

### Agent 4 (integration — complete)

| Topic | Guidance |
|-------|----------|
| **Status** | **Complete** — no immediate action unless integration bugs found |
| **Files integrated** | `api.ts`, `ProductsPage.tsx`, `listMasters.test.ts` |
| **Verification** | 48/48 tests; build OK |

### Agent 1B (app-wide UX — post-INTEGRATED, optional)

| Topic | Guidance |
|-------|----------|
| **Next** | Post-integrated labels/accessibility review on `ProductsPage` |
| **Files** | `ProductsPage.tsx` (labels, empty/loading copy, pager accessibility) |
| **May improve** | Plain-language column headers, search hint text, pagination aria labels |
| **Do NOT** | Change `listMasters` calls or pagination logic (Agent 4) |
| **Blocking?** | No — not required before Agent 1A Phase 1 QA unless coordination decides otherwise |

---

## API-4 — Builder table pagination

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Can continue without it?** | Yes — catalogues under ~500 lines |
| **Do NOT touch** | `getCatalog`, `getCatalogLayoutStatus` in `api.ts` while API-4 in flight |
| **After INTEGRATED** | Polish pagination bars, loading UX in builder tables |

### Agent 4 (integration — after CONFIRMED)

| Topic | Guidance |
|-------|----------|
| **Files** | `api.ts`, `CatalogEditorPage.tsx`, `CatalogPresentationBuilder.tsx` |
| **Wire** | Pass page params; server-driven pagination; keep DnD page-scope limitation documented |
| **Do NOT** | Change visual design beyond functional wiring |

---

## API-5 — Bulk line reorder

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Status** | `INTEGRATED` — **manual DnD smoke required** |
| **Smoke** | QA Stress Catalog — DnD, bulk reorder request, save/discard, persisted order, `patchCatalogItem` blur |
| **Optional polish** | Toast/loading style on "Guardar orden"; save/discard UX |
| **Do NOT touch** | `api.ts`, `catalogLines.ts` reorder wiring (Agent 4) |

### Agent 4 (integration — complete)

| Topic | Guidance |
|-------|----------|
| **Status** | **Complete** — idle unless integration bugs found |
| **Files integrated** | `api.ts`, `catalogLines.ts`, `CatalogEditorPage.tsx`, `catalogLines.test.ts`, `reorderCatalogItems.test.ts` |
| **Verification** | 55/55 tests; build OK |

---

## API-6 — Presentation master reorder

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Can continue without it?** | Yes — Presentation tab works without DnD |
| **Do NOT implement** | Presentation tab DnD UI until API-6 `INTEGRATED` |
| **After INTEGRATED** | Sortable presentation table UX, drag handles, visual feedback (Agent 4 wires API first) |

### Agent 4 (integration — after CONFIRMED)

| Topic | Guidance |
|-------|----------|
| **Files** | `api.ts`, presentation reorder hooks, minimal wiring in `CatalogPresentationBuilder.tsx` |
| **Wire** | Master reorder API; persist order; reload layout-status |
| **Do NOT** | Build design-heavy DnD UI — Agent 1A owns visual layer after integration |

---

## API-7 — Category tree reorder

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Can continue without it?** | Yes — categories display in alphabetical tree order |
| **Do NOT implement** | Category DnD UI until API-7 `INTEGRATED` |
| **After INTEGRATED** | Category tree drag UX, section order visuals |

### Agent 4 (integration — after CONFIRMED)

| Topic | Guidance |
|-------|----------|
| **Files** | `api.ts`, category reorder hooks, minimal builder wiring |
| **Wire** | Category reorder API; update `listCategories` consumption if needed |
| **Do NOT** | Design-heavy category tree UI — Agent 1A polishes after |

---

## API-8 — Bulk layout skipped reasons

### Agent 1A (catalogue visual / QA)

| Topic | Guidance |
|-------|----------|
| **Status** | `INTEGRATED` — functional skip list wired |
| **Next** | Polish skip-reason list layout, typography, severity styling if needed |
| **Manual QA** | Presentation tab bulk-apply `single_standard`; confirm product name + reason for skipped items |
| **Catalogue-only** | Agent 1A scope — not app-wide |

### Agent 4 (integration — complete)

| Topic | Guidance |
|-------|----------|
| **Status** | **Complete** — no immediate action unless integration bugs found |
| **Files integrated** | `api.ts`, `catalogLayout.ts`, `CatalogPresentationBuilder.tsx`, `catalogLayout.test.ts` |
| **Verification** | 48/48 tests; build OK |

---

## Safe continuation summary

### Agent 1A (catalogue)

May continue catalogue visual UI/UX on small/medium catalogues without waiting on Agent 2:

- PreviewWorkspace, export modal, presentation tab, catalogue tables, catalogue tests
- Do **not** touch `apps/api/**`, `api.ts`, or app-wide pages (Agent 1B)
- Do **not** integrate contracts — Agent 4 owns that
- After `INTEGRATED`, polish catalogue surfaces (step 11)

### Agent 1B (app-wide)

May run **discovery only** until user approves plan ([APP_WIDE_UX_SCOPE.md](./APP_WIDE_UX_SCOPE.md)):

- Map routes, usability/a11y risks, shared-file needs
- Do **not** implement before user approval
- Do **not** touch catalogue builder, `api.ts`, or backend
- After Agent 4 `INTEGRATED`, may improve labels/UX on affected list pages (e.g. `ProductsPage`) — not contract wiring
- Request shared-file lock via Agent 3 before editing `Layout.tsx`, `components/ui/**`, etc.

### Agent 4

**Current status:** API-3, API-8, **API-5** **INTEGRATED** (2026-06-07). All integration locks **released**. **Idle** unless integration bugs reported.

May act when a new contract reaches `CONFIRMED` / `READY_FOR_AGENT4` (next candidate: **API-4** after coordination reprioritizes).

Must not invent contracts or implement design-heavy UI.

---

## Related documents

- [API_DEPENDENCY_BACKLOG.md](./API_DEPENDENCY_BACKLOG.md)
- [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)
- [TASK_HISTORY.md](./TASK_HISTORY.md)
- [APP_WIDE_UX_SCOPE.md](./APP_WIDE_UX_SCOPE.md)
- [MANUAL_QA_BUILDER_UI.md](../MANUAL_QA_BUILDER_UI.md)
