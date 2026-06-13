# P2A Sheet Focus Revalidation Report

**Task ID:** `APP-PLATFORM-UX-3.0-PHASE-2A-SHEET-FOCUS-REVALIDATION`  
**Agent:** 1A (read-only QA)  
**Date:** 2026-06-03  
**Verdict:** **`P2A_SHEET_FOCUS_REVALIDATION_PASS`**

---

## 1. Estado

**`P2A_SHEET_FOCUS_REVALIDATION_PASS`** — P2A-SHEET-001 is corrected in runtime. Focus returns to the exact variants trigger after Escape and after the “Cerrar variantes” button on all tested masters.

---

## 2. Tests y build

| Command | Result |
|---------|--------|
| `npm run test --prefix apps/desktop` | **PASS** — 47 files, **367/367** tests |
| `npm run build --prefix apps/desktop` | **PASS** |

Fix under test: `restoreVariantSheetFocus` + `onCloseAutoFocus` in `ProductVariantExpandSheet.tsx`, trigger captured via `event.currentTarget` in `ProductMasterCard.tsx`.

---

## 3. Foco inicial

| Check | Result |
|-------|--------|
| Open Sheet via “Mostrar 8 variantes de Barras Crossfit” | ✅ |
| `document.activeElement` on open | **`button[aria-label="Cerrar variantes"]`** ✅ |

---

## 4. Cierre con Escape

| Check | Result |
|-------|--------|
| Sheet disappears | ✅ |
| `activeElement ===` opening trigger (same DOM node) | ✅ |
| `activeElement` is not `BODY` | ✅ |
| Trigger aria-label | `Mostrar 8 variantes de Barras Crossfit` |

---

## 5. Cierre con botón

| Check | Result |
|-------|--------|
| Reopen same master | ✅ |
| Click **Cerrar variantes** | ✅ |
| `activeElement ===` opening trigger (same DOM node) | ✅ |
| `activeElement` is not `BODY` | ✅ |

---

## 6. Secuencia entre dos masters

| Master | Close method | Focus returns to own trigger |
|--------|--------------|------------------------------|
| Barras Crossfit - NEXO | Escape | ✅ `Mostrar 6 variantes de Barras Crossfit - NEXO` |
| Saco Gusano | Cerrar variantes | ✅ `Mostrar 5 variantes de Saco Gusano` |

Each Sheet restored focus to **its own** trigger, not a stale trigger from a prior open.

---

## 7. Focus trap

During Sheet open (Saco Gusano, 5 variants):

- 6 sequential focus steps sampled (close → PDF → Ver ficha → …)
- **All steps:** `dialog.contains(document.activeElement) === true` ✅
- Focus did not escape to page chrome or `BODY` while Sheet was open ✅

---

## 8. Smoke cards/table y contenido Sheet

| Smoke | 390×844 | 1024×768 |
|-------|---------|----------|
| View mode | cards only (6 cards) | table only (0 cards) |
| Dual mode | none | none |
| Sheet variant cards | 5× `.product-variant-card` | — |
| Mini-tabla in Sheet | none | — |
| PDF in Sheet | 5 visible | — |
| Ver ficha in Sheet | 5 visible | — |

Details: `smoke-minimal.json`

---

## 9. Defectos encontrados

**None.** P2A-SHEET-001 is **resolved**.

---

## 10. Artefactos generados

All under `temp/qa/ux30-phase2a-products/focus-revalidation/`:

| File | Purpose |
|------|---------|
| `P2A_SHEET_FOCUS_REVALIDATION_REPORT.md` | This report |
| `focus-results.json` | Focus test metrics (initial, Escape, button, two masters, trap) |
| `smoke-minimal.json` | Cards/table + Sheet content smoke |
| `smoke-1024-table.png` | Desktop table-only screenshot |

---

## 11. Confirmación read-only

- No application code, tests, CSS, config, or docs were modified.
- Only QA artifacts written under the allowed path.
- ProductDetail, catalog, Import, backend, API, and PDF were not touched.

---

## 12. Recomendación

1. **Close P2A-SHEET-001** — revalidation PASS.
2. **Upgrade Phase 2A QA status** from `UX30_PHASE2A_PRODUCTS_QA_PASS_WITH_NOTES` to **`UX30_PHASE2A_PRODUCTS_QA_PASS`**.
3. **Recommend releasing Phase 2A locks** (`LOCK-UX30-P2A-PRODUCTS` or equivalent) — responsive cards/table split and Sheet focus management both verified in runtime.
