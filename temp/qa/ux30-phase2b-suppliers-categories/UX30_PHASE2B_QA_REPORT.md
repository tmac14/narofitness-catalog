# UX30 Phase 2B — Suppliers + Categories QA Report

| Field | Value |
|---|---|
| **Task ID** | `APP-PLATFORM-UX-3.0-PHASE-2B` |
| **Agent** | 1A — Catalogue Builder UI/UX |
| **Mode** | QA (read-only) |
| **Date** | 2026-06-13 |
| **Environment** | `npm run dev:web --prefix apps/desktop` → `http://127.0.0.1:5173` |
| **API** | `http://127.0.0.1:8000/api/v1` (Docker, 1 supplier, seeded category tree) |
| **Evidence target** | `EVID-UX30-P2B-001` (pending control-plane index) |

## Verdict: **QA_PASS_WITH_NOTES**

All mandatory checklist items pass at required viewports. Two non-blocking notes recorded (P2). No P0/P1 defects.

---

## Baseline commands

| Command | Result |
|---|---|
| `npm test --prefix apps/desktop -- suppliersPageResponsive categoriesPageResponsive useDataViewMode` | **12/12 PASS** |
| `npm run build --prefix apps/desktop` | **PASS** |

**Out of scope:** `catalogEditorHeaderRouteActions.test.tsx` (Chrome 3.1 track) — not evaluated for P2B gate.

---

## Viewport matrix

Legend: ✅ pass · ⚠️ note · — not applicable

### Suppliers (`/suppliers`)

| Check | 360 | 640 | 1023 | 1024 |
|---|---|---|---|---|
| Drill-down: select supplier → profiles panel | ✅ | ✅ | ✅ | — (two-panel) |
| Back control `← Proveedores` on narrow | ✅ | ✅ | ✅ | — |
| Back preserves selection (`aria-pressed="true"`) | ✅ | ✅ | ✅ | — |
| Profiles render as **cards** (not table) | ✅ (1 card) | ✅ | ✅ | — |
| Two-column layout + profiles **table** | — | — | — | ✅ |
| Supplier / back / Import CTA touch ≥44px | ✅ (44px) | ✅ | ✅ | ✅ |
| No hover-only primary actions | ✅ overflow N/A; buttons exposed | ✅ | ✅ | ✅ |
| Empty state (no selection) | — | — | — | ✅ "Seleccione un proveedor" |
| Import link from empty profiles | ✅ (code + link present) | ✅ | ✅ | ✅ |
| Horizontal overflow | ✅ none | ✅ | ✅ | ✅ |

### Categories (`/categories`)

| Check | 360 | 640 | 1023 | 1024 |
|---|---|---|---|---|
| Parent accordion **default-collapsed** (<640) | ✅ (2 collapsed toggles) | — | — | — |
| Parent accordion **default-expanded** (≥640) | — | ✅ (2 expanded) | ✅ | ✅ |
| Expand/collapse toggle (`aria-expanded`) | ✅ Cardio false→true | ✅ | ✅ | ✅ |
| Overflow menu (Editar / + Hijo / Eliminar) | ✅ | ✅ | ✅ | ✅ |
| Menu trigger touch ≥44px | ✅ (44×44) | ✅ | ✅ | ✅ |
| Editar → form populated + in viewport | ✅ "Cardio" | — | — | — |
| Eliminar → confirmation dialog | ✅ | — | — | — |
| Dialog footer buttons ≥44px | ✅ Cancelar/Eliminar 44px | — | — | — |
| Form submit/cancel ≥44px | ✅ Crear/Guardar/Cancelar 44px | ✅ | ✅ | ✅ |
| Deep tree, no horizontal overflow | ✅ scrollWidth=360 | ✅ | ✅ | ✅ |
| Long titles truncate acceptably | ✅ `.truncate` on long Musculación children | ✅ | ✅ | ✅ |
| No inline `sm:` hover-only row buttons | ✅ menu-only (unit + visual) | ✅ | ✅ | ✅ |

---

## Manual QA method

- **Browser:** Cursor IDE browser MCP + CDP `Emulation.setDeviceMetricsOverride`
- **Measurements:** `getBoundingClientRect().height`, DOM queries for `table`, `.import-profile-card`, `aria-*`
- **Interactions:** `browser_click` on overflow menu, Editar, Eliminar (cancelled — no data mutation)

### Screenshots

| File | Description |
|---|---|
| `screenshots/suppliers-360-profiles-drilldown.png` | Mobile drill-down — profile card + back affordance |
| `screenshots/suppliers-1024-two-column-table.png` | Desktop two-column layout with profiles table |
| `screenshots/categories-360-deep-tree.png` | Mobile category tree, collapsed parents, overflow menus |

---

## Checklist detail

### Suppliers

1. **360px drill-down** — Select FDL Fitness → profiles panel with card "Tarifa mayorista PDF"; back button labeled "Proveedores" with arrow; back restores list with `aria-pressed="true"`.
2. **640 / 1023 cards** — `tables: 0`, `cardItems: 1` after selection; drill-down + back behave identically to 360.
3. **1024+ table** — Grid `336.5px 336.5px` (two columns); `tables: 1`, `tableRows: 1`; no back button (master-detail simultaneous); supplier `aria-pressed="true"` on select.
4. **Touch** — Supplier button, back, Import CTA, retry buttons use `min-h-11` (44px measured).
5. **Empty / Import** — Desktop empty profiles prompt before selection; Import link reachable from header and empty profiles CTA.

### Categories

1. **<640 collapsed** — On fresh load at 360: Cardio + Musculación toggles `aria-expanded="false"`; children hidden until expand.
2. **≥640 expanded** — At 640/1024: parent toggles expanded by default; "Air Bike" visible without manual expand.
3. **Overflow menu** — Radix dropdown exposes Editar, + Hijo, Eliminar (no inline row buttons).
4. **Editar** — Populates `#cat-name` with "Cardio"; heading switches to "Editar categoría"; name field in viewport (`nameInViewport: true`).
5. **Eliminar** — Dialog "¿Eliminar categoría?" with Cancelar/Eliminar at 44px; cancelled without delete.
6. **360 deep tree** — All parents expanded programmatically: `scrollWidth === clientWidth === 360`; long names (e.g. "Soportes y Mancuerneros") truncate via `.truncate`.
7. **Form touch** — Crear/Guardar/Cancelar measured 44px height.

---

## Defects

| ID | Severity | Summary | Repro | Status |
|---|---|---|---|---|
| P2B-N1 | **P2** | Profiles panel may briefly show "Sin perfiles" before API resolves at desktop | `/suppliers` @1024 → click supplier → snapshot during first ~500ms | Cosmetic / loading race; resolves to table |
| P2B-N2 | **P2** | Error/retry states not disconnect-tested | Would require stopping API mid-fetch | Code review confirms `ErrorState` + `min-h-11` retry buttons exist; not runtime-verified |

**P0 / P1:** none.

---

## Binding compliance

| Decision | Result |
|---|---|
| **UX30-D6** (cards ≤1023, table ≥1024) | ✅ Suppliers profiles |
| **UX30-D1** breakpoints (640 tablet, 1024 desktop) | ✅ Matches `useDataViewMode` + `classifyPlatformWidth` |
| **UX30-D4** (no hover-only actions) | ✅ Category row actions via overflow menu |
| **44px touch targets** | ✅ Measured on primary controls |

---

## Scope confirmation

- **Read-only** — no product files edited.
- **Out of scope exercised:** catalog-builder, Chrome 3.1, coordination docs, Phase 2C authorization.
- **Phase 2C:** not authorized by this report.

---

## Recommendation for control plane

Accept P2B validation; index `EVID-UX30-P2B-001` from this artifact; release P2B locks; proceed to Phase 2C planning gate. Optional follow-up: add skeleton or retain previous profiles during refetch to address P2B-N1.

---

## Agent sign-off

**Agent 1A** · QA mode · `QA_PASS_WITH_NOTES` · 2026-06-13
