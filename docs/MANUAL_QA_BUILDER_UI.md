# Manual QA — Builder UI/UX

Checklist for **visual and interaction** quality of the catalogue builder. Complements [MANUAL_QA_PRESENTATION_BUILDER.md](./MANUAL_QA_PRESENTATION_BUILDER.md) (functional QA).

This document is written for **non-developers** (QA, product, operations). You do not need to read code or use developer tools except optionally DevTools for dimension checks.

---

## Before you start

| Item | Detail |
|------|--------|
| **Purpose** | Confirm the builder looks professional, behaves predictably, and is ready for production use |
| **Prerequisites** | App running (desktop + API); at least one catalog with 20+ products (50+ preferred for pagination/DnD) |
| **Estimated time** | ~45 minutes for full pass; ~15 minutes for smoke (sections A, D, E) |
| **Record** | Catalogue ID, app version/branch, date, viewport size (e.g. 1440×900 desktop, 768×1024 tablet) |

### Recommended test order

1. **A** — Global layout (header, tabs, no sidebar preview)
2. **D** — Full preview workspace
3. **B** — Presentación tab
4. **C** — Productos tab (including DnD)
5. **E** — PDF export modal
6. **F** — Layout stability
7. **G** — List pages (Productos / Catálogos)
8. **H** — Responsive and edge cases

### Pass / fail recording template

Copy this table for your session notes:

| ID | Pass / Fail | Notes | Screenshot / log |
|----|-------------|-------|------------------|
| A-1 | | | |
| A-2 | | | |
| … | | | |

**Pass** = expected result matches. **Fail** = any item under "Bug if" occurs. Attach screenshot or short screen recording for failures.

---

## A. Global editor layout

### A-1. Stable header
| | |
|---|---|
| **Screen** | Catálogos → abrir catálogo → cualquier pestaña |
| **Action** | Observe header: back link, title, product count, Vista previa + Exportar PDF |
| **Expected** | Header sticky; actions aligned right; no jump on tab change |
| **Bug if** | Header disappears, overlaps content, or actions wrap unpredictably |
| **Send if fails** | Screenshot full width + console log |

### A-2. Tab panel min-height
| | |
|---|---|
| **Screen** | Builder — General / Presentación / Productos |
| **Action** | Switch General → Presentación → Productos |
| **Expected** | No large vertical collapse; tab content area keeps minimum height (~560px) |
| **Bug if** | Page height shrinks >200px between tabs with similar content |
| **Send if fails** | Screen recording of tab switches |

### A-3. Full preview workspace (replaces sidebar dock)
| | |
|---|---|
| **Screen** | Builder — any tab |
| **Action** | Click **Vista previa** in header |
| **Expected** | Builder tabs/content **hidden**; full-width preview workspace fills editor area; iframe uses max available height; **no** small right-column square |
| **Bug if** | Preview appears beside tabs in a narrow column; preview is a small square; builder tabs still visible beside preview |
| **Send if fails** | Screenshot full viewport + note viewport width |

### A-4. Full preview dimensions
| | |
|---|---|
| **Screen** | Builder — preview mode active |
| **Action** | Compare preview area height to window; scroll if needed |
| **Expected** | Preview body ≥480px tall; grows with viewport; toolbar fixed at top; iframe stable width (no horizontal jump) |
| **Bug if** | Preview constrained to ~420×480 sidebar size; iframe height changes between loading/ready |
| **Send if fails** | Screenshot + DevTools computed height of `.preview-workspace-frame` |

### A-5. Exit full preview / restore tab
| | |
|---|---|
| **Screen** | Builder — open preview from **Productos** tab |
| **Action** | Click **Salir de vista previa** (header or preview toolbar) |
| **Expected** | Preview closes; **Productos** tab restored (same tab as before); builder content visible |
| **Bug if** | Wrong tab after close; preview stuck open; blank workspace |
| **Send if fails** | Screen recording open → close |

### A-6. Layout shift between tabs (with preview closed)
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Switch tabs repeatedly without opening preview |
| **Expected** | No horizontal jump; header stable; tab list width stable |
| **Bug if** | Content shifts sideways or pager jumps vertically on tab switch |
| **Send if fails** | Screen recording |

---

## B. Presentation tab

### B-1. Mode selector cards
| | |
|---|---|
| **Screen** | Builder → Presentación |
| **Action** | Click Automático / Uniforme / Manual cards |
| **Expected** | Selected card has primary border/ring; description visible; uniform layout field when Uniforme |
| **Bug if** | Unclear which mode is active |

### B-2. Table pagination
| | |
|---|---|
| **Screen** | Builder → Presentación — catálogo con 50+ productos |
| **Action** | Change page; change rows/page (25/50/100) |
| **Expected** | Pager always visible (min height ~44px); stable table columns; page indicator updates |
| **Bug if** | Pager disappears; table height jumps between pages; horizontal scroll appears |
| **Send if fails** | Screenshots page 1 vs page 2 |

### B-3. Filters + pagination
| | |
|---|---|
| **Screen** | Builder → Presentación |
| **Action** | Go to page 3 → apply search or status filter |
| **Expected** | Page resets to 1; pager shows updated count; empty state if no matches |
| **Bug if** | Stays on page 3 with empty table; pager missing on empty filter |
| **Send if fails** | Filter used + pager screenshot |

### B-4. Bulk selection + pagination
| | |
|---|---|
| **Screen** | Builder → Presentación — filtered list spanning multiple pages |
| **Action** | Select items on page 1 → go to page 2 → use **Sel. todos filtrados** |
| **Expected** | Sticky bar shows count with **"incluye otras páginas"** when selection spans pages; selection persists across page changes |
| **Bug if** | Count resets silently on page change; no hint that selection is filter-scoped |
| **Send if fails** | Sticky bar text screenshot |

### B-5. Manual override expand row
| | |
|---|---|
| **Pre** | Catálogo en modo **manual** (guardado) |
| **Screen** | Builder → Presentación |
| **Action** | Click chevron on product row |
| **Expected** | Override select expands below row; table columns do not shift horizontally |
| **Bug if** | Extra column appears/disappears causing horizontal jump |
| **Send if fails** | Before/after expand screenshot |

### B-6. Diagnostics filter link
| | |
|---|---|
| **Screen** | Builder → Presentación — diagnostics with issues |
| **Action** | Click product name in Diagnóstico panel |
| **Expected** | Table filters to that product; banner **"Filtro diagnóstico activo"**; page resets to 1 |
| **Bug if** | No filter applied; wrong product shown |
| **Send if fails** | Diagnostic item clicked + table screenshot |

### B-7. Diagnostics severity badges
| | |
|---|---|
| **Screen** | Builder → Presentación → Diagnóstico |
| **Action** | Expand Crítico / Avisos / Información sections |
| **Expected** | Severity groups visually distinct (destructive / warning / info) |
| **Bug if** | All badges same color; unreadable contrast |

### B-8. Long product names
| | |
|---|---|
| **Screen** | Builder → Presentación |
| **Action** | Find product with long name |
| **Expected** | Name truncates with ellipsis; full name on hover (`title`) |
| **Bug if** | Name breaks column layout or overlaps adjacent cells |

### B-9. Layout registry
| | |
|---|---|
| **Screen** | Builder → Presentación — scroll to **Layouts registrados** |
| **Action** | Expand `<details>` |
| **Expected** | Collapsed by default; short intro text; grid of layout cards without overwhelming main flow |
| **Bug if** | Registry open by default pushing table off screen |

---

## C. Products tab

### C-1. Lines pagination + layout shift
| | |
|---|---|
| **Screen** | Builder → Productos — 50+ líneas |
| **Action** | Change page and rows/page |
| **Expected** | Pager stable height; SKU/name/action columns same width on every page |
| **Bug if** | Action buttons shift; columns resize between pages |
| **Send if fails** | Page 1 vs last page screenshots |

### C-2. DnD reorder (Products tab only)
| | |
|---|---|
| **Screen** | Builder → Productos |
| **Action** | Drag line via grip handle (not inputs/buttons); observe banner |
| **Expected** | Only grip handle initiates drag; **"Orden modificado sin guardar"** banner; limitation copy visible under **Líneas** title |
| **Bug if** | Drag starts when clicking input/button; no limitation copy |
| **Send if fails** | Network log if accidental drag |

### C-3. Save / discard DnD order
| | |
|---|---|
| **Screen** | Builder → Productos — after reorder |
| **Action** | **Guardar orden** → reload page; repeat with **Descartar** |
| **Expected** | Save persists order after reload; discard restores server order; preview marked stale after reorder |
| **Network (save)** | Exactly **one** `PATCH /api/v1/catalogs/{id}/items/reorder` with `{ "items": [{ "id": "<catalog-item-uuid>", "sort_order": N }, ...] }`; only changed lines included (not all 946); toast **Orden guardado**; **no** per-item `PATCH .../items/{id}` for `sort_order` |
| **Network (discard)** | No `items/reorder` request |
| **Bug if** | Order not saved; discard leaves dirty banner; multiple sequential item PATCH calls for order |
| **Send if fails** | Network tab screenshot (request count + reorder payload) |

### C-4. DnD within current page only
| | |
|---|---|
| **Screen** | Builder → Productos — page 2 of lines |
| **Action** | Reorder on page 2; save |
| **Expected** | Only relative order within page changes in global list; cannot drag to another page; reorder payload contains only the swapped item IDs (e.g. 2 entries with `sort_order` 50 and 51) |
| **Bug if** | Items jump to wrong global positions |
| **Send if fails** | Item IDs + sort_order before/after |

### C-5. DnD API failure (if reproducible)
| | |
|---|---|
| **Screen** | Builder → Productos |
| **Action** | Reorder lines; stop API (`docker compose stop api`) or block network; click **Guardar orden** |
| **Expected** | Spanish error toast (e.g. **Catálogo no encontrado** or generic **No se pudo guardar el orden…**); dirty banner **remains**; user can retry after API is back. Reorder is **atomic** (all-or-nothing) — no partial save |
| **Bug if** | Silent failure; banner cleared incorrectly; partial order persisted |
| **Send if fails** | Network failures + toast screenshot |

### C-6. DnD disabled while saving
| | |
|---|---|
| **Screen** | Builder → Productos |
| **Action** | Save order with slow network |
| **Expected** | Grip handles disabled during save; **Guardando…** on button |
| **Bug if** | Can drag during save |

### C-7. Variant search pagination
| | |
|---|---|
| **Screen** | Builder → Productos — panel Añadir variante |
| **Action** | Search with many results |
| **Expected** | Paginated results; page resets when search changes |
| **Bug if** | Only first page with no navigation |

---

## D. Full preview workspace

### D-1. Preview states
| | |
|---|---|
| **Screen** | Builder — preview mode |
| **Action** | Open preview; click **Regenerar preview**; edit layout (stale); simulate API error |
| **Expected** | Badges: Sin preview / Regenerando… / Actualizada / Desactualizada / Error al cargar; stale banner when desactualizada; error panel with **Reintentar** |
| **Bug if** | Blank iframe on error without retry; dimensions jump between states |
| **Send if fails** | Each state screenshot |

### D-2. Pending changes badge
| | |
|---|---|
| **Screen** | Builder — change layout mode without saving |
| **Action** | Open preview |
| **Expected** | **Cambios pendientes** badge; no auto-regenerate on every keystroke |
| **Bug if** | Aggressive auto-refresh; missing pending badge |

### D-3. Preview toolbar actions
| | |
|---|---|
| **Screen** | Builder — preview mode |
| **Action** | Use **Regenerar preview**, **Exportar PDF**, **Salir de vista previa** |
| **Expected** | All actions work; helper text visible under title; export opens preflight dialog if needed |
| **Bug if** | Missing export in preview toolbar; button still says only "Regenerar" without "preview" |

### D-4. Export warnings from preview
| | |
|---|---|
| **Screen** | Builder — preview with export warnings badge |
| **Action** | Click **N avisos exportación** |
| **Expected** | Preview closes; **Presentación** tab opens |
| **Bug if** | Tab changes but preview still hides content |

### D-5. Preview after tab change (manual)
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Open preview from General → close → switch to Presentación → open preview again |
| **Expected** | Preview works; returns to Presentación on close |
| **Bug if** | Broken state or wrong tab restore |

### D-6. PDF / catalogue visual comparison (manual only)
| | |
|---|---|
| **Screen** | Builder — preview mode |
| **Action** | Visually compare preview pages to exported PDF (layouts, images, prices) |
| **Expected** | Preview reasonably matches PDF output |
| **Bug if** | Major layout/product mismatches |
| **Send if fails** | Side-by-side preview + PDF screenshots |
| **Note** | Cannot be fully automated — mark pass/fail manually |

---

## E. PDF export modal

### E-1. Integrated dialog (no native confirm)
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Export with warnings/fallbacks |
| **Expected** | Radix **ExportPdfDialog**; severity badges; ack checkbox for critical |
| **Bug if** | `window.confirm` appears for PDF export in builder |
| **Send if fails** | Screenshot of dialog |

### E-2. Stale preview warning
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Export after unsaved presentation config or stale preview |
| **Expected** | Stale banner + **Regenerar preview** + **Exportar de todos modos** |
| **Bug if** | Silent export without warning |

### E-3. Export modal states
| | |
|---|---|
| **Screen** | Builder — export dialog open |
| **Action** | Cancel; confirm critical export; export while loading |
| **Expected** | Cancel closes without export; critical requires checkbox; buttons disabled while generating |
| **Bug if** | Double export; modal leaves page scrolled incorrectly |

### E-4. Builder delete confirmation
| | |
|---|---|
| **Screen** | Builder → General |
| **Action** | Click **Eliminar** |
| **Expected** | Radix dialog (not native `confirm`) |
| **Bug if** | Native browser confirm in builder |

---

## F. Layout shift / stability

### F-1. Filter application (Presentation)
| | |
|---|---|
| **Screen** | Builder → Presentación |
| **Action** | Apply filters rapidly |
| **Expected** | Column widths stable; pager stays in place |
| **Bug if** | Horizontal scrollbar appears/disappears abruptly |

### F-2. Loading skeleton
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Hard reload catalog editor |
| **Expected** | Skeleton matches final layout padding; minimal shift when data loads |
| **Bug if** | Large layout shift when catalog loads |

### F-3. Enter/exit preview layout shift
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Open and close preview several times |
| **Expected** | Smooth transition; no horizontal page jump; header unchanged |
| **Bug if** | Page scroll position lost badly or content flashes |

### F-4. Export modal open/close
| | |
|---|---|
| **Screen** | Builder |
| **Action** | Open and close export dialog |
| **Expected** | No workspace resize jump (Radix portal) |
| **Bug if** | Main content width changes when modal opens |

---

## G. List pages

### G-1. Products page pagination
| | |
|---|---|
| **Screen** | Productos (list) |
| **Action** | Paginate; change search |
| **Expected** | Client pagination with stable pager; page resets on search |
| **Bug if** | Missing pager; layout jump between pages |

### G-2. Catalogs page pagination
| | |
|---|---|
| **Screen** | Catálogos (list) |
| **Action** | Paginate; filter/search if available |
| **Expected** | Same pager pattern as Products |
| **Bug if** | Inconsistent pager UI |

---

## H. Responsive & edge cases

### H-1. Narrow viewport + full preview
| | |
|---|---|
| **Screen** | Builder — width <768px |
| **Action** | Open full preview |
| **Expected** | Preview toolbar wraps; iframe still usable; no horizontal overflow on body |
| **Bug if** | Clipped controls or unusable preview |

### H-2. Products without images
| | |
|---|---|
| **Screen** | Builder → Presentación / preview |
| **Action** | Find product flagged sin imagen in diagnostics |
| **Expected** | Fallback visible in preview/diagnostics; not noisy in table |
| **Bug if** | Broken layout in preview |

### H-3. Empty states
| | |
|---|---|
| **Screen** | Builder — empty catalog or empty filter |
| **Action** | Open each tab / apply filter with no matches |
| **Expected** | Clear empty message; pager shows 0 de 0 where applicable |
| **Bug if** | Broken table or missing empty copy |

### H-4. Loading states
| | |
|---|---|
| **Screen** | Builder → Presentación / preview |
| **Action** | Observe loading spinners |
| **Expected** | Loading overlays/skeletons without layout collapse |
| **Bug if** | Content flash or zero-height containers |

---

## I. Known limitations (documented, not bugs)

| Item | Notes |
|------|--------|
| **Catalogs list delete** | [`CatalogsPage`](../apps/desktop/src/pages/CatalogsPage.tsx) still uses native `confirm()` — out of builder scope |
| **DnD scope** | Reorder only on **Productos** tab lines; not Presentation masters or categories |
| **DnD page scope** | Drag reorder applies within **current page** of lines only |
| **Sequential PATCH save** | Saving order sends N requests; slow for 50+ lines — see **API-5** in [BUILDER_BACKEND_DEPENDENCIES.md](./BUILDER_BACKEND_DEPENDENCIES.md) |
| **Client pagination** | All paginated lists are client-side — see **API-3/API-4** in [BUILDER_BACKEND_DEPENDENCIES.md](./BUILDER_BACKEND_DEPENDENCIES.md) |

---

## Backend dependencies (not UI-validated here)

See **[BUILDER_BACKEND_DEPENDENCIES.md](./BUILDER_BACKEND_DEPENDENCIES.md)** for the full actionable list (API-1 through API-8) for the backend agent.
