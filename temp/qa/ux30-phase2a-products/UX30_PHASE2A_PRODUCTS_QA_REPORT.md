# UX30 Phase 2A — Products Responsive QA Report

**Task ID:** `APP-PLATFORM-UX-3.0-PHASE-2A-PRODUCTS-QA`  
**Agent:** 1A (read-only QA)  
**Date:** 2026-06-03  
**Verdict:** **`UX30_PHASE2A_PRODUCTS_QA_PASS_WITH_NOTES`**

---

## 1. Estado

| Result | Condition |
|--------|-----------|
| ~~UX30_PHASE2A_PRODUCTS_QA_PASS~~ | Blocked by one medium a11y note on Sheet focus return |
| **UX30_PHASE2A_PRODUCTS_QA_PASS_WITH_NOTES** | **All UX30-D6 responsive/touch criteria met; Sheet focus-restore pending** |
| ~~UX30_PHASE2A_PRODUCTS_QA_FAIL~~ | Not applicable — no blocking responsive/table/cards regressions |

---

## 2. Tests y build

| Command | Result |
|---------|--------|
| `npm run test --prefix apps/desktop` | **PASS** — 47 files, **362/362** tests (includes `productsPageResponsive.test.tsx`) |
| `npm run build --prefix apps/desktop` | **PASS** — Vite production build completed |

---

## 3. Tabla de resultados por viewport

| Viewport | Modo | Dual cards+table | Overflow H | Small targets (<44px) | PDF triggers | Screenshot |
|----------|------|------------------|------------|----------------------|--------------|------------|
| 360×800 | **cards** | No | No | 0 | 6 | `products-360x800-cards.png` |
| 390×844 | **cards** | No | No | 0 | 6 | `products-mobile-390x844-cards.png` |
| 640×360 | **cards** | No | No | 0 | 6 | `products-640x360-cards.png` |
| 768×1024 | **cards** | No | No | 0 | 6 | `products-768x1024-cards.png` |
| 1023×768 | **cards** | No | No | 0 | 6 | `products-1023x768-cards.png` |
| 1024×768 | **table** | No | No | n/a (desktop row chrome) | 6 | `products-1024x768-table.png` |
| 1440×900 | **table** | No | No | n/a | 6 | `products-1440x900-table.png` |

JSON per viewport: `viewport-*.json` · Summary: `viewport-metrics-summary.json`

**Breakpoint:** cards at ≤1023px, table at ≥1024px — boundary verified (`1023` cards-only, `1024` table-only).

---

## 4. Cards / table exclusivas

| Platform | Expected | Observed | Pass |
|----------|----------|----------|------|
| Mobile & tablet (<1024) | Cards only, no desktop table | `.product-master-card-list` visible; `.product-list-table` hidden | ✅ |
| Desktop & wide (≥1024) | Table only, no card list | `.product-list-table` visible; `.product-master-card` count 0 | ✅ |
| Dual mode | Never both | `dualMode: false` at all 7 viewports | ✅ |
| Mini-tabla in mobile Sheet | Never | `nestedVariantTable: false` in Sheet | ✅ |

---

## 5. Sheet y accesibilidad (multi-variante, mobile 390×844)

| Check | Result |
|-------|--------|
| Trigger opens light Sheet | ✅ Dialog `"Barras Crossfit"` |
| Variants as cards/list | ✅ 8× `.product-variant-card`; no `.product-variants-panel__table` in Sheet |
| Referencia, precio, PDF, Ver ficha | ✅ 8 PDF buttons + 8 ficha links in Sheet |
| Initial focus | ✅ `"Cerrar variantes"` on open |
| Tab within Sheet | ✅ Tab → first `"Ver origen PDF"` inside dialog |
| Escape closes | ✅ Sheet dismissed |
| **Focus return to trigger** | **❌ Active element → `BODY` (not trigger)** |
| Close button closes | ✅ `"Cerrar variantes"` dismisses Sheet |
| **Focus return after close button** | **❌ Active element → `BODY`** |

Details: `sheet-a11y.json` · Screenshot: `products-sheet-390x844-open.png`

---

## 6. Touch targets

Measured selectors on card mode (390×844, 360×800, 640×360, 768×1024, 1023×768):

- `.product-master-card__variants-btn`
- `.product-master-card__menu-btn`
- `.product-master-card-list__sort-select` / `__sort-dir`
- `button[aria-label="Ver origen PDF"]`

**Result:** **0 targets below 44px** at all measured mobile/tablet viewports.

Sheet interactive controls (close, PDF, Ver ficha): **0 below 44px**.

No hover-only primary actions observed; all actions exposed as visible buttons/menus.

---

## 7. Overflow horizontal

| Viewport | `scrollWidth` vs `innerWidth` | Overflow |
|----------|-------------------------------|----------|
| All 7 mandatory viewports | Equal (no +1px slack) | **None detected** |

---

## 8. Búsqueda / ordenación / paginación / acciones / source pages

| Feature | Result | Notes |
|---------|--------|-------|
| Búsqueda | ✅ | `"Barras Crossfit"` → 3 cards; `"Barras"` → 11; `"Crossfit"` alone → empty state |
| Ordenación + dirección | ✅ | Card sort controls; toggle ascendente/descendente changes first product |
| Paginación | ✅ | 534 products, 50/page; next → `51–100 de 534` |
| Ficha single-variant | ✅ | Menú → Ver ficha → `/products/b5cf4dd2-…` |
| Ficha multi-variant (Sheet) | ✅ | `Ver ficha` links present (`/products/ca44024f-…`) |
| PDF / source page | ✅ | `Ver origen PDF` on every card row and every Sheet variant |
| Empty state | ✅ | `"Sin productos"` / `"No hay resultados para su búsqueda."` |
| Error state | — | Not provoked (read-only; no API fault injection) |
| Loading | ✅ (observed) | Brief load on reload before cards render |

Details: `transversal-smoke.json`

---

## 9. Regresión desktop (1024×768, 1440×900)

| Check | Result |
|-------|--------|
| Table exclusive | ✅ No cards |
| Sortable column headers | ✅ Producto, Referencia, Marca, Categoría, PVP |
| Inline variant expansion | ✅ Expand button opens `.product-variants-panel` with `.product-variants-panel__table` (desktop path — not Sheet) |
| No Sheet on desktop expand | ✅ `sheetOpen: false` when expanding row |
| PDF actions in table | ✅ 6 triggers visible |
| Visual regression | ✅ No evident layout break (see screenshots) |

Desktop inline expand: `products-1024x768-inline-expand.png`

---

## 10. Defectos

### P2A-SHEET-001 — Sheet close does not restore focus to trigger

| Field | Value |
|-------|-------|
| **Severity** | Medium (a11y / WCAG focus management) |
| **Area** | `ProductVariantExpandSheet` — focus restore on dismiss |
| **Repro** | 390×844 → Products → click `"Mostrar N variantes de …"` → Sheet opens with focus on `"Cerrar variantes"` → press **Escape** OR click **Cerrar variantes** → Sheet closes → `document.activeElement` is `BODY`, not the variants trigger button |
| **Expected** | Focus returns to the button that opened the Sheet |
| **Impact** | Keyboard/screen-reader users lose place in list; does not block touch-first card UX or UX30-D6 layout policy |

---

## 11. Artefactos generados

All under `temp/qa/ux30-phase2a-products/`:

| Artifact | Purpose |
|----------|---------|
| `UX30_PHASE2A_PRODUCTS_QA_REPORT.md` | This report |
| `viewport-metrics-summary.json` | Aggregated viewport metrics |
| `viewport-360x800.json` … `viewport-1440x900.json` | Per-viewport DOM probes |
| `sheet-a11y.json` | Sheet open/close/focus metrics |
| `transversal-smoke.json` | Search/sort/pagination/ficha smoke |
| `measure-products.mjs` | Reusable DOM measurement expression |
| `products-*-{cards,table}.png` | Screenshots (7 viewports + sheet + inline expand) |

---

## 12. Confirmación read-only

- **No application code, tests, CSS, config, or docs were modified.**
- Only artifacts written under `temp/qa/ux30-phase2a-products/`.
- ProductDetail, catalog builder, Import, backend, API, and PDF export were not touched.
- No defects were fixed during this session.

---

## 13. Recomendación

**Validar Phase 2A** (`UX30-D6` responsive split cards/table, Sheet ligero con variant cards, desktop table preserved) **con nota a Agent 1B:**

1. Implement focus restore to the variants trigger on Sheet close (Escape + close button), e.g. Radix `onCloseAutoFocus` prevention + manual `triggerRef.focus()`.
2. Optional follow-up: confirm desktop row-action touch targets if tablet-with-touch at 1024+ becomes a supported scenario.

**No se recomienda bloquear Phase 2A** por P2A-SHEET-001 alone; el criterio principal responsive/touch-first está cumplido.
