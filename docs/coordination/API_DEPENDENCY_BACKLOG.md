# API Dependency Backlog

Master backlog for backend/API work required by the Professional Builder UI/UX upgrade.

- **Agent 2** owns backend implementation and validation (Plan Mode → Agent mode → Contract Summary).
- **Agent 4** owns frontend integration after `CONFIRMED` (via ChatGPT Agent 4 prompt → Cursor Agent 4).
- **Agent 1A** owns catalogue visual polish after `INTEGRATED` (step 11).
- **Agent 1B** owns app-wide plain-language UX on affected pages (not `api.ts`).
- **Agent 3** maintains this registry.

**Last updated:** 2026-06-11 (Codex — source-catalog dual-path priority)

**Status legend:** `OPEN` | `Pending Agent 2 validation` | `CONFIRMED` | `READY_FOR_AGENT4` | `INTEGRATED` | `QA_READY` | `PASS_WITH_WARNINGS` | `DONE`

**Workflow:** See [CODEX_TASK_EXECUTION_PROTOCOL.md](./CODEX_TASK_EXECUTION_PROTOCOL.md).

---

## Summary table

| ID | Title | Backend owner | Integration owner | Priority | Status | Blocks manual QA? |
|----|-------|---------------|-------------------|----------|--------|-------------------|
| API-1 | Official QA/stress catalogue seeder | Agent 2 | — (seeder only) | P0 | **Phase 1 PASS_WITH_WARNINGS** | No — scale QA gate passed |
| API-3 | Server-side pagination (product masters list) | Agent 2 | Agent 4 | P2 | **INTEGRATED** | Partial — Products page manual QA |
| API-4 | Server-side pagination (builder tables) | Agent 2 | Agent 4 | P2 | OPEN | Partial — builder scale |
| API-5 | Bulk reorder (catalog line items) | Agent 2 | Agent 4 | P1 | **INTEGRATED** | No — Agent 1A DnD smoke pending |
| API-6 | Presentation master reorder | Agent 2 | Agent 4 → Agent 1A visual | P3 | OPEN | No |
| API-7 | Category tree reorder | Agent 2 | Agent 4 → Agent 1A visual | P3 | OPEN | No |
| API-8 | Bulk layout skipped reasons | Agent 2 | Agent 4 → Agent 1A visual | P1 | **INTEGRATED** | Partial — bulk feedback manual QA |

**Note:** API-2 is intentionally unused (stable ID gap). Do not renumber IDs.

**Backend appears implemented (Agent 2 must validate):** API-4.

**Agent 2 validated (2026-06-07):** API-1 `CONFIRMED` → `QA_READY`; API-3, API-5, API-8 `CONFIRMED`. See `docs/coordination/contracts/API-*_CONTRACT_SUMMARY.md`.

**Agent 4 integrated (2026-06-07):** API-3, API-8 (48/48 tests); **API-5** (55/55 tests) — build OK. API-5 locks **released**. Agent 2 has **no immediate follow-up** for API-3/API-5/API-8 unless smoke finds contract bugs.

**Phase 1 manual QA (2026-06-07):** `PASS_WITH_WARNINGS` — catalog `65096ef9-cb58-4026-b998-c557bf3bd007`. Remaining catalogue-builder QA is recoverable through [CATALOGUE-BUILDER-OPEN-QA.md](./tasks/CATALOGUE-BUILDER-OPEN-QA.md).

**Next work:** Agent 1A **API-5 DnD smoke** on QA Stress Catalog; optional polish; then decide **API-4** vs catalogue performance/polish.

**Import/parser (separate track):** [IMPORT_PARSER_BACKLOG.md](./IMPORT_PARSER_BACKLOG.md) — **PR-FDL-FAMILY-BLOCK** `BACKEND_VALIDATED` / `QA_VISUAL_READY` (2026-06-08).

**Theme v2 (complete):** SHARED-3 **RELEASED** — `THEME_V2_COMPLETE` (70/70 tests).

**Status Bar:** SHARED-4 **RELEASED** — `IMPLEMENTED` / `VISUAL_QA_PENDING` — [APP_WIDE_UX_SCOPE.md § Status Bar](./APP_WIDE_UX_SCOPE.md). Jobs baseline: [APP_JOBS_CONTRACT.md](./contracts/APP_JOBS_CONTRACT.md) **IMPLEMENTED**.

**Presentation Phase 1:** `show_description_column` **`INTEGRATED` / `QA_READY`** — [CATALOG_PRESENTATION_BACKLOG.md](./CATALOG_PRESENTATION_BACKLOG.md).

**Paginated PDF preview (PREV-3 / PRES-4):** **`IMPLEMENTED` / `QA_PASS`** — Phases 3A–3D complete; manual QA passed 2026-06-07 — [CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md](./contracts/CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md).

**Future jobs extension:** generic source/adaptation subjects — [BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md](./contracts/BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md).

**PDF export / print renderer (separate track):** **PDF-EXPORT** — Agent 6 — **`PDF_LAYOUT_VISUALLY_ACCEPTED`** · **`PDF_EXPORT_INTEGRATED`** · **`EXPORT_QA_PENDING`**. **PDF-TABLE-FIX-1** open. Contract: [PDF_EXPORT_CONTRACT_SUMMARY.md](./contracts/PDF_EXPORT_CONTRACT_SUMMARY.md).

**Transversal (separate track):** [TRANSVERSAL_BACKLOG.md](./TRANSVERSAL_BACKLOG.md) · [CODEX_ORCHESTRATION_STATE.md](./CODEX_ORCHESTRATION_STATE.md).

**TOP PRIORITY:** [SOURCE-CATALOG-DUAL-PATH-1](./SOURCE_CATALOG_DUAL_PATH_PLAN.md) — **`ACTIVE`**. Import baseline remains paused: 358 masters, 544 variants, **292 blocked**.

**PAUSED:** VARIANT-REP frontend QA, PROD-DETAIL-UX-V2 QA, B2 integration tests, PDF QA — resume after import gate.

**VARIANT-REPRESENTATION-1:** Backend **COMPLETE**; frontend QA **PAUSED / DEFERRED**.

**PROD-DETAIL-UX-V2-B2:** api.ts **COMPLETE**; backend integration + UI QA **PAUSED / DEFERRED**.

---

## VARIANT-REPRESENTATION-1 — Mixed-brand variant families

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 (backend); Agent 1B (frontend); Agent 6 (PDF) |
| **Priority** | P1 — transversal |
| **Contract** | [VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md](./contracts/VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md) |
| **Development phase** | No legacy compatibility |

### Status by layer

| Layer | Status |
|-------|--------|
| Backend (1) | **COMPLETE** |
| Cleanup (1B/1C) | **COMPLETE** |
| Frontend UI | **IMPLEMENTED / QA_PENDING** |
| PDF / preview | **Integrated** — visual QA pending |
| Manual QA | **Pending** — dataset incomplete |

### Implemented contract (backend)

| Field | Contract |
|-------|----------|
| `ProductVariant.brand_id` | Nullable FK |
| `brand_mode` | `none` \| `uniform` \| `mixed` |
| `brand_display` | `Varias marcas` when mixed |
| `variant_columns` | Dynamic column config |
| `variant_label` | Per-row visible name |
| Master brand | **No last-row-wins** |

**Audits:** pages 11/12/13/14 — **PASS**

### Frontend (Agent 1B — QA_PENDING)

- `ProductsPage` + `ProductDetailPage` use `brand_display`
- `ProductVariantsPanel` dynamic columns
- Column order finalized; table-layout fixed for overlap fix
- Tests **218** → **223+**; build OK

### QA dataset required

`CRO-SACO-GUSANO`, `BOC-BARRAS-CROSSFIT`, `BOC-BARRAS-CROSSFIT-NEXO`, `DOBHT` (separate load if DB purged per page).

**Registry:** [TRANSVERSAL_BACKLOG.md](./TRANSVERSAL_BACKLOG.md)

---

## PROD-DETAIL-UX-V2-B2 — External URL image ingest

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 (backend); Agent 4 (`api.ts`); Agent 1B (UI) |
| **Contract** | [PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md](./contracts/PRODUCT_IMAGE_FROM_URL_CONTRACT_SUMMARY.md) |
| **Parent** | [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./contracts/PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md) |

| Layer | Status |
|-------|--------|
| Migration `007_product_image_source` | Shipped |
| `POST .../images/from-url` (master + variant) | **IMPLEMENTED / INTEGRATION_TESTS_PENDING** |
| `api.ts` helpers | **COMPLETE** |
| UI inline URL panel | **IMPLEMENTED / QA_PENDING** |

**Before closure:** `alembic upgrade head` + PostgreSQL + `RUN_INTEGRATION=1` (19 integration tests).

---

## API-1 — Official QA/stress catalogue seeder

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 |
| **Priority** | P0 |
| **Status** | **Phase 1 `PASS_WITH_WARNINGS`** (backend `CONFIRMED`; Phase 1 scale QA complete) |
| **Backend appears implemented** | Yes — `apps/api/app/services/seed_stress_catalog.py`, `docs/STRESS_CATALOG_SEED.md` |
| **Blocks manual QA** | Unblocks scale QA — [MANUAL_QA_BUILDER_UI.md](../MANUAL_QA_BUILDER_UI.md) sections B, C, G; [MANUAL_QA_PRESENTATION_BUILDER.md](../MANUAL_QA_PRESENTATION_BUILDER.md) stress scenarios |
| **Blocks future features** | No |

### Required backend/API contract

- CLI/npm: `npm run db:seed:stress`, `npm run db:seed:stress:fresh`
- Creates catalogue **QA Stress Catalog** with ~350 masters (configurable `--masters`), ~400 variants
- SKU prefix `STRESS-`, master key prefix `STRESS-M`
- 15+ categories/subcategories
- Product profiles: `single_standard`, `variant_grid_50_50`, `variant_row_wide`, `no_image`, `no_category`, `incomplete_variants`, incompatible layout overrides
- Idempotent update or documented `--fresh` reset

### Required frontend integration (Agent 4)

None — seeder-only. User runs `npm run db:seed:stress:fresh`; desktop opens catalogue by name/ID. Agent 4 does not act on API-1.

### Validated stress seed data (API-1)

| Field | Value |
|-------|-------|
| Masters | 350 |
| Catalogue lines | 946 |
| Categories | 24 |
| Layout overrides | 72 |
| Layout modes | `single_standard`, `variant_grid_50_50`, `variant_row_wide` |
| `sort_order` | Contiguous `0..945` |
| Manual QA target | **Catálogos → QA Stress Catalog** |
| Manual QA command | `npm run db:seed:stress:fresh` |

### Acceptance criteria

- [x] One command produces catalogue with ~300–400 product lines
- [x] Profiles cover all layout modes and diagnostic edge cases per [STRESS_CATALOG_SEED.md](../STRESS_CATALOG_SEED.md)
- [x] `npm run db:seed:stress:fresh` is documented and safe (does not wipe full DB)
- [x] Integration tests pass: `apps/api/tests/test_stress_seed_integration.py`, `test_seed_stress_catalog.py`
- [x] Agent 2 publishes Contract Summary; Agent 3 sets `CONFIRMED` / user QA (no Agent 4 step)

Contract: [API-1_CONTRACT_SUMMARY.md](./contracts/API-1_CONTRACT_SUMMARY.md)

### Implementation notes for Agent 2

- Review `apps/api/app/services/seed_stress_catalog.py` and `apps/api/scripts/seed_stress_catalog.py`
- Confirm category distribution uses `seed_categories.py` / default taxonomy
- Verify layout override count (5 incompatible `single_standard` on multi-attribute products)
- Confirm catalogue line `sort_order` is populated for DnD/pagination QA

### Risks

- Seeder may exist but profiles incomplete vs QA checklist expectations
- Docker/API must be running; prerequisites in STRESS_CATALOG_SEED.md must be current

### Open questions

- None blocking — Agent 2 confirms counts and profile coverage during validation

---

## API-3 — Server-side pagination (product masters list)

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 |
| **Priority** | P2 |
| **Status** | **INTEGRATED** |
| **Backend appears implemented** | Yes — `GET /api/v1/product-masters` in `apps/api/app/routers/masters.py` |
| **Frontend integrated by** | Agent 4 (2026-06-07) |
| **Blocks manual QA** | Partial — Products page server pagination manual QA remains |
| **Blocks future features** | Yes — [ProductsPage](../../apps/desktop/src/pages/ProductsPage.tsx) scale |

### Required backend/API contract

```
GET /api/v1/product-masters?q={string}&page={int}&page_size={int}
→ {
  "items": ProductMasterOut[],
  "total": int,
  "page": int,
  "page_size": int
}
```

- `page` default 1, min 1
- `page_size` default 50, min 1, max 200
- `ProductMasterOut`: `{ id, name, brand, category_id, category_name, master_key, notes, variant_count }`
- **Canonical path is `/product-masters`** (not `/masters`)

### Frontend integration record (Agent 4 — complete)

| Item | Detail |
|------|--------|
| **Tests** | `npm test` 48/48; `npm run build` OK |
| **Files** | `api.ts`, `ProductsPage.tsx`, `listMasters.test.ts` |
| **Types** | `MastersListParams`, `MastersListResponse` |
| **Wiring** | `listMasters({ q, page, page_size })`; server-driven pagination on Products page |

**Agent 1B (post-INTEGRATED, optional):** labels, a11y, plain-language copy on `ProductsPage` — not data wiring.

**Agent 1A:** no role on `ProductsPage`.

**Manual QA:** stress seed → Products → multi-page pagination; search `STRESS-M`; change page size.

### Acceptance criteria

- [x] Agent 2 confirms existing pagination matches contract above
- [x] `total` reflects full filtered count, not page length
- [x] Backend tests cover pagination bounds and `q` filter
- [x] Contract marked `CONFIRMED`; Agent 4 integrates; no silent 50-item cap
- [x] Frontend integration complete; `api.ts` lock released

Contract: [API-3_CONTRACT_SUMMARY.md](./contracts/API-3_CONTRACT_SUMMARY.md)

### Implementation notes for Agent 2

- **No immediate follow-up** — integration complete. Future work only if integration bugs reported.

### Risks

- API-4 builder pagination remains client-side (catalogue scale)
- ProductsPage labels/accessibility polish belongs to Agent 1B
- Contract drift with legacy doc referencing `GET /masters`

### Open questions

- Should `page`/`page_size` be required in future API versions? (Assume optional for now.)

---

## API-4 — Server-side pagination (builder tables)

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 |
| **Priority** | P2 |
| **Status** | OPEN |
| **Backend appears implemented** | No |
| **Blocks manual QA** | Partial — builder pagination/DnD at 500+ lines |
| **Blocks future features** | Yes — [CatalogEditorPage](../../apps/desktop/src/pages/CatalogEditorPage.tsx), [CatalogPresentationBuilder](../../apps/desktop/src/components/catalog-builder/CatalogPresentationBuilder.tsx) |

### Required backend/API contract

**Option A (recommended):** Optional query params on existing endpoints; omitting params preserves current full-payload behavior.

```
GET /api/v1/catalogs/{id}?items_page=1&items_page_size=50
→ CatalogDetail with paginated items[] + items_total, items_page, items_page_size

GET /api/v1/catalogs/{id}/layout-status?products_page=1&products_page_size=50
→ LayoutStatus with paginated products[] + products_total, products_page, products_page_size
```

- Same pagination pattern as API-3: `{ items/products, total, page, page_size }`
- Item/product shape unchanged
- Summary/diagnostics on layout-status remain global (not paginated) unless Agent 2 documents otherwise

### Required frontend integration (Agent 4, post-CONFIRMED)

- Replace client `paginate()` in Products tab lines and Presentation product table
- `getCatalog()` / `getCatalogLayoutStatus()` pass page params
- Handle page reset on filter/search changes
- DnD save (API-5) may still operate on full order or current page per existing UX limitation

### Acceptance criteria

- [ ] Catalogues with 500+ lines load without transferring full arrays by default when frontend requests pages
- [ ] Backward compatible: no params → current behavior
- [ ] Backend tests for pagination + catalog not found
- [ ] Contract `CONFIRMED` before Agent 4 integration

### Implementation notes for Agent 2

- Affected routers: `apps/api/app/routers/catalogs.py`
- `GET /catalogs/{id}` currently returns all items via `catalog_resolve.py`
- `GET /catalogs/{id}/layout-status` builds full `products[]` in layout service
- Consider performance of diagnostics when only products are paginated

### Risks

- DnD reorder semantics across pages remain a frontend UX limitation until designed
- Full catalog load may still be needed for cross-page reorder UX until API-4 + dedicated UX exist (API-5 reorder save is integrated)

### Open questions

- Separate `GET /catalogs/{id}/items` endpoint vs query params on `GET /catalogs/{id}`? (Agent 2 decides; document in contract.)
- Should `layout-status` paginate diagnostics too? (Assume products only.)

---

## API-5 — Bulk reorder (catalog line items)

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 (backend) / Agent 4 (frontend) |
| **Priority** | P1 |
| **Status** | **INTEGRATED** |
| **Backend** | `CONFIRMED` |
| **Frontend integrated by** | Agent 4 (2026-06-07) |
| **Backend appears implemented** | Yes — `PATCH /catalogs/{id}/items/reorder` in `catalogs.py` |
| **Blocks manual QA** | Agent 1A DnD smoke on stress catalog pending |

### Contract (integrated)

```
PATCH /api/v1/catalogs/{catalog_id}/items/reorder
→ { "updated": N }
```

- IDs are catalogue line item IDs: `catalog.items[].id`
- **Atomic / all-or-nothing** — no per-item errors
- No fallback to N sequential PATCH requests
- `patchCatalogItem()` remains for markup/price override only

### Frontend integration record (Agent 4 — complete)

| Item | Detail |
|------|--------|
| **Tests** | `npm test` 55/55; `npm run build` OK |
| **Files** | `api.ts`, `catalogLines.ts`, `CatalogEditorPage.tsx`, `catalogLines.test.ts`, `reorderCatalogItems.test.ts` |
| **api.ts** | `reorderCatalogItems()`, `CatalogItemReorderEntry`, `CatalogItemsReorderResult` |
| **catalogLines.ts** | Bulk `applySortOrderUpdates()`, `filterSortOrderChanges()`, `mapReorderError()`; sequential PATCH loop removed |
| **CatalogEditorPage** | `saveLineOrder()` uses bulk reorder |
| **Not changed** | `SortableCatalogLines.tsx`; no `apps/api/**`; no unrelated app-wide UI |

**UX (wired):**

- Success → `toast.success("Orden guardado")`, `reloadCatalogAndPreview()`
- No changes → `toast.info("El orden ya está guardado")`, `orderDirty = false`
- Atomic failure → `toast.error(mapReorderError(e))`, unsaved banner remains
- `savingOrder` disables Guardar/Descartar

**Locks:** `api.ts`, `catalogLines.ts`, `CatalogEditorPage.tsx` — **released**.

**Agent 1A next:** Manual DnD smoke on QA Stress Catalog; optional toast/loading polish on "Guardar orden".

**Agent 2:** No further API-5 backend action unless smoke finds contract bug.

### Acceptance criteria

- [x] Single request persists full catalog or full page reorder
- [x] 50+ line reorder completes in one round-trip
- [x] Invalid item id returns documented error without corrupting order
- [x] Backend tests cover happy path, empty list, foreign item id, not-found catalog
- [x] Agent 4 integrates bulk reorder; sequential PATCH loop removed
- [x] Frontend integration tests pass (55/55)

Contract: [API-5_CONTRACT_SUMMARY.md](./contracts/API-5_CONTRACT_SUMMARY.md)

### Risks

- Cross-page DnD semantics remain a frontend UX limitation until API-4 + dedicated UX
- Concurrent editors overwriting order (out of scope unless documented)

### Open questions

- ~~Atomic all-or-nothing vs per-item error list?~~ **Closed:** atomic all-or-nothing (see [API-5_CONTRACT_SUMMARY.md](./contracts/API-5_CONTRACT_SUMMARY.md)).

---

## API-6 — Presentation master reorder

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 |
| **Priority** | P3 |
| **Status** | OPEN |
| **Backend appears implemented** | No — order derived from line-item `sort_order` in `catalog_builder.py` |
| **Blocks manual QA** | No |
| **Blocks future features** | Yes — Presentation tab drag-and-drop ordering |

### Required backend/API contract

- Persist **per-catalog master order** (section-aware) affecting preview HTML and PDF export order
- Proposed endpoint (Agent 2 may refine):

```
PATCH /api/v1/catalogs/{id}/masters/reorder
{ "items": [{ "master_id": "uuid", "sort_order": 0 }] }
→ { "updated": int }
```

- Alternative: formalize line-item `sort_order` as canonical master order (document semantics)
- Order must be reflected in `catalog_builder.py` section/master sorting

### Required frontend integration (Agent 4, post-CONFIRMED)

- **Do not implement** Presentation tab DnD until contract `CONFIRMED`
- Future: DnD on presentation product table, preview/PDF reflects order

### Acceptance criteria

- [ ] Master order persisted per catalog
- [ ] Preview and PDF order match stored master order within section
- [ ] Document relationship to variant line `sort_order` (independent vs derived)
- [ ] Backend tests for reorder + builder output order

### Implementation notes for Agent 2

- Current builder groups by category section; masters sort by `min(row.sort_order)` among variant lines
- Options: new `catalog_master_order` table vs normalize via line items
- Files: `catalog_builder.py`, `catalogs.py`, possibly new migration

### Risks

- Overlap with API-5 line reorder semantics may confuse users
- Section boundaries vs global master order

### Open questions

- Should presentation master order be **independent** of variant line order, or remain derived from line items? (Agent 2 design decision.)

---

## API-7 — Category tree reorder

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 |
| **Priority** | P3 |
| **Status** | OPEN |
| **Backend appears implemented** | No — `categories` sorted alphabetically by name in `categories.py` |
| **Blocks manual QA** | No |
| **Blocks future features** | Yes — category/section ordering in catalogue builder |

### Required backend/API contract

- `categories.sort_order` column (migration required)
- Reorder endpoint, e.g.:

```
PATCH /api/v1/categories/reorder
{ "items": [{ "id": "uuid", "sort_order": 0, "parent_id": null }] }
→ { "updated": int }
```

- `GET /categories` tree respects `sort_order` among siblings; fallback to name for ties
- Catalogue section order in PDF/preview follows category order where applicable

### Required frontend integration (Agent 4, post-CONFIRMED)

- **Do not implement** category DnD until contract `CONFIRMED`
- Future: reorder UI in builder category/section panel

### Acceptance criteria

- [ ] Migration adds `sort_order` with sensible default for existing rows
- [ ] Tree build uses `sort_order`
- [ ] Reorder validates parent_id consistency (no orphans/cycles)
- [ ] Backend tests for reorder and tree output order

### Implementation notes for Agent 2

- Model: `apps/api/app/models/entities.py` — `Category`
- Router: `apps/api/app/routers/categories.py` — `build_tree()`
- Migration: new revision after `001_pim_schema.py`

### Risks

- Existing imports/seeders assume name-based order
- Moving categories affects catalogue section grouping

### Open questions

- Reorder canonical PIM categories only, or also import taxonomy tree? (Assume PIM `/categories` for v1.)

---

## API-8 — Bulk layout skipped reasons

| Field | Value |
|-------|-------|
| **Owner** | Agent 2 |
| **Priority** | P1 |
| **Status** | **INTEGRATED** |
| **Backend appears implemented** | Yes — `POST /catalogs/{id}/product-layouts/bulk` returns `skipped[]` |
| **Frontend integrated by** | Agent 4 (2026-06-07) |
| **Blocks manual QA** | Partial — manual QA for skip-reason list display |
| **Blocks future features** | No — UX polish |

### Required backend/API contract

```
POST /api/v1/catalogs/{id}/product-layouts/bulk
{ "layout_id": "string|null", "master_ids": ["uuid", ...] }
→ {
  "applied": int,
  "cleared": int,
  "skipped": [{ "master_id": "uuid", "reason": "human-readable string" }]
}
```

Known reasons (Agent 2 validate/stable):
- `"Product not in catalog"`
- Layout validation errors from `LayoutConfigError` (e.g. incompatible layout for variant count)

### Frontend integration record (Agent 4 — complete)

| Item | Detail |
|------|--------|
| **Tests** | `npm test` 48/48; `npm run build` OK |
| **Files** | `api.ts`, `catalogLayout.ts`, `CatalogPresentationBuilder.tsx`, `catalogLayout.test.ts` |
| **Types** | `BulkLayoutSkipped`, `BulkLayoutResult`, `BulkLayoutFeedback` |
| **Wiring** | `buildBulkLayoutFeedback()`; skip reasons in `CatalogPresentationBuilder`; list UI for skipped items |

**Agent 1A (post-INTEGRATED):** visual polish for skip-reason list in Presentation Builder if needed.

**Manual QA:** stress seed → QA Stress Catalog → Presentation tab → bulk-apply `single_standard` → confirm skipped items show product name + reason.

### Acceptance criteria

- [x] Agent 2 confirms `skipped` array always present (may be empty)
- [x] Reasons are stable, human-readable, suitable for UI display
- [x] Backend tests cover skipped paths (not in catalog, incompatible layout)
- [x] Contract `CONFIRMED`; Agent 4 wires skip reasons
- [x] Frontend integration complete; Agent 1A may polish display

Contract: [API-8_CONTRACT_SUMMARY.md](./contracts/API-8_CONTRACT_SUMMARY.md)

### Implementation notes for Agent 2

- **No immediate follow-up** — integration complete. Future work only if integration bugs reported.

### Risks

- Skip reasons are free-text; tests use substrings rather than exact snapshots
- Visual polish for skip-reason list belongs to Agent 1A
- Agent 2 may standardize `reason_code` later (optional enhancement)

### Open questions

- Should Agent 2 add machine-readable `reason_code` alongside `reason`? (Optional enhancement.)

---

# Agent 2 handoff prompts

Copy-paste-ready implementation prompts. One per dependency.

---

## Prompt — API-1: Validate QA/stress catalogue seeder

**Objective:** Validate and officially sign off the QA/stress catalogue seeder so manual QA can run at ~350 products with documented layout/diagnostic edge cases.

**Allowed scope:**
- `apps/api/app/services/seed_stress_catalog.py`
- `apps/api/scripts/seed_stress_catalog.py`
- `apps/api/tests/test_stress_seed_integration.py`, `test_seed_stress_catalog.py`
- `docs/STRESS_CATALOG_SEED.md`

**Blocked scope:**
- `apps/desktop/**`
- Unrelated API endpoints
- Frontend tests

**API/schema/seed scope:**
- npm scripts: `db:seed:stress`, `db:seed:stress:fresh`
- Catalogue name default: `QA Stress Catalog`
- ~350 masters, 15+ categories, profiles: single, grid_1attr, row_2attr, no_image, no_category, incomplete_variants, incompatible overrides
- Layout coverage: `single_standard`, `variant_grid_50_50`, `variant_row_wide`

**Validation rules:**
- `--dry-run` reports expected counts
- `--fresh` removes only stress prefix data, not full DB
- Idempotent re-run updates without duplicating masters

**Tests expected:**
- Run `pytest apps/api/tests/test_stress_seed_integration.py apps/api/tests/test_seed_stress_catalog.py`
- All pass

**Migration considerations:** None (uses existing schema)

**Backward compatibility:** Seeder is additive; must not break existing PIM seed

**Expected output (contract summary for Agent 3):**
```
Dependency: API-1
Status recommendation: CONFIRMED | DONE (no Agent 4 for seeder-only)
Commands: npm run db:seed:stress / db:seed:stress:fresh
Catalog name: QA Stress Catalog
Counts: masters, variants, categories, layout overrides
Profiles confirmed: [list]
Tests run: [commands + pass/fail]
Docs updated: STRESS_CATALOG_SEED.md [yes/no]
QA unblocked: [MANUAL_QA sections]
```

---

## Prompt — API-3: Validate product masters pagination

**Objective:** Confirm and document server-side pagination on `GET /api/v1/product-masters` as the official contract for the Products list page.

**Allowed scope:**
- `apps/api/app/routers/masters.py`
- `apps/api/app/schemas.py` (`ProductMasterListResponse`, `ProductMasterOut`)
- Backend tests for masters list

**Blocked scope:**
- `apps/desktop/**`
- Catalog endpoints (API-4)

**API/schema/seed scope:**
```
GET /api/v1/product-masters?q&page&page_size
→ { items, total, page, page_size }
```
- Defaults: page=1, page_size=50, max page_size=200

**Validation rules:**
- `page` >= 1, `page_size` 1–200
- `total` is count of filtered query, not len(items)
- `q` filters name and master_key (case-insensitive)

**Tests expected:**
- Pagination boundaries, empty results, search filter
- Add tests if missing

**Migration considerations:** None

**Backward compatibility:** Omitting page/page_size must keep current defaults (first page, size 50)

**Expected output:**
```
Dependency: API-3
Status recommendation: CONFIRMED → READY_FOR_AGENT4
Endpoint: GET /api/v1/product-masters
Request/response: [full JSON schema]
Breaking changes: none
Tests: [commands]
Agent 4 files to integrate: api.ts listMasters, ProductsPage.tsx
Known issue: frontend currently omits pagination params
```

---

## Prompt — API-4: Server-side pagination for builder tables

**Objective:** Add optional server-side pagination for catalog line items and/or layout-status product lists to support catalogues exceeding ~500 rows without full payload transfer.

**Allowed scope:**
- `apps/api/app/routers/catalogs.py`
- `apps/api/app/services/catalog_resolve.py`, `catalog_layout.py`
- `apps/api/app/schemas.py`
- Backend tests

**Blocked scope:**
- `apps/desktop/**`
- Unrelated routers

**API/schema/seed scope (proposed — refine as needed):**
```
GET /api/v1/catalogs/{id}?items_page&items_page_size
GET /api/v1/catalogs/{id}/layout-status?products_page&products_page_size
```
- Response includes pagination metadata; item/product shapes unchanged
- Omitting params returns full payload (backward compatible)

**Validation rules:**
- Valid catalog id
- page/page_size bounds consistent with API-3
- Empty page returns `items: []`, correct `total`

**Tests expected:**
- Paginated catalog detail, layout-status products page
- Not found, out-of-range page

**Migration considerations:** None unless new indexes recommended for large catalogs

**Backward compatibility:** Required — default behavior unchanged when params omitted

**Expected output:**
```
Dependency: API-4
Status recommendation: CONFIRMED → READY_FOR_AGENT4
Endpoints: [paths + params]
Response shapes: [JSON]
Diagnostics handling: [global vs paginated]
Tests: [commands]
Agent 4 integration notes: CatalogEditorPage, CatalogPresentationBuilder, api.ts
```

---

## Prompt — API-5: Bulk reorder catalog line items

**Objective:** Implement a single endpoint to persist multiple catalogue item `sort_order` values in one request, replacing N sequential PATCH calls from the Products tab DnD save flow.

**Allowed scope:**
- `apps/api/app/routers/catalogs.py`
- `apps/api/app/schemas.py`
- Backend tests

**Blocked scope:**
- `apps/desktop/**`
- Master/category reorder (API-6, API-7)

**API/schema/seed scope:**
```
PATCH /api/v1/catalogs/{id}/items/reorder
Body: { "items": [{ "id": "uuid", "sort_order": int }] }
Response: { "updated": int }
```

**Validation rules:**
- Catalog must exist
- All item ids must belong to catalog
- Reject duplicate ids; document `sort_order` gap/duplicate policy
- Prefer atomic commit

**Tests expected:**
- Reorder 50+ items in one call
- Invalid id → 422 without partial apply (if atomic)
- Catalog not found → 404

**Migration considerations:** None

**Backward compatibility:** Keep existing `PATCH .../items/{item_id}` for single-field edits

**Expected output:**
```
Dependency: API-5
Status recommendation: CONFIRMED → READY_FOR_AGENT4
Endpoint: PATCH /api/v1/catalogs/{id}/items/reorder
Request/response: [JSON]
Atomicity: [yes/no + semantics]
Tests: [commands]
Agent 4: catalogLines.ts applySortOrderUpdates, api.ts reorder endpoint
```

---

## Prompt — API-6: Presentation master reorder

**Objective:** Add backend support for persisting product master display order per catalogue, affecting preview HTML and PDF export order in the Presentation flow.

**Allowed scope:**
- `apps/api/app/routers/catalogs.py`
- `apps/api/app/services/catalog_builder.py`
- Models, migrations if new table/columns needed
- Backend tests

**Blocked scope:**
- `apps/desktop/**`
- Category reorder (API-7)

**API/schema/seed scope:**
- Design and implement reorder endpoint (e.g. `PATCH /catalogs/{id}/masters/reorder`)
- Document relationship to existing line-item `sort_order`
- PDF/preview order must reflect stored order within sections

**Validation rules:**
- master_ids must exist in catalog
- Section-aware ordering documented

**Tests expected:**
- Reorder changes builder output order
- Preview/PDF integration test or builder unit test

**Migration considerations:** Likely new `catalog_master_order` table or equivalent — document choice

**Backward compatibility:** Existing catalogs get default order from current line-item derivation

**Expected output:**
```
Dependency: API-6
Status recommendation: CONFIRMED (UI not built yet)
Design decision: [independent vs derived order]
Schema: [tables/columns]
Endpoint: [method path]
Tests: [commands]
Agent 4: wire reorder API first; Agent 1A: visual DnD UI after INTEGRATED
```

---

## Prompt — API-7: Category tree reorder

**Objective:** Add `sort_order` to categories and an API to reorder categories/subcategories so future catalogue builder UI can control section order.

**Allowed scope:**
- `apps/api/app/routers/categories.py`
- `apps/api/app/models/entities.py`
- Alembic migration
- Backend tests

**Blocked scope:**
- `apps/desktop/**`
- Import taxonomy canonical tree (unless explicitly scoped)

**API/schema/seed scope:**
```
PATCH /api/v1/categories/reorder
Body: { "items": [{ "id", "sort_order", "parent_id" }] }
GET /categories → tree sorted by sort_order among siblings
```

**Validation rules:**
- No cycles in parent_id
- Cannot reorder into invalid parent
- Default sort_order for existing rows on migration

**Tests expected:**
- Tree order after reorder
- Sibling order independent of name

**Migration considerations:** Add `sort_order` column with server default 0; backfill if needed

**Backward compatibility:** Namesort fallback where sort_order ties

**Expected output:**
```
Dependency: API-7
Status recommendation: CONFIRMED (UI not built yet)
Migration: [revision id]
Endpoint: [method path]
Tests: [commands]
Agent 4: wire category reorder API first; Agent 1A: visual DnD after INTEGRATED
```

---

## Prompt — API-8: Validate bulk layout skipped reasons

**Objective:** Validate that `POST /catalogs/{id}/product-layouts/bulk` returns stable, human-readable per-product skip reasons and sign off the contract for frontend bulk feedback UI.

**Allowed scope:**
- `apps/api/app/routers/catalogs.py` (`bulk_product_layouts`)
- `apps/api/app/services/catalog_layout.py`
- Backend tests for bulk layout

**Blocked scope:**
- `apps/desktop/**`

**API/schema/seed scope:**
```
POST /api/v1/catalogs/{id}/product-layouts/bulk
→ { applied, cleared, skipped: [{ master_id, reason }] }
```

**Validation rules:**
- `skipped` always an array (possibly empty)
- Reasons human-readable; document known reason strings
- Optional: add `reason_code` if standardization desired

**Tests expected:**
- Master not in catalog → skipped with reason
- Incompatible layout → skipped with LayoutConfigError message
- All valid → skipped []

**Migration considerations:** None

**Backward compatibility:** Response shape must not remove fields; adding `reason_code` is optional

**Expected output:**
```
Dependency: API-8
Status recommendation: CONFIRMED → READY_FOR_AGENT4
Endpoint: POST /api/v1/catalogs/{id}/product-layouts/bulk
Skipped shape: [{ master_id, reason (, reason_code?) }]
Known reasons: [list]
Tests: [commands]
Agent 4: CatalogPresentationBuilder skip-reason wiring; Agent 1A: visual polish
```

---

# Agent 4 integration prompts (overview)

ChatGPT **Agent 4 prompt-generation chat** creates Cursor integration prompts from **confirmed** contracts (step 9). Agent 4 must not start until Agent 2 Contract Summary and status `READY_FOR_AGENT4`.

Each prompt should include:

| Field | Content |
|-------|---------|
| Dependency ID | API-X |
| Contract reference | Link to [UI_BACKEND_CONTRACTS.md](./UI_BACKEND_CONTRACTS.md) entry (must be `CONFIRMED`) |
| Allowed scope | `api.ts`, types, hooks, minimal wiring, integration tests |
| Blocked scope | `apps/api/**`, inventing contracts, design-heavy UI |
| Files to change | From Agent 2 Contract Summary `Agent 4 integration scope` |
| Types | Request/response TypeScript shapes from contract |
| Wiring tasks | Specific function calls, page param changes, error handling |
| Tests | Files to update (e.g. `catalogLines.test.ts`) |
| Handoff to Agent 1A | Components Agent 1A may visually polish after `INTEGRATED` |

### Per-dependency Agent 4 scope (after CONFIRMED)

| ID | Agent 4 integrates | Agent 1A polishes after INTEGRATED |
|----|-------------------|-----------------------------------|
| API-1 | — (seeder only) | — |
| API-3 | ~~`listMasters` pagination, `ProductsPage.tsx`~~ **INTEGRATED** | Labels, a11y, pager UX clarity (Agent 1B) — Agent 1A: no role |
| API-4 | `getCatalog` / `getCatalogLayoutStatus` pagination, builder pages | Pagination bar styling |
| API-5 | ~~Reorder endpoint in `api.ts`, `catalogLines.ts`~~ **INTEGRATED** | Save/discard UX, toasts (Agent 1A polish) |
| API-6 | Master reorder API wiring | Presentation DnD visuals |
| API-7 | Category reorder API wiring | Category DnD visuals |
| API-8 | ~~Skip-reason list in `CatalogPresentationBuilder`~~ **INTEGRATED** | Bulk feedback banner visual polish (Agent 1A) |

---

## Related documents

- [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)
- [UI_BACKEND_CONTRACTS.md](./UI_BACKEND_CONTRACTS.md)
- [TASK_HISTORY.md](./TASK_HISTORY.md)
- [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml)
- Legacy: [BUILDER_BACKEND_DEPENDENCIES.md](../BUILDER_BACKEND_DEPENDENCIES.md)
