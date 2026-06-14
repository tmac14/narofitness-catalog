# PDF Export / Print Renderer — Contract Summary

**Agent:** 6  
**Track ID:** PDF-EXPORT  
**Date:** 2026-06-08  
**Status:** **`PDF_LAYOUT_VISUALLY_ACCEPTED`** · **`PDF_EXPORT_INTEGRATED`** · **`EXPORT_QA_PENDING`**

---

## Scope

Catalogue **PDF export** and **PDF-oriented table layout** for preview + print. Out of scope: FDL importer/parser logic, taxonomy, brand resolution at import time (Agent 2 / PR-* track).

| In scope | Out of scope |
|----------|--------------|
| `POST /export/pdf` pipeline | Parser row grouping |
| `PdfExportEngine` abstraction | Import review UI |
| `catalog_supplier_table` shell + `family_variant_table` layout | Replacing legacy layouts (`single_standard`, `variant_row_wide`, `variant_grid_50_50`) |
| Preview PDF (`POST .../preview/pdf`) + export via shared pipeline | Agent 5 audit tooling (fixtures only) |
| Preview/export context parity via shared `build_catalog_context` | HTML iframe as opt-in fallback only (PREV-3) |

---

## Coordination status

| Flag | Meaning |
|------|---------|
| `PDF_LAYOUT_VISUALLY_ACCEPTED` | User accepted PDF-table visual iteration (brand groups, columns, typography, placeholders). |
| `PDF_EXPORT_INTEGRATED` | Export button planning fixed; engine abstraction shipped; automated tests green. |
| `EXPORT_QA_PENDING` | Full manual QA checklist not yet signed off (Windows download, page breaks, large families, stress catalog). |

**Not yet `QA_READY`:** Phase 1 stress QA explicitly deferred PDF execution; pagination/orphan-header checks remain open.

---

## Export trigger (desktop)

| Rule | Contract |
|------|----------|
| UI entry points | `CatalogEditorHeader`, `PreviewWorkspace` → **Exportar PDF** |
| Preview behavior | Export **must not** call `refreshPreview()` / reload PDF preview viewer |
| Dirty guards | Block when `orderDirty` or `pendingPreview`; user saves Productos / Presentación first |
| General tab | Persist via `updateCatalog({ skipPreviewRefresh: true })` before export when dirty |
| Download | Client `triggerPdfDownload()`; filename `sanitizePdfFilename(catalogName)`; body magic `%PDF` |

**Owner:** Agent 6 (pipeline); Agent 4 already integrated `exportCatalogPdf()` in `api.ts` — no new API-X lock.

---

## HTTP contract

```
POST /api/v1/catalogs/{catalog_id}/export/pdf
Body: none
```

| Success | `200`, `Content-Type: application/pdf`, PDF bytes |
| Errors | `404` catalog not found; `503` no PDF engine available |

**State source:** `build_catalog_context(catalog_id, for_html_preview=false)` — server DB, not preview viewer DOM.

---

## Preview PDF endpoint (PREV-3 — separate from export)

**Status:** **`IMPLEMENTED` / `QA_PASS`** — full contract: [CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md](./CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md). Manual QA passed 2026-06-07; preview/export page-count comparison accepted.

```
POST /api/v1/catalogs/{catalog_id}/preview/pdf?cache_bust={optional}
```

| Success | `200`, `application/pdf`, PDF bytes |
| Headers | `X-Total-Pages`, `X-Pdf-Engine`, `X-Preview-Generated-At` |
| Side effects | Ephemeral cache under `data_dir/previews` (24h TTL); **no** `CatalogExport` row |
| Frontend | PDF.js paginated viewer — one page at a time; opt-in HTML fallback only |

**Relationship to export:**

| Path | Role |
|------|------|
| `POST .../preview/pdf` | Non-persistent preview cache; drives in-app paginated viewer |
| `POST .../export/pdf` | **Authoritative** download; unchanged by PREV-3 |

**Parity QA:** For one representative catalogue, `X-Total-Pages` = PDF.js `numPages` = exported PDF page count.

**Playwright engine note:** Export may still load `GET .../preview/html?render_density=print` for Chromium rendering when `catalog_id` + `api_base` present — distinct from the desktop PDF.js preview viewer.

---

## Renderer engine decision (implemented)

| Engine | Role |
|--------|------|
| **Playwright / Chromium** | **Preferred Phase 1 default** (`PDF_EXPORT_ENGINE=auto` → playwright when available) |
| **WeasyPrint** | **Legacy fallback** when Playwright unavailable |
| **PrinceXML / DocRaptor** | **Future premium stubs only** — Phase 2 if advanced print pagination required |

**Abstraction:** `app/services/pdf_engines/` — `PdfExportEngine` protocol, registry, `resolve_pdf_export_engine()`.

**Parity strategy:** Playwright loads preview URL (`/api/v1/catalogs/{id}/preview/html?render_density=print`) when `catalog_id` + `api_base` present; otherwise `set_content` + filesystem `base_url`.

**Render density (2026-06-08):** Opt-in HTML fallback uses `render_density=screen` (default). PDF export and `POST .../preview/pdf` use `for_html_preview=false` / print density via shared export pipeline. PDF export uses `catalog_render_density=print` → `body.catalogue-pdf-render` + `_supplier_table_print.css` for smaller A4 typography, tighter padding, wider SKU column, no SKU ellipsis.

**Health:** `GET /api/v1/health` exposes `pdf_engine`, `pdf_engine_fallback`, `pdf_engines_available`, `pdf_engine_error`. Desktop `Layout` shows degraded badge when `pdf_engine` is null.

**Rationale:** Chromium matches browser preview CSS/fonts; WeasyPrint retained for Docker/minimal installs and CI without Chromium.

---

## Layout selection

| Condition | Template shell |
|-----------|------------------|
| `layout_mode=uniform` + `uniform_layout_id=family_variant_table` | `catalog_supplier_table.html` |
| All resolved product `layout_id` = `family_variant_table` | `catalog_supplier_table.html` |
| Otherwise | `catalog_branded.html` / `catalog_default.html` (unchanged) |

**Registry ID:** `family_variant_table` — UI label *Tabla familia-variante (PDF)*. Existing layouts **remain registered**; this is an **additional PDF-oriented representation**.

---

## PDF-table layout contract

### Visual hierarchy (top → bottom)

1. **Category section header** — red, full width (`section.name`)
2. **Brand header** — secondary grey band per commercial brand group
3. **Product/family master header** — dark grey (`family_title` / `title_line1`)
4. **Detail block** — column headers + data row(s)

### Brand grouping

| Rule | Value |
|------|-------|
| Group within category | By **commercial brand** (`master.brand`), not supplier |
| Missing brand | `"Sin marca"` |
| Supplier vs brand | Separate concepts; supplier never substituted as commercial brand in PDF-table shell |
| Builder | `group_products_by_brand()` → `section.brand_groups[]` when `catalog_shell=supplier_table` |

### Rendering modes (same visual system)

**Decision:** `len(variants) == 1` → `simple_product_block`; `len(variants) > 1` → `family_variant_table`.

#### `simple_product_block`

- Per-product table: `supplier-catalog-table--simple`
- `<colgroup>` fixed widths (Imagen 21% · SKU 14% · EAN 14% · P.V.P. 9% · Descripción 42%)
- Columns: **Imagen** (no header label) · **SKU** · **EAN** · **P.V.P.** · **Descripción**
- Product header **does not repeat brand** when subtitle equals commercial brand (brand shown in brand header)
- Description column: smaller body font; header same Montserrat 9pt as other headers, left-aligned with indent

#### `family_variant_table`

- Per-product table: `supplier-catalog-table--family`
- Master header + variant rows
- Columns: Variante/specs · SKU · EAN · P.V.P. · Imagen familia (rowspan, last column, no header label)
- Family image shared across variant rows

### Column rules (both modes)

| Column | Rule |
|--------|------|
| **EAN** | **Always dedicated column**; render `—` when empty — never merged into SKU |
| **P.V.P.** | Default label via `supplier_price_column_label` (`"P.V.P."`); configurable later |
| **SKU** | Monospace in **data cells only**; headers use Montserrat |
| **Price** | Centered content; light green background `#e8f5e9` |

### Images

| Rule | Behavior |
|------|----------|
| Simple products | Larger image cell (~140×120px max) |
| Variant families | Family image once per block (`rowspan`) |
| Missing image | `resolve_placeholder_url()` professional placeholder — **no broken image icons** |
| Broken URLs | Placeholder fallback via builder context |

### Pagination / print CSS

- `break-inside: avoid` on product blocks and section headers (best-effort)
- A4, 15 mm margins
- **Open QA:** orphan family header vs first variant row; large families across pages

---

## Context fields (supplier shell)

| Field | Purpose |
|-------|---------|
| `catalog_shell` | `"supplier_table"` when uniform/all `family_variant_table` |
| `catalog_render_density` | `"screen"` (preview iframe) or `"print"` (export / Playwright URL) |
| `brand_groups` | `[{ brand, products }]` per section |
| `supplier_table_show_ean` | Always `true` (EAN column always rendered) |
| `supplier_price_column_label` | Default `"P.V.P."` |
| `sections` | Flat `products` retained for non-supplier templates |

### Print typography targets (`catalogue-pdf-render`)

| Element | Size |
|---------|------|
| Category header | 8.5pt |
| Brand header | 7.5pt |
| Product/family header | 7pt |
| Table header | 6.5pt |
| Body / variant cells | 6.5pt |
| SKU / EAN | 6pt monospace |
| P.V.P. | 7.5pt bold |
| Legal footer | 5.5pt |

SKU cells: `overflow: visible` in print scope — full values (e.g. `REPUESTO-806`) must not ellipsis.

---

## Automated tests (Agent 6)

| File | Coverage |
|------|----------|
| `test_pdf_engines.py` | Engine registry, Playwright/WeasyPrint selection |
| `test_pdf_export.py` | HTML render, template shell selection |
| `test_family_variant_table_layout.py` | Brand groups, colgroup widths, SKU/EAN/P.V.P., simple vs family modes |
| `test_catalog_export_route.py` | `POST /export/pdf` route + engine facade |
| `apps/desktop/src/lib/exportPdf.test.ts` | Client download/guards |

---

## Regression fixtures (catalogue data)

Use Agent 5 page audits + FDL seed paths as **QA fixtures** (Agent 5 does not own export):

| Fixture | Validates |
|---------|-----------|
| Pages **3 / 4 / 5** data | Simple 1:1 products, brand grouping, compact SKU/EAN/P.V.P. columns |
| Page **11** data | Multi-variant families (CROSSTRAINING bumper), rowspan image, variant rows |
| Page **12** (when import fixed) | Mixed blocks, larger variant families, page-break stress |

**Stress path:** `npm run db:seed:stress:fresh` → QA Stress Catalog — layout modes + scale (may not use `family_variant_table` unless presentation set).

---

## Agent handoff

| Agent | Role |
|-------|------|
| **Agent 6** | PREV-3 **QA_PASS**; VARIANT-REP MARCA/VARIANTE **integrated** — visual QA pending; **PDF-TABLE-FIX-1** visual confirm pending |
| **Catalog UI agent** | Idle — optional polish on regressions |
| **Agent 4** | `fetchCatalogPreviewPdf` **complete** — idle unless integration bugs |
| **Agent 2** | VARIANT-REP backend **COMPLETE**; B2 integration tests pending |
| **Agent 5** | Page audits as QA fixtures |
| **User** | PDF-1 export QA remaining — [PDF-EXPORT-PREVIEW-MANUAL-QA.md](../tasks/PDF-EXPORT-PREVIEW-MANUAL-QA.md) |

---

## Open risks / questions

| # | Risk | Status |
|---|------|--------|
| 1 | Export button fully fixed? | **Yes** — code + unit tests; manual Windows sign-off pending |
| 2 | Playwright implemented or planned? | **Implemented** — default with WeasyPrint fallback |
| 3 | Page breaks / pagination QA’d? | **Open** — CSS `break-inside` only; no Prince/DocRaptor yet |
| 4 | Large variant families QA’d? | **Open** — page 11 fixture recommended |
| 5 | PDFs checked on Windows? | **Open** — user manual QA |
| 6 | Automated PDF smoke? | **Partial** — route + HTML tests; no binary PDF snapshot CI |
| 7 | WeasyPrint still in use? | **Yes** — fallback engine, not removed |
| 8 | Preview vs PDF page-count parity | **Accepted** — PREV-3 manual QA passed (2026-06-07) |
| 8b | Preview vs PDF pixel parity | **Close** — shared render pipeline; engine-specific font/render deltas possible |
| 9 | Packaging Chromium for desktop bundle | **Phase 1b groundwork** — PyInstaller/electron-builder notes exist; not QA’d end-to-end |

---

## Related documents

- [CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md](./CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md)
- [UI_BACKEND_CONTRACTS.md § API-EXPORT-PDF / API-PREVIEW-PDF](../UI_BACKEND_CONTRACTS.md)
- [TASK_HISTORY.md](../TASK_HISTORY.md)
- [PDF-EXPORT-PREVIEW-MANUAL-QA.md](../tasks/PDF-EXPORT-PREVIEW-MANUAL-QA.md)
- [engineering roles.yaml](../engineering roles.yaml)
- Product layout registry (non-coordination): `docs/CATALOG_LAYOUTS.md`
