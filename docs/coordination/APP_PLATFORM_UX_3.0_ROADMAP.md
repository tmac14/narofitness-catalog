# APP-PLATFORM-UX-3.0 — Touch-First Responsive Redesign

**Track ID:** APP-PLATFORM-UX-3.0  
**Plan task:** `APP-PLATFORM-UX-3.0-PLAN` — **`APPROVED_WITH_NOTES`**  
**Coordination tasks:** P0 **`VALIDATED`** · P1 **`VALIDATED`** · P2A **`VALIDATED`** / locks **RELEASED** (2026-06-12)  
**Primary owner:** Agent 1B (app-wide responsive UX/UI)  
**Phase 0 QA:** Agent 1A — **`UX30_PHASE0_QA_PASS_WITH_NOTES`**  
**Phase 1 QA:** Agent 1A — **`UX30_PHASE1_SHELL_REVALIDATION_PASS_WITH_NOTES`**  
**Phase 2A QA:** Agent 1A — **`UX30_PHASE2A_PRODUCTS_QA_PASS`**

**Parallel track (protected):** [IMPORT_FDL_FULL_QUALITY_PLAN.md](./IMPORT_FDL_FULL_QUALITY_PLAN.md) — Agents **2** and **5** must not be interrupted.

**Task and locks registry:** [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml) · **Ownership registry:** [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)

---

## Status

| Field | Value |
|-------|-------|
| **Plan** | **APPROVED_WITH_NOTES** |
| **Phase 0** | **`IMPLEMENTED` / `VALIDATED`** — QA **`PASS_WITH_NOTES`** |
| **Phase 1** | **`IMPLEMENTED` / `VALIDATED`** — QA **`PASS_WITH_NOTES`** |
| **Phase 2A** | **`IMPLEMENTED` / `VALIDATED`** — QA **`PASS`** |
| **Current phase** | **Phase 3 — next slice** — **`NEEDS_DECISION`** (Phase 2 complete) |
| **Phase 1 decisions** | **UX30-D1**, **UX30-D4** — **`DECIDED`** (2026-06-12) |
| **Phase 2A decision** | **UX30-D6** — Products cards/sheet — **`DECIDED`** (user-approved) |
| **Phase 0 locks** | **RELEASED** (2026-06-12) |
| **Phase 1 locks** | **`LOCK-UX30-P1-SHELL`** — **RELEASED** (2026-06-12) |
| **Phase 2A locks** | **RELEASED** (2026-06-12) — see § Phase 2A |
| **Phase 2B** | **`VALIDATED`** (2026-06-13) |
| **Phase 2C** | **`VALIDATED`** (2026-06-13) |
| **Phase 2D** | **`VALIDATED`** (2026-06-14) — Phase 2 list track **COMPLETE** |
| **Phase 3** | **`PLANNED` / `NOT_AUTHORIZED`** — awaiting slice selection |

### Phase 2A verification (Agent 1A QA)

| Check | Result |
|-------|--------|
| Tests | **367/367** PASS |
| Build | PASS |
| Mobile/tablet ≤1023px | **Cards** touch-first |
| Desktop/wide ≥1024px | **Table** |
| Dual mode / horizontal overflow | **None** |
| Touch targets | **≥44px** |
| Variant Sheet | Light Sheet + variant cards; **no** mini-table |
| Sheet a11y — initial focus, trap, return to trigger | **PASS** |
| **P2A-SHEET-001** | **CLOSED / RESOLVED** |
| ProductDetail, catalogue, backend, API, PDF | **Intact** |

**QA evidence:** `temp/qa/ux30-phase2a-products/UX30_PHASE2A_PRODUCTS_QA_REPORT.md` · `temp/qa/ux30-phase2a-products/focus-revalidation/P2A_SHEET_FOCUS_REVALIDATION_REPORT.md`

### Phase 1 verification (Agent 1A independent revalidation)

| Check | Result |
|-------|--------|
| Tests | **351/351** PASS |
| Build | PASS |
| Mobile | **Bottom navigation only** |
| Tablet portrait | **Drawer header only** |
| Tablet landscape | **Rail only** |
| Desktop / wide | **Sidebar only** |
| **P1-SHELL-001** | **RESOLVED / CLOSED** |
| Catalogue smoke | **PASS** |
| TitleBar Electron — tablet controls | **44×44px** |
| TitleBar Electron — desktop/wide controls | **32×32px** |
| TitleBar — title overflow | **None** |
| TitleBar — drag / no-drag regions | **Present** |

### Phase 0 verification (Agent 1A independent QA)

| Check | Result |
|-------|--------|
| Tests | **351/351** PASS |
| Build | PASS |
| Semantic breakpoints + legacy screens | PASS |
| Tokens/CSS | Safe and inert |
| Catalogue list / editor / preview shell | No regression attributable to Phase 0 |

---

## Roadmap (approved — summary)

| Phase | Name | Status |
|-------|------|--------|
| **0** | Foundations (tokens, responsive primitives) | **`IMPLEMENTED` / `VALIDATED`** — locks **RELEASED** |
| **1** | Shell / navigation | **`IMPLEMENTED` / `VALIDATED`** — lock **RELEASED** |
| **2A** | Products responsive list | **`IMPLEMENTED` / `VALIDATED`** — locks **RELEASED** |
| **2B** | Suppliers / Categories | **`VALIDATED`** (2026-06-13) |
| **2C** | PriceLists | **`VALIDATED`** (2026-06-13) |
| **2D** | Shared list primitives | **`VALIDATED`** (2026-06-14) — Phase 2 list track **COMPLETE** |
| **3** | Forms & detail surfaces | **`PLANNED` / `NOT_AUTHORIZED`** — awaiting slice selection |
| 4 | Import flows | Not locked yet — **needs user decision** (mobile Import Review scope) |
| 5 | Catalogue surfaces | Not locked yet — **needs user decision** (mobile Catalog Editor scope) |
| 6 | Polish & a11y hardening | Not locked yet |
| 7 | Visual regression / QA sign-off | Not locked yet — **needs user decision** (automation strategy) |

**Phase 0 rule:** Foundations only — no speculative screen-specific responsive components until a consuming phase proves need.

---

## Ownership (explicit)

| Agent | Owns | Blocked from |
|-------|------|--------------|
| **Agent 1B** | App-wide responsive UX; Phase 0–2A **shipped**; Phase 2B/2C planning pending user decision | `catalog-builder/**`, PreviewWorkspace, export UI, `lib/api.ts`, ProductDetail |
| **Agent 1A** | `CatalogsPage`, `CatalogEditorPage`, `components/catalog-builder/**`, PreviewWorkspace, export-dialog UI | Backend, `api.ts` |
| **Agent 4** | `lib/api.ts`, hooks, types — **only after `CONFIRMED` contract** | Visual/design work |
| **Agent 6** | PDF/print renderer, export parity — **advisory** on preview/export | Agent 1A frontend files; automatic frontend ownership |
| **Agent 2 / 5** | `IMPORT-FDL-FULL-QUALITY` | UI work reassignment |

**Agent 1B may audit catalogue surfaces read-only; edits require Agent 1A handoff + Agent 3 lock.**

**`components/ui/**`:** No wildcard lock. Existing primitive edits require **per-file** lock request from Agent 3.

---

## Phase 0 locks — RELEASED (2026-06-12)

| Lock ID | Released | Validated by |
|---------|----------|--------------|
| `LOCK-UX30-P0-TOKENS` | **RELEASED** | Agent 1A QA — tokens/CSS inert |
| `LOCK-UX30-P0-RESPONSIVE-PATHS` | **RELEASED** | Agent 1A QA — no catalogue regression |

**Historical paths (Phase 0 only):** `tailwind.config.cjs`, `index.css`, `narofitness-tokens.css`, `components/responsive/**`, `lib/responsive/**`.

Future edits to global tokens or responsive foundations require a **new Agent 3 lock** per task.

### Phase 0 QA notes (non-blocking — out of Phase 0 scope)

| ID | Note | Track |
|----|------|-------|
| P0-N1 | ExportPdfDialog not opened — preflight bypass behaved correctly | Paused PDF/export QA |
| P0-N2 | Transient preview runtime error during concurrent export | Paused PDF/Preview QA — **do not reactivate** |
| P0-N3 | Small PDF scale — pre-existing issue | Paused PDF QA |

**These notes do not block Phase 0 closure or Phase 1 decision gate.**

---

## Phase 1 locks — RELEASED (2026-06-12)

| Lock ID | Released | Validated by |
|---------|----------|--------------|
| `LOCK-UX30-P1-SHELL` | **RELEASED** | Agent 1A `UX30_PHASE1_SHELL_REVALIDATION_PASS_WITH_NOTES` |

**Historical paths (Phase 1 only):** `App.tsx`, `Layout.tsx`, `TitleBar.tsx`.

Future shell edits require a **new Agent 3 lock** per task.

### Phase 1 defects

| ID | Status | Notes |
|----|--------|-------|
| **P1-SHELL-001** | **CLOSED / RESOLVED** | Verified in Agent 1A revalidation |

### Phase 1 QA notes (non-blocking)

| ID | Note | Deferred to |
|----|------|-------------|
| P1-N1 | Minimize/close button clicks not manually executed | Phase 7 final QA |
| P1-N2 | TitleBar Electron manual drag not executed | Phase 7 final QA |

**Do not reactivate** paused ProductDetail / PDF / Preview QA for these notes.

### Phase 7 deferred QA (registered)

| ID | Check | Source |
|----|-------|--------|
| **P7-N1** | Manually validate minimize/close button clicks (TitleBar Electron) | P1-N1 |
| **P7-N2** | Manually validate real TitleBar window drag behavior | P1-N2 |

---

## Phase 2 plan — APPROVED_WITH_NOTES (2026-06-12)

Phase 2 split into sub-phases **2A–2D**. **2A–2D** complete; Phase 2 list track **COMPLETE** (2026-06-14).

| Sub-phase | Surface | Status |
|-----------|---------|--------|
| **2A** | Products responsive list | **`IMPLEMENTED` / `VALIDATED`** |
| **2B** | Suppliers / Categories | **`VALIDATED`** (2026-06-13) |
| **2C** | PriceLists | **`VALIDATED`** (2026-06-13) |
| **2D** | Shared list primitives | **`VALIDATED`** (2026-06-14) |

**Next UI gate:** User decision — **Phase 3** slice selection. No implementation until plan approved and locks registered.

---

## Phase 2A locks — RELEASED (2026-06-12)

| Lock ID | Released | Validated by |
|---------|----------|--------------|
| `LOCK-UX30-P2A-PRODUCTS-PAGE` | **RELEASED** | `UX30_PHASE2A_PRODUCTS_QA_PASS` |
| `LOCK-UX30-P2A-PRODUCTS-CSS` | **RELEASED** | scoped Products CSS — no catalogue regression |
| `LOCK-UX30-P2A-PRODUCTS-COMPONENTS` | **RELEASED** | card/sheet components shipped |
| `LOCK-UX30-P2A-HOOK` | **RELEASED** | `useDataViewMode.ts` |
| `LOCK-UX30-P2A-PRODUCTS-TESTS` | **RELEASED** | Products + hook tests |

**Historical paths (Phase 2A):** `ProductsPage.tsx`; scoped `index.css`; `ProductMasterCard.tsx`, `ProductMasterCardList.tsx`, `ProductVariantExpandSheet.tsx`; `useDataViewMode.ts`; `productsPageSourcePageActions.test.tsx`, `productsPageResponsive.test.tsx`.

Future Products responsive edits require a **new Agent 3 lock** per task.

### Phase 2A defects

| ID | Status | Notes |
|----|--------|-------|
| **P2A-SHEET-001** | **CLOSED / RESOLVED** | Sheet focus trap + return-to-trigger — revalidated PASS |

### Phase 2A delivered tests (record)

| File | Lock origin | Notes |
|------|-------------|-------|
| `lib/productsPageSourcePageActions.test.tsx` | `LOCK-UX30-P2A-PRODUCTS-TESTS` | In original lock |
| `lib/productsPageResponsive.test.tsx` | `LOCK-UX30-P2A-PRODUCTS-TESTS` | In original lock |
| `hooks/useDataViewMode.test.ts` | Delivered during P2A | **Not in original lock** — recorded for traceability |

---

## Not registered (by design)

| Item | Reason |
|------|--------|
| Phase 3 UX30 slice | **NOT_AUTHORIZED** — awaiting user/orchestration gate |
| ProductDetail / Import / Dashboard / Settings | Out of Phase 2 scope |
| Catalogue Builder lock | Agent 1A default ownership — no 1B lock |
| `components/ui/**` wildcard | Per-file lock only when needed |
| Preview / Export frontend | Agent 1A — Agent 6 advisory only |
| Agent 4 involvement | Only on confirmed API contract |

---

## Decisions — DECIDED (Phase 1)

### UX30-D1 — Supported platforms (`DECIDED` 2026-06-12)

| Band | Range | Notes |
|------|-------|-------|
| **Mobile** | **360–639px** | Portrait **priority**; landscape supported |
| **Tablet** | **640–1023px** | Portrait and landscape **first-class** |
| **Desktop** | **1024–1279px** | — |
| **Wide desktop** | **1280px+** | — |

| Constraint | Value |
|------------|-------|
| Minimum supported viewport | **360px** |
| Minimum touch target | **44px** |

### UX30-D4 — Hybrid responsive navigation (`DECIDED` 2026-06-12)

| Band | Pattern |
|------|---------|
| **Mobile** | **Bottom navigation** — 4 primary destinations + **“Más”** opens drawer |
| **Tablet portrait** | **Collapsible navigation drawer** |
| **Tablet landscape** | **Navigation rail** or compact sidebar |
| **Desktop / wide** | **Full sidebar** |

**Rule:** No action may depend **exclusively on hover**.

---

## Pending decisions (`NEEDS_DECISION`)

| ID | Topic | Blocks |
|----|-------|--------|
| **UX30-D2** | **Import Review** mobile scope (read-only vs inline edit) | Phase 4 |
| **UX30-D3** | **Catalog Editor** mobile scope (read-only vs full edit) | Phase 5 |
| **UX30-D5** | **Visual regression** automation strategy (tooling, scope, CI) | Phase 7 |
| **UX30-D7** | **Phase 2B vs 2C** implementation sequence | Phase 2 next slice |

---

## Decisions — DECIDED (Phase 2A)

### UX30-D6 — Products responsive list pattern (`DECIDED` — user-approved)

| Band | Pattern |
|------|---------|
| **Mobile / tablet** | **Cards** — touch-first master list |
| **Variant inspection** | **Light Sheet** with list/cards — touch-first |
| **Desktop / wide** | **Current table** — unchanged layout paradigm |

**Rules:**

- **No** compressed mini-table on mobile/tablet.
- **No** duplication or reactivation of **ProductDetail** workstream.
- Consume `lib/responsive/**` read-only; no edits without separate lock.

---

## Phase 2 next slice — decision gate (`NEEDS_DECISION`)

**Task:** `APP-PLATFORM-UX-3.0-PHASE-2-SEQUENCE-DECISION`  
**Status:** **`BLOCKED`** — awaiting user decision **UX30-D7**

| Option | Surface | Notes |
|--------|---------|-------|
| **2B** | Suppliers + Categories | Simpler list surfaces; pattern reuse from P2A |
| **2C** | PriceLists | Distinct table semantics; may benefit from 2D primitives later |

**No locks, no implementation** until user selects sequence and Agent 3 registers locks.

### Protected parallel tracks

- **IMPORT-FDL-FULL-QUALITY** — Agents 2/5
- **Paused:** ProductDetail QA, PDF/Preview QA, Page15, etc.

---

## Collision risks

| Hotspot | Agents | Risk | Mitigation |
|---------|--------|------|------------|
| Global tokens/CSS | 1B vs 1A (theme consumers) | Token drift breaks catalogue preview | P0 **VALIDATED**; per-task lock on re-edit |
| `tailwind.config.cjs` | 1B vs prior Theme v2 | Regression on desktop layout | Incremental diff; no shell changes in P0 |
| New `responsive/**` imports | 1B vs 1A | Premature coupling into catalog-builder | Paths reserved for 1B; 1A uses only after explicit handoff |
| `lib/api.ts` | 1B vs 4 | Contract invention | Agent 4 only on `CONFIRMED` |
| Import track | 2/5 vs 1B | Context switch | IMPORT-FDL remains top data priority; UX 3.0 UI parallel |
| `components/ui/*` (existing) | 1A vs 1B | Primitive conflicts | No wildcard lock; per-file request |
| Shell (`Layout`/`TitleBar`) | 1B vs 1A catalogue entry | Nav breaks builder routes | P1 **VALIDATED**; per-task lock on re-edit |
| Phase 2A Products vs ProductDetail | 1B vs paused PROD-DETAIL | Accidental detail refactor | P2A locks exclude ProductDetail*; UX30-D6 no duplication |
| Phase 2A index.css vs catalogue | 1B vs 1A preview theme | Global CSS drift | LOCK scope: Products list rules only |
| Phase 2 list/table surfaces | 1B vs 1A catalogue tables | Scope creep into builder | P2A **VALIDATED**; 1A owns catalog-builder; P2B/2C await UX30-D7 |
| Bottom nav vs status bar | 1B vs SHARED-4 | Overlap/z-index | Reuse status bar zone; no duplicate chrome |
| Hover-only patterns | 1B vs touch | Mobile unusable | UX30-D4: no hover-only actions |

---

## Approved plan notes (preserved)

- Mobile and tablet are **first-class**, not residual desktop shrink.
- Agent 4 is **not** a shared-primitive owner.
- Agent 1A owns all catalogue-builder implementation including preview and export dialog UI.
- Agent 6 advises PDF/preview/export parity; does not take frontend file ownership.

---

## Related documents

- [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md)
- [APP_WIDE_UX_SCOPE.md](./APP_WIDE_UX_SCOPE.md)
- [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)
- [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml)
