# Manual QA — Presentation Builder

This checklist covers everything that **cannot be validated automatically** and requires opening the application, inspecting the UI, generating previews, and exporting PDFs.

## Pre-requisitos (obligatorio antes de empezar)

1. **Migraciones aplicadas** (gestionadas por el agente backend — consultar revisión actual):
   ```bash
   npm run docker:up
   npm run db:migrate
   docker compose exec api alembic current
   ```

2. **Catálogo de prueba con suficientes productos** (usar seeder oficial cuando esté disponible):
   ```bash
   # Pendiente: comando oficial del agente backend
   # npm run db:seed:stress:fresh
   ```
   Anota el **Catalog ID** (UUID) impreso en la salida CLI.

3. **App en marcha:**
   ```bash
   npm run dev
   ```

4. **Abrir catálogo:** Catálogos → **QA Stress Catalog** → pestaña **Presentación**

**Recommended test catalogue:** `QA Stress Catalog` (see [STRESS_CATALOG_SEED.md](./STRESS_CATALOG_SEED.md))

Record at the start of your session:

| Field | Your value |
|-------|------------|
| Catalogue name | |
| Catalogue ID (UUID) | |
| Date | |
| App version / branch | |

---

## A. Builder — Presentation tab

### A-1. Open stress catalogue
**Priority:** Critical

| | |
|---|---|
| **Action** | Run `npm run db:seed:stress`, open desktop app → Catálogos → open **QA Stress Catalog** → **Presentación** tab |
| **Expected** | Tab loads; stats show ~350 products; no blank screen |
| **Bug if** | Error toast, infinite spinner, or 0 products |
| **Send if fails** | Screenshot, catalogue ID, browser/Electron console log, Network timing for `layout-status` |

---

### A-2. Initial load time
**Priority:** High

| | |
|---|---|
| **Action** | Note time from tab click until table is interactive |
| **Expected** | Usable within ~3–8 s locally; no browser freeze; loading copy mentions large catalog may take a few seconds |
| **Bug if** | >15 s freeze, tab crash, UI unresponsive, or spinner with no explanation |
| **Send if fails** | Product count, load time, console log, `layout-status` response time from Network tab |

### A-2b. Spanish display text (skip/diagnostic reasons)
**Priority:** Medium

| | |
|---|---|
| **Action** | Bulk-apply incompatible layout; open **Diagnóstico** panel |
| **Expected** | Skip reasons and diagnostic messages shown in **Spanish** (not raw English API strings) |
| **Bug if** | Primary UI shows `Layout single_standard is not compatible…` or `No manual layout override…` verbatim |
| **Send if fails** | Screenshot of skip feedback panel + diagnostics list |

### A-2c. Presentation form a11y
**Priority:** Low

| | |
|---|---|
| **Action** | Open Presentación tab; run Chrome DevTools **Issues** (or Lighthouse) on form controls |
| **Expected** | Filters, bulk layout select, search, and per-row override editors have `id`/`name` and associated labels |
| **Bug if** | Mass missing `id`/`name` on Presentation controls |
| **Send if fails** | DevTools Issues count + screenshot of filter row |

---

### A-3. Stats cards
**Priority:** Medium

| | |
|---|---|
| **Action** | Review top 5 stat cards |
| **Expected** | Productos ≈350, Categorías ≥15, Fallbacks/Avisos badges only when counts > 0 |
| **Bug if** | Wrong totals vs table footer, overlapping layout |
| **Send if fails** | Screenshot of stats row + table footer total |

---

### A-4. Category sidebar
**Priority:** High

| | |
|---|---|
| **Action** | Click **Todas**, then 3 different categories |
| **Expected** | Active highlight; table filters; badge count matches filtered footer |
| **Bug if** | Wrong products, count mismatch |
| **Send if fails** | Category name clicked, screenshot before/after, filtered count |

---

### A-5. Filters (combined)
**Priority:** High

| | |
|---|---|
| **Action** | Set category + **Con variantes** + **2+ atributos** + status filter |
| **Expected** | Only matching products; page resets to 1 |
| **Bug if** | Non-matching rows appear |
| **Send if fails** | Screenshot of all active filters + resulting table |

---

### A-6. Search debounce
**Priority:** Medium

| | |
|---|---|
| **Action** | Type a product name quickly |
| **Expected** | Table updates after brief pause (~300 ms), not every keystroke |
| **Bug if** | Severe lag while typing or no filter effect |
| **Send if fails** | Note behaviour; console errors if any |

---

### A-7. Pagination
**Priority:** High

| | |
|---|---|
| **Action** | With all products, go to page 1 and last page (should be ~8 pages at 350 products) |
| **Expected** | 50 rows per page; footer shows correct page count |
| **Bug if** | Wrong page size, duplicates across pages |
| **Send if fails** | Screenshots of page 1 and last page footers |

---

### A-8. Bulk apply (filtered)
**Priority:** Critical

| | |
|---|---|
| **Action** | Filter one category → **Aplicar filtrados (N)** with a layout → confirm toast and skip feedback panel |
| **Expected (skips)** | If items are skipped: panel shows applied vs omitted counts clearly; sample reasons in Spanish; expand shows full list when >10 |
| **Expected** | Toast with applied count; only filtered products affected |
| **Bug if** | Products outside filter changed |
| **Send if fails** | Category, layout chosen, N count, screenshot of one affected + one unaffected product |

---

### A-9. Clear overrides
**Priority:** High

| | |
|---|---|
| **Action** | Select products with manual overrides → **Quitar overrides** |
| **Expected** | Toast with cleared count; badges revert to Auto |
| **Bug if** | Overrides remain |
| **Send if fails** | Product master_id before/after, `layout-status` snippet |

---

### A-10. Diagnostics panel
**Priority:** High

| | |
|---|---|
| **Action** | Open **Diagnóstico**; expand severity groups |
| **Expected** | Groups: Crítico / Advertencia / Informativo; no duplicate product+type |
| **Bug if** | Flat unordered list, duplicates, wrong severity |
| **Send if fails** | Screenshot of diagnostics + `diagnostics_by_severity` from layout-status API |

---

### A-11. Layout registry
**Priority:** Low

| | |
|---|---|
| **Action** | Expand **Layouts registrados** |
| **Expected** | 3 layouts with mini previews and product counts |
| **Bug if** | Missing layouts or counts ≠ stats |
| **Send if fails** | Screenshot expanded registry |

---

### A-12. Single layout-status fetch on mount
**Priority:** Medium

| | |
|---|---|
| **Action** | Open Presentación tab with Network tab open; count `layout-status` requests on first open |
| **Expected** | **1** request on initial tab open (not 2) |
| **Bug if** | 2+ identical requests on mount without user action |
| **Send if fails** | Network HAR or screenshot of request list |

---

## B. Preview

### B-1. Preview updated state
**Priority:** Critical

| | |
|---|---|
| **Action** | Click **Vista previa** → wait for load |
| **Expected** | Badge **Actualizada**; iframe shows catalogue content |
| **Bug if** | Blank iframe, stuck on loading |
| **Send if fails** | Screenshot of preview dock + console errors |

---

### B-2. Preview stale state
**Priority:** Critical

| | |
|---|---|
| **Action** | With preview open, change a layout (bulk or config) **without** regenerating |
| **Expected** | Badge **Desactualizada**; **no** new preview-html request in Network |
| **Bug if** | Auto-regenerates or no stale indicator |
| **Send if fails** | Network log around the change, screenshot of badge |

---

### B-3. Manual regeneration
**Priority:** Critical

| | |
|---|---|
| **Action** | Click **Regenerar preview** when stale |
| **Expected** | **Regenerando…** → **Actualizada**; content reflects changes |
| **Bug if** | Stuck loading or old content |
| **Send if fails** | Screenshot of each state |

---

### B-4. Preview error state
**Priority:** High

| | |
|---|---|
| **Action** | If preview fails (stop API temporarily or invalid catalogue) |
| **Expected** | Badge **Error al cargar** |
| **Bug if** | Silent failure or infinite loading |
| **Send if fails** | Console log, API error response |

---

### B-5. Pending changes after layout edit
**Priority:** High

| | |
|---|---|
| **Action** | Edit global layout config without saving → check preview dock |
| **Expected** | Config shows "Cambios sin guardar"; export modal mentions pending preview if exporting |
| **Bug if** | No indication of unsaved config |
| **Send if fails** | Screenshot of config section + export modal |

---

### B-6. Preview matches layout-status
**Priority:** Critical

| | |
|---|---|
| **Action** | Pick 2 products; note layout in table; find them in preview HTML |
| **Expected** | Same layout template (single / grid / row-wide) |
| **Bug if** | Different layout in preview vs table |
| **Send if fails** | Product names, table screenshot, preview screenshot, layout-status JSON for those products |

---

## C. PDF export

### C-1. Export modal — fallbacks/warnings
**Priority:** Critical

| | |
|---|---|
| **Action** | Switch to **Uniforme → single_standard**, save → **Exportar PDF** |
| **Expected** | Professional modal (not browser alert) with severity summary and type counts |
| **Bug if** | `window.confirm` appears, or no modal when fallbacks exist |
| **Send if fails** | Screenshot of modal |

---

### C-2. Export modal — stale preview
**Priority:** High

| | |
|---|---|
| **Action** | Change layout without regenerating preview → Export |
| **Expected** | Modal shows stale preview banner; **Regenerar preview** and **Exportar de todos modos** buttons |
| **Bug if** | No stale warning; auto-regenerates before export |
| **Send if fails** | Screenshot of modal |

---

### C-3. Export modal — info only
**Priority:** Medium

| | |
|---|---|
| **Action** | Export with only info diagnostics (sin imagen, sin categoría) — no fallbacks |
| **Expected** | Modal shows info counts; export allowed without critical checkbox |
| **Bug if** | Blocked export for info-only |
| **Send if fails** | Screenshot of modal |

---

### C-4. Direct export (clean catalogue)
**Priority:** Medium

| | |
|---|---|
| **Action** | On a small catalogue with no issues and updated preview, export |
| **Expected** | No modal; PDF downloads immediately |
| **Bug if** | Modal appears unnecessarily |
| **Send if fails** | Note catalogue used and steps |

---

### C-5. Automatic mode PDF
**Priority:** Critical

| | |
|---|---|
| **Action** | Export **QA Stress Catalog** in automatic mode |
| **Expected** | PDF generates; layouts match automatic assignments |
| **Bug if** | Export fails or wrong layouts |
| **Send if fails** | PDF file, catalogue ID, 2 example products |

---

### C-6. Uniform mode with fallbacks PDF
**Priority:** Critical

| | |
|---|---|
| **Action** | Uniform + single_standard → export after confirming modal |
| **Expected** | PDF uses fallback layouts for incompatible products |
| **Bug if** | Broken blocks or wrong templates |
| **Send if fails** | PDF, list of fallback product names |

---

### C-7. Manual overrides PDF
**Priority:** High

| | |
|---|---|
| **Action** | Manual mode → override 2 products → export |
| **Expected** | PDF reflects manual layouts for those products only |
| **Bug if** | Overrides ignored |
| **Send if fails** | PDF, product IDs, layout-status before export |

---

## D. Visual comparisons required

When reporting issues, provide these captures as applicable:

| # | Capture | When required |
|---|---------|---------------|
| 1 | Full **Presentación** tab (stats + sidebar + table) | Any builder UI issue |
| 2 | Product table with **filters active** | Filter/pagination bugs |
| 3 | **Diagnóstico** panel expanded | Diagnostics issues |
| 4 | **Export PDF modal** | Export warning/modal issues |
| 5 | **Preview iframe** (2+ sections visible) | Preview content issues |
| 6 | **Exported PDF** (full file or pages 1, 2, and one variant page) | PDF content issues |
| 7 | **Single product** with 2+ variant attributes in table + preview + PDF | Layout consistency |

---

## E. Issue report template

Copy and fill for each issue:

```
QA-ID: (e.g. B-2, C-5)
Priority: Critical / High / Medium / Low

Catalogue: [name] / ID: [uuid]
Layout mode: automatic | uniform | manual
Uniform layout (if applicable): [layout_id]
Active filter/category: [name or "none"]
Affected product: [master_name] / master_id: [uuid]
Expected layout: [layout_id or rule]
Applied layout: [layout_id from table/API]

Steps to reproduce:
1.
2.
3.

Expected result:


Actual result:


Attachments:
[ ] Screenshot — Presentation tab
[ ] Screenshot — filters active
[ ] Screenshot — diagnostics
[ ] Screenshot — export modal
[ ] Screenshot — preview
[ ] PDF file
[ ] Console log (paste or screenshot)
[ ] API response — layout-status snippet
[ ] Network — preview-html requests

Console/API errors (exact text):


Additional notes:

```

---

## Suggested test order

1. A-1, A-12 (seed + single fetch)
2. B-1, B-2, B-3 (preview states)
3. B-6, C-5 (consistency)
4. C-1, C-2 (export modal)
5. A-8, A-9 (bulk workflows)
6. C-6, C-7 (PDF modes)
7. Remaining medium/low items

---

## What automated tests already cover (no manual pass needed for logic only)

- Filter/pagination helpers at 400 synthetic products
- Export preflight summary logic (`buildExportPreflight`)
- Diagnostics severity grouping
- Stress seed profile distribution (unit tests)
- Double-fetch guard helper (`shouldReloadLayoutStatusOnPropSync`)

Manual QA is still **required** for visual UI, preview iframe, PDF rendering, and end-to-end workflows.
