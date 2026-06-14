# UX30 Phase 2D — Shared List Primitives QA Report

| Field | Value |
|---|---|
| **Task ID** | `APP-PLATFORM-UX-3.0-PHASE-2D` |
| **Agent** | 1A — Catalogue Builder UI/UX |
| **Mode** | QA (read-only) |
| **Date** | 2026-06-14 |
| **Environment** | `npm run dev:web --prefix apps/desktop` → `http://127.0.0.1:5173` |
| **API** | `http://127.0.0.1:8000/api/v1` (Docker) |
| **Evidence target** | `EVID-UX30-P2D-001` (pending control-plane index) |

## Verdict: **QA_PASS_WITH_NOTES**

All mandatory viewport checks that could be exercised pass. Shared `responsive-data-card*` primitives render correctly on Products and Suppliers profiles; legacy list BEM shells (`import-profile-card`, `price-diff-card`, `product-master-card` article) are **absent** at runtime. Breakpoint policy holds (cards ≤1023, table ≥1024). Price Lists collapsible panel uses `responsive-collapsible-panel__toggle`. Two carry-over data limitations from Phase 2C (price diff runtime) plus variant sheet not exercised in seed. No P0/P1 defects.

---

## Baseline commands

| Command | Result |
|---|---|
| `npm test --prefix apps/desktop -- productsPageResponsive suppliersPageResponsive priceListsPageResponsive responsiveListPrimitives useDataViewMode` | **31/31 PASS** |
| `npm test --prefix apps/desktop` (full suite, post-implementation) | **405/405 PASS** |
| `npm run build --prefix apps/desktop` | **PASS** (Agent 1B report) |

---

## Viewport matrix — `/products`

| Check | 360 | 640 | 1023 | 1024 |
|---|---|---|---|---|
| `responsive-data-card` rendered | ✅ (6) | ✅ (6) | ✅ (6) | — |
| `responsive-data-card-list__items` | ✅ | ✅ | ✅ | — |
| Sort bar (`product-master-card-list`) | ✅ | ✅ | ✅ | — |
| Legacy `product-master-card` article shell | ✅ 0 | ✅ 0 | ✅ 0 | ✅ 0 |
| Table mode | — | — | — | ✅ (6 rows) |
| Horizontal overflow | ✅ none | ✅ | ✅ | ✅ |

---

## Viewport matrix — `/suppliers` (profiles panel)

| Check | 360 drill-down | 1024 two-column |
|---|---|---|
| `responsive-data-card` on profiles | ✅ (1) | — |
| Legacy `import-profile-card` | ✅ 0 | ✅ 0 |
| Table mode for profiles | — | ✅ (1 row) |
| Profiles panel present | ✅ | ✅ |

---

## Viewport matrix — `/price-lists`

| Check | 360 | 1024 |
|---|---|---|
| `responsive-collapsible-panel__toggle` | ✅ `aria-expanded=false` → true on click | — (absent, expected) |
| Legacy `price-lists-toolbar__filter-toggle` | ✅ 0 | ✅ 0 |
| Filters panel visible @1024 | — | ✅ |
| Compare button touch ≥44px | ✅ 44px | ✅ |
| Filter toggle touch ≥44px | ✅ 44px | — |
| Diff `responsive-data-card` runtime | ⚠️ blocked (1 price list) | ⚠️ |

---

## Manual QA method

- **Browser:** Chrome DevTools MCP (`emulate` viewport + `evaluate_script` DOM counts)
- **Measurements:** `.responsive-data-card`, `.responsive-data-card-list__items`, legacy BEM selectors, `table` presence, `aria-expanded`, button heights
- **Interactions:** Supplier drill-down @360; filter toggle expand @360; supplier select @1024

### Screenshots

| File | Description |
|---|---|
| `screenshots/products-360-cards.png` | Products — shared cards @360 |
| `screenshots/products-640-cards.png` | Products — cards @640 |
| `screenshots/products-1023-cards.png` | Products — cards @1023 boundary |
| `screenshots/products-1024-table.png` | Products — desktop table @1024 |
| `screenshots/suppliers-360-profiles-drilldown.png` | Suppliers — profile card @360 drill-down |
| `screenshots/suppliers-1024-two-column-table.png` | Suppliers — profiles table @1024 |
| `screenshots/price-lists-360-toolbar-collapsed.png` | Price Lists — collapsible toggle collapsed |
| `screenshots/price-lists-360-filters-expanded.png` | Price Lists — filters panel expanded |
| `screenshots/price-lists-1024-desktop-toolbar.png` | Price Lists — desktop toolbar, filters always visible |

---

## Non-blocking notes

| ID | Sev | Issue |
|---|---|---|
| P2D-N1 | P2 | Variant expand sheet + focus restore not runtime-tested — no multi-variant master visible in current products seed @360. Covered by unit tests (`productsPageResponsive` focus helpers). |
| P2D-N2 | P2 | Price diff `responsive-data-card` rows and change-type badges not runtime-verified — only **1** price list in DB (same constraint as P2C-N1). Unit tests cover markup + `responsive-data-card--only_a` modifier. |
| P2D-N3 | P2 | Error/retry states not runtime-tested on migrated surfaces. |

---

## Scope confirmation

- QA read-only; no product or control doc edits.
- Categories tree out of scope (unchanged).
- `ProductVariantExpandSheet` behavior unchanged (not opened in this pass).

---

## Recommendation

**ACCEPT** for control-plane validation closure. Release Phase 2D locks after registry update. Defer P2D-N1–N3 as non-blocking P2 follow-ups (same class as P2B-N1/N2, P2C-N1/N2).
