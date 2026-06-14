# UX30 Phase 2C — Price Lists QA Report

| Field | Value |
|---|---|
| **Task ID** | `APP-PLATFORM-UX-3.0-PHASE-2C` |
| **Agent** | 1A — Catalogue Builder UI/UX |
| **Mode** | QA (read-only) |
| **Date** | 2026-06-13 |
| **Environment** | `npm run dev:web --prefix apps/desktop` → `http://127.0.0.1:5173` |
| **API** | `http://127.0.0.1:8000/api/v1` (Docker; **1** price list seeded) |
| **Evidence target** | `EVID-UX30-P2C-001` (pending control-plane index) |

## Verdict: **QA_PASS_WITH_NOTES**

All mandatory checklist items that could be exercised at required viewports pass. Diff results cards/table rendering and change-type badges were **not** runtime-tested because the environment has only one importable price list (API returns 422 for self-diff). Policy and markup are covered by unit tests (12/12 PASS). Two non-blocking notes recorded (P2). No P0/P1 defects.

---

## Baseline commands

| Command | Result |
|---|---|
| `npm test --prefix apps/desktop -- priceListsPageResponsive useDataViewMode` | **12/12 PASS** |
| `npm run build --prefix apps/desktop` | **PASS** |

---

## Viewport matrix — `/price-lists`

Legend: ✅ pass · ⚠️ note (blocked by data) · — not applicable

| Check | 360 | 640 | 1023 | 1024 |
|---|---|---|---|---|
| Page heading "Comparar tarifas" | ✅ | ✅ | ✅ | ✅ |
| Compare button visible | ✅ | ✅ | ✅ | ✅ |
| Compare / selects touch ≥44px | ✅ (44px) | ✅ | ✅ | ✅ |
| Filter toggle (mobile only) | ✅ collapsed `aria-expanded=false` | — | — | — |
| Filters expanded by default (≥640) | — | ✅ panel visible | ✅ | ✅ |
| Filter toggle absent (≥640) | — | ✅ | ✅ | ✅ |
| Filters panel opens on toggle (360) | ✅ checkbox + direction + min % | — | — | — |
| Checkbox label row touch ≥44px | ✅ label 44px | ✅ | ✅ | ✅ |
| Horizontal overflow | ✅ none | ✅ | ✅ | ✅ |
| Empty state before compare | ✅ "Sin comparación" | ✅ | ✅ | ✅ |
| Diff results as **cards** (≤1023) | ⚠️ no 2nd list | ⚠️ | ⚠️ empty after compare | — |
| Diff results as **table** (≥1024) | — | — | — | ⚠️ no 2nd list |
| Change-type badge on cards | ⚠️ unit tests only | ⚠️ | ⚠️ | — |
| Export CSV link when A+B selected | ⚠️ needs 2 lists | ⚠️ | ⚠️ | ⚠️ |
| Scroll container max-h ~55vh | ⚠️ not exercised (no rows) | ⚠️ | ⚠️ | ⚠️ |

---

## Manual QA method

- **Browser:** Chrome DevTools MCP (`emulate` viewport + `evaluate_script` measurements)
- **Measurements:** `getBoundingClientRect()`, DOM queries for `.price-diff-card`, `table`, `.price-lists-toolbar__filter-toggle`, `aria-expanded`
- **Interactions:** filter toggle expand @360; compare attempted @1023 (same-list blocked by API)

### Screenshots

| File | Description |
|---|---|
| `screenshots/price-lists-360-toolbar-collapsed.png` | Mobile toolbar — selects + Compare; filters collapsed |
| `screenshots/price-lists-360-filters-expanded.png` | Mobile filters panel expanded |
| `screenshots/price-lists-640-toolbar-expanded.png` | Tablet toolbar — filters visible, no toggle |
| `screenshots/price-lists-1023-empty-after-compare.png` | Tablet empty result after compare attempt |
| `screenshots/price-lists-1024-desktop-toolbar.png` | Desktop toolbar — two-row layout, filters expanded |

---

## Non-blocking notes

| ID | Sev | Issue |
|---|---|---|
| P2C-N1 | P2 | Diff cards/table and change-type badges not runtime-verified — only **1** price list in DB; self-diff returns HTTP 422. Unit tests (`priceListsPageResponsive`, `useDataViewMode`) cover policy + card markup. |
| P2C-N2 | P2 | Error/retry states (fetch lists / compare API failure) not runtime-tested; code paths present in `PriceListsPage`. |

---

## Scope confirmation

- Read-only QA; no product code or control docs modified
- No legacy fallbacks introduced
- No productive SKU/page hardcodes

## Recommended control-plane action

- Accept Agent 1B implementation + this QA report
- Transition `APP-PLATFORM-UX-3.0-PHASE-2C` → `VALIDATED`
- Release five `LOCK-UX30-P2C-*` locks
- Index `EVID-UX30-P2C-001`
- Next gate: Phase 2D selection (`UX30-D8` or successor)
