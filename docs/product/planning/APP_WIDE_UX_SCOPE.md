# App-Wide UX Scope (App UX agent)

Discovery and planning reference for **App UX agent — App-Wide Accessible UX/UI Agent**. Defines what is outside the catalogue builder (Catalog UI agent) and how App UX agent should begin work.

**Last updated:** 2026-06-12 (Agent 3 — APP-PLATFORM-UX-3.0 Phase 1 **VALIDATED**)

**Owner:** App UX agent. Agent 3 tracks shared-file locks.

**Active UI track:** [APP_PLATFORM_UX_3.0_ROADMAP.md](./APP_PLATFORM_UX_3.0_ROADMAP.md) — Phase 2A **`VALIDATED`**; **no active locks**; next gate **UX30-D7** (2B vs 2C).

**Parallel (protected):** [IMPORT_FDL_FULL_QUALITY_PLAN.md](./IMPORT_FDL_FULL_QUALITY_PLAN.md) — Agents 2/5.

**Paused:** PROD-DETAIL-UX-V2 QA, SOURCE-CATALOG-DUAL-PATH-1 Phase 1A.

---

## APP-PLATFORM-UX-3.0 — Phase 0 Foundations (CLOSED)

| Field | Value |
|-------|-------|
| **Status** | **`IMPLEMENTED` / `VALIDATED`** |
| **QA** | Catalog UI agent — **`UX30_PHASE0_QA_PASS_WITH_NOTES`** (351/351; build OK) |
| **Locks** | **RELEASED** — `LOCK-UX30-P0-TOKENS`, `LOCK-UX30-P0-RESPONSIVE-PATHS` |

**Non-blocking QA notes (paused tracks — do not reactivate):** ExportPdfDialog bypass; transient preview on concurrent export; small PDF scale pre-existing.

## APP-PLATFORM-UX-3.0 — Phase 1 Shell (CLOSED)

| Field | Value |
|-------|-------|
| **Status** | **`IMPLEMENTED` / `VALIDATED`** |
| **QA** | **`UX30_PHASE1_SHELL_REVALIDATION_PASS_WITH_NOTES`** (351/351; build OK) |
| **Lock** | **`LOCK-UX30-P1-SHELL`** — **RELEASED** |
| **P1-SHELL-001** | **CLOSED** |

**Revalidation:** Mobile bottom-nav only; tablet portrait drawer; tablet landscape rail; desktop/wide sidebar; catalogue smoke PASS; TitleBar 44×44 tablet / 32×32 desktop.

**Non-blocking (Phase 7):** min/close clicks; manual TitleBar drag — do not reactivate paused QA tracks.

## APP-PLATFORM-UX-3.0 — Phase 2A Products (CLOSED)

| Field | Value |
|-------|-------|
| **Status** | **`IMPLEMENTED` / `VALIDATED`** |
| **QA** | **`UX30_PHASE2A_PRODUCTS_QA_PASS`** — 367/367; build OK |
| **Defect** | **P2A-SHEET-001** — **CLOSED / RESOLVED** |
| **Locks** | 5 × `LOCK-UX30-P2A-*` — **RELEASED** |

**Delivered:** cards ≤1023px; table ≥1024px; variant Sheet; `useDataViewMode`; tests incl. `useDataViewMode.test.ts`.

**QA evidence:** `temp/qa/ux30-phase2a-products/UX30_PHASE2A_PRODUCTS_QA_REPORT.md`

## APP-PLATFORM-UX-3.0 — Phase 2 next slice (`NEEDS_DECISION`)

| Sub-phase | Status |
|-----------|--------|
| 2B Suppliers/Categories | **`PLANNED` / `NOT_AUTHORIZED`** — **BLOCKED** |
| 2C PriceLists | **`PLANNED` / `NOT_AUTHORIZED`** — **BLOCKED** |
| 2D Shared primitives | **`DEFERRED` / `NOT_AUTHORIZED`** — **BLOCKED** |

**Decision required:** **UX30-D7** — implement 2B before 2C, or vice versa.

**Roadmap:** [APP_PLATFORM_UX_3.0_ROADMAP.md](./APP_PLATFORM_UX_3.0_ROADMAP.md)

---

## App UX agent implementation record (iterations 1–5)

**Recorded by:** Agent 3 (from App UX agent completion report)

**Verification reported:**

- `npm run build` — OK
- `npm test` — OK (38 tests passing)
- No `api.ts` changes
- No `apps/api/**` changes
- No catalogue builder files intentionally touched (`components/catalog-builder/**`, `CatalogEditorPage.tsx` unchanged by design)

### Iteration 1 — App shell

| File | Changes |
|------|---------|
| `components/Layout.tsx` | Skip link; nav `aria-label`; `aria-current="page"`; focus rings; API badge `role="status"` + `aria-live`; “Dashboard” → “Inicio”; `<main id="main-content">` |
| `index.css` | Skip-link styles; nav focus; `prefers-reduced-motion` |

### Iteration 2 — Dashboard + shared patterns

| File | Changes |
|------|---------|
| `components/ErrorState.tsx` | **New** — retryable error pattern |
| `pages/Dashboard.tsx` | Removed Docker message; retryable errors; “Ver todas/todos” links; title “Inicio” |
| `components/EmptyState.tsx` | Icons `aria-hidden` |
| `components/ui/button.tsx` | `outline` variant |

### Iteration 3 — Importar tarifa

| File | Changes |
|------|---------|
| `lib/importLabels.ts` (or equivalent) | **New** — plain-language import labels |
| `pages/ImportPage.tsx` | Guided steps; semantic tabs; loading overlay in dropzone; inline errors; Spanish filters/stats; clearer 500-row warning; plain-language form labels |

### Iteration 4 — Lists

| File | Changes |
|------|---------|
| `pages/ProductsPage.tsx` | Removed “maestros” jargon; labelled search; retryable error; no empty paginator |
| `pages/PriceListsPage.tsx` | Third state “Sin cambios con estos filtros”; two-row toolbar; visible minimum % label; “Diferencia” columns |
| `pages/SuppliersPage.tsx` | Differentiated empty/error states; Spanish columns; `aria-selected`; import CTA |
| `components/ui/pagination.tsx` | Hide bar when `total = 0` |

### Iteration 5 — Forms and details

| File | Changes |
|------|---------|
| `pages/ProductDetailPage.tsx` | 404 instead of infinite skeleton; accessible price history table; Spanish labels; `aria-expanded`; image alt text |
| `pages/SettingsPage.tsx` | Load error; restore dialog with “RESTAURAR” confirmation; template label “Con portada e índice” |
| `pages/CategoriesPage.tsx` | Retryable error; parent selector indentation; less prominent delete button |

### Scope confirmation (App UX agent did not touch)

| Area | Touched? |
|------|----------|
| `apps/api/**` | No |
| `apps/desktop/src/lib/api.ts` | No |
| `components/catalog-builder/**` | No (intentional) |
| `pages/CatalogEditorPage.tsx`, `CatalogsPage.tsx` | No (intentional) |

---

## Shared files touched (completed — locks released)

These files were edited under App UX agent iterations 1–5. Recorded as **completed SHARED work**; **no active locks** remain for this pass.

| Lock ID (historical) | File(s) | Status | Notes |
|----------------------|---------|--------|-------|
| SHARED-1B-1 | `components/Layout.tsx` | **Released / complete** | App shell a11y |
| SHARED-1B-2 | `index.css` | **Released / complete** | Global skip-link, focus, reduced-motion |
| SHARED-1B-3 | `components/EmptyState.tsx` | **Released / complete** | `aria-hidden` on icons |
| SHARED-1B-4 | `components/ui/button.tsx` | **Released / complete** | `outline` variant |
| SHARED-1B-5 | `components/ui/pagination.tsx` | **Released / complete** | Hide when total = 0 — **catalogue builder uses this component** |
| SHARED-1B-6 | `components/ErrorState.tsx` | **Released / complete** | New shared pattern |

---

## App UX agent implementation record (Iteration 6 — SHARED-2)

**Status:** **Complete** — lock **RELEASED / CLOSED** (2026-06-07)

**Verification:** `npm test` 41/41; build OK; no `api.ts`; no `apps/api/**`; no catalogue builder files touched.

| Deliverable | Detail |
|-------------|--------|
| Import labels | Plain Spanish in `import/**` / `ImportPage` |
| Inline import errors | Improved inline errors (reduced toast-only failures) |
| Import flow guidance | Step guidance in import flow |
| Import tab/panel a11y | Tab and panel accessibility improvements |
| `LoadingPage` | `aria-busy` |
| `PageHeader` | Decorative icons `aria-hidden` |
| `dialog.tsx` | Close button `focus-visible` |
| Layout | Connection badge plain wording |
| Dashboard | Link wording |
| Categories | Delete confirmation dialog |

**Lock:** `SHARED-2` — completed by App UX agent; validated by Catalog UI agent static smoke; **no active lock**.

---

## Catalog UI agent catalogue smoke result (Phase 1B-A — post Iteration 6)

**Recorded by:** Agent 3 (from Catalog UI agent audit report)

| Field | Result |
|-------|--------|
| Audit type | Read-only static smoke/regression |
| Files modified | **None** |
| Blocking regressions | **None found** |
| Catalogue builder | **Safe** at static audit level |
| SHARED-2 | May remain **released** from Catalog UI agent perspective |

**Manual visual checks still recommended (non-blocking):**

- Outline button appearance in builder/export flows
- PDF export health badge wording in `Layout` (engine name when active) — Agent 6 owns semantics; App UX agent may polish copy via shared-file lock
- Focus rings on builder controls
- Preview workspace behavior
- DnD save/discard on Products tab
- Dialog focus-visible and trap behavior (export modal, settings-style dialogs)

**Known non-blocking notes:**

- `CatalogsPage` delete still uses native `confirm()` — out of Iteration 6 scope
- Pagination empty edge case — not blocking per Catalog UI agent audit

---

## Catalog UI agent catalogue smoke checklist (reference — completed static pass)

Static audit covered shared surfaces: `dialog`, `LoadingPage`, `PageHeader`, `Layout`, `pagination`, `button`, `EmptyState`. Optional user manual visual pass may use [MANUAL_QA_BUILDER_UI.md](../MANUAL_QA_BUILDER_UI.md).

---

## App UX agent mission

Design and improve the desktop app so a **non-technical person from another trade** can use it comfortably — not necessarily fast or intuitive with software.

**Prioritize:**

- Plain language and clear labels
- Guided flows with obvious primary actions
- Strong empty, loading, and error states
- Readable information hierarchy
- Accessibility (keyboard, focus, contrast, screen-reader-friendly patterns)
- Reduced cognitive load
- No unexplained technical jargon
- No dense dashboards without explanation
- App feels easy, safe, and understandable

---

## Required first task (discovery — no implementation)

App UX agent must **not implement** until the user approves a written plan.

### Discovery checklist

| Step | Task | Output |
|------|------|--------|
| 1 | Inspect `apps/desktop/src` — routes, pages, layout, shared components | Route/screen map (below) |
| 2 | Walk each non-catalogue screen for usability risks | Risk list per screen |
| 3 | Note accessibility gaps (focus, labels, errors, empty states) | A11y backlog |
| 4 | Identify shared files that overlap Catalog UI agent | Shared-file coordination requests |
| 5 | Propose phased iteration plan (small, safe slices) | Plan for user approval |
| 6 | Wait for user approval | — |
| 7 | Implement approved slice only | PR/report to Agent 3 |

### Deliverable template (App UX agent → Agent 3 → User)

```
Agent: 1B
Phase: Discovery (no code changes unless approved)
Screens reviewed: [list]
Top usability risks: [ranked]
Top accessibility risks: [ranked]
Shared files needing lock: [list + proposed owner]
Proposed iteration 1: [scope, files, out of scope]
Proposed iteration 2: [optional]
Blocked by Catalog UI agent/4 locks: [list]
Awaiting: user plan approval
```

---

## Route / screen map

From [`App.tsx`](../../apps/desktop/src/App.tsx):

| Route | Page | Owner | Notes |
|-------|------|-------|-------|
| `/` | `Dashboard.tsx` | **App UX agent** | Home / entry point |
| `/suppliers` | `SuppliersPage.tsx` | **App UX agent** | |
| `/import` | `ImportPage.tsx` | **App UX agent** | + `components/import/**` |
| `/products` | `ProductsPage.tsx` | **App UX agent** (UX/a11y) + **Agent 4** (API-3 data) | Catalog UI agent has **no role** on this page |
| `/products/:id` | `ProductDetailPage.tsx` | **App UX agent** | |
| `/categories` | `CategoriesPage.tsx` | **App UX agent** | |
| `/catalogs` | `CatalogsPage.tsx` | **Catalog UI agent** | Catalogue list |
| `/catalogs/:id` | `CatalogEditorPage.tsx` | **Catalog UI agent** | Builder + PreviewWorkspace |
| `/price-lists` | `PriceListsPage.tsx` | **App UX agent** | |
| `/settings` | `SettingsPage.tsx` | **App UX agent** | |

**Catalogue-only components (Catalog UI agent):** `components/catalog-builder/**`

**Import flow (App UX agent):** `components/import/**`

---

## Catalog UI agent vs App UX agent boundaries

| Area | Catalog UI agent (Catalogue) | App UX agent (App-wide) |
|------|------------------------|---------------------|
| Catalogue list + editor | Yes | No |
| PreviewWorkspace, export modal, presentation tab | Yes | No |
| Catalogue builder tests (`catalogLines`, `catalogLayout`, `editorPreview`, `previewState`) | Yes | No |
| Catalogue manual QA docs | Yes | No |
| Dashboard, import, suppliers, settings | No | Yes |
| Products list/detail (non-builder) | No | Yes |
| Categories, price lists pages | No | Yes |
| App shell, navigation, title bar | Shared — one owner at a time | Shared |
| Design system primitives (`components/ui/**`) | Prefer catalogue wrappers in `catalog-builder/**` | Default a11y steward — lock required |

**Rule:** App UX agent does **not** edit catalogue builder files unless Agent 3 documents an explicit handoff from Catalog UI agent.

**Rule:** Catalog UI agent does **not** edit app-wide pages or navigation unless explicitly assigned.

**Rule:** Catalog UI agent has **no role** on `ProductsPage` unless user reclassifies it as catalogue workflow.

---

## Shared primitives and shared files (closed rules)

App UX agent is the **default accessibility steward** for shared UI primitives (`components/ui/**`), but this is **not unrestricted ownership**.

**Before any edit to a shared file:** Agent 3 must record a temporary `SHARED-N` lock.

**Shared files include:**

- `components/ui/**`
- `Layout.tsx`, `PageHeader.tsx`, `EmptyState.tsx`, `TitleBar.tsx`
- `App.tsx`
- Global CSS
- Shared frontend utilities (e.g. `lib/pagination.ts`)

| Agent | Rule |
|-------|------|
| **App UX agent** | May propose app-wide a11y improvements to shared primitives — **lock required first** |
| **Catalog UI agent** | Must request lock to modify shared primitives for catalogue needs |
| **Catalog UI agent (preferred)** | Catalogue-specific wrappers/variants live under `components/catalog-builder/**` — no shared lock unless touching shared imports |

| File / area | Steward | Lock before edit? |
|-------------|---------|-------------------|
| `components/ui/**` | App UX agent (a11y) | **Yes** |
| `Layout.tsx`, `TitleBar.tsx`, `App.tsx` | App UX agent | **Yes** |
| `PageHeader.tsx`, `EmptyState.tsx`, `LoadingPage.tsx` | Per iteration | **Yes** |
| Global CSS, `lib/pagination.ts` | Per iteration | **Yes** |
| `components/catalog-builder/**` | Catalog UI agent | No |
| `lib/api.ts` | Agent 4 (API-X) | N/A — 1A and 1B blocked |

Agent 3 maintains the **shared-file lock table** in sync summaries.

---

## ProductsPage three-way split (closed)

| Agent | Owns on `ProductsPage` |
|-------|------------------------|
| **Agent 4** | API/data integration when API-3 `CONFIRMED` (`listMasters`, server pagination) |
| **App UX agent** | Labels, accessibility, visual clarity, UX polish |
| **Catalog UI agent** | **No role** (unless user reclassifies page) |

---

## Iteration plan (status)

| Iteration | Scope | Status |
|-----------|-------|--------|
| 0 | Discovery | Complete (led to user-approved roadmap) |
| 1 | App shell (`Layout.tsx`, `index.css`) | **Complete** |
| 2 | Dashboard + shared patterns (`ErrorState`, `EmptyState`, `button`) | **Complete** |
| 3 | Importar tarifa (`ImportPage`, `importLabels`) | **Complete** |
| 4 | Lists (`ProductsPage`, `PriceListsPage`, `SuppliersPage`, `pagination`) | **Complete** |
| 5 | Forms/details (`ProductDetailPage`, `SettingsPage`, `CategoriesPage`) | **Complete** |
| 6 | Import plain language, shared a11y (`dialog`, `LoadingPage`, `PageHeader`, …) | **Complete — SHARED-2 released** |

### Out of scope for App UX agent

- Catalogue builder tabs, PreviewWorkspace, presentation builder
- Backend/API changes
- `api.ts` contract integration (Agent 4)
- Catalogue manual QA checklists (Catalog UI agent)

---

## Usability / accessibility review prompts

Use during discovery walkthrough:

1. Would a warehouse/office worker understand every label without training?
2. Is the primary action obvious on each screen?
3. What happens when there is no data, slow network, or an error?
4. Can the screen be used with keyboard only?
5. Is focus visible? Are dialogs trap focus correctly?
6. Is there unexplained jargon (SKU, master, variant, layout mode)?
7. Does the screen overload the user with tables/filters at once?

---

## Documentation location (closed)

| Document | Status |
|----------|--------|
| `APP_WIDE_UX_SCOPE.md` (this file) | Active — discovery scope and iteration plan |
| [MANUAL_QA_APP_WIDE.md](../MANUAL_QA_APP_WIDE.md) | **PASS** (iterations 1–5); optional user visual re-check after Iteration 6 |

---

## Theme v2.0 — Narofitness App Design System (dark-premium)

**Status:** **`THEME_V2_COMPLETE`** — **SHARED-3 RELEASED / CLOSED** (2026-06-08)

**Reference:** [NAROFITNESS_DESIGN_SYSTEM_v2.md](../design/NAROFITNESS_DESIGN_SYSTEM_v2.md)

### Implementation record (App UX agent)

| Phase | Status | Scope |
|-------|--------|-------|
| **A** | **Complete** | Theme tokens, Tailwind, CSS variables |
| **B** | **Complete** | App shell — `Layout`, `TitleBar`, `main.tsx`, `index.html` |
| **C** | **Complete** | `components/ui/**` dark-premium migration |
| **D** | **Complete** | Page-level visual polish across routes |
| **E** | **Complete** | Focus/disabled/contrast, toasts, docs, release readiness |

**Verification:** `npm test` **70/70**; `npm run build` **OK**.

**Catalog UI agent smoke (post Theme v2):** **PASS** — QA Stress Catalog; export preflight modal; preview iframe white; no builder regressions.

**Not touched:** PDF templates/export engine (Agent 6); backend/API/importer/parser; `api.ts`.

### Catalogue Presentation Phase 1 — `show_description_column` (INTEGRATED)

**Status:** **`INTEGRATED` / `QA_READY`** — manual visual QA pending

| Layer | Status |
|-------|--------|
| Agent 2 backend | Complete — `003_catalog_show_description_column.py` |
| Agent 6 PDF | Complete — supplier-table Description column conditional |
| Catalog UI agent UI | Complete — General → Opciones del PDF checkbox |

Registry: [CATALOG_PRESENTATION_BACKLOG.md](./CATALOG_PRESENTATION_BACKLOG.md)

### Presentation — catalogue (Catalog UI agent / 6)

| Feature | Status |
|---------|--------|
| `show_description_column` (PRES-1) | **INTEGRATED** / **QA_READY** |
| Paginated PDF preview (PREV-3) | **`IMPLEMENTED` / `QA_PASS`** |
| Background jobs (PRES-5) | **NOT_STARTED** — [APP_JOBS_CONTRACT.md](./contracts/APP_JOBS_CONTRACT.md) |

### SHARED-3 — RELEASED / CLOSED

Historical scope: `index.css`, `theme/**`, `tailwind.config.cjs`, `main.tsx`, `index.html`, `components/ui/**`, `Layout.tsx`, `TitleBar.tsx`. **No active lock.**

### Known issues (preserved)

| ID | Issue |
|----|-------|
| KN-2 | Import confirm gate — no hard UI block if category mapping not re-applied |
| KN-3 | Import tabs — roving tabindex not implemented |
| KN-4 | Import row edit panel — no focus trap |
| KN-5 | Proveedores — `aria-pressed` selection pattern |
| KN-7 | Optional future token split for `--card` |
| KN-8 | Future cleanup of light-theme rollback comment block |

(KN-1, KN-6 unchanged — see [MANUAL_QA_APP_WIDE.md](../MANUAL_QA_APP_WIDE.md).)

---

## Status Bar / Process Center — SHARED-4 (RELEASED)

**Status:** **`IMPLEMENTED` / `VISUAL_QA_PENDING`** — SHARED-4 **RELEASED / CLOSED** (Phases **1 + 1.1**)

### Implementation record (App UX agent)

| Item | Detail |
|------|--------|
| Bar | Fixed bottom **2rem**; main green `#638B06`; left/API zone `#2F4702` |
| Chrome | Separators + outer border |
| Process Center | Panel for **system health only** |
| Health | Polls existing `/health` endpoint |
| Sidebar | API/PDF health badges **removed** (migrated to bar) |
| Verification | Tests/build passed |

**Not implemented:** ProcessRegistry, jobs, queue counts, PDF background jobs, backend/API/PDF changes.

**Manual QA:** [MANUAL_QA_APP_WIDE.md § Status Bar](../MANUAL_QA_APP_WIDE.md) SB-1–SB-8 — **pending**

**Future:** [APP_JOBS_CONTRACT.md](./contracts/APP_JOBS_CONTRACT.md) — **NOT_STARTED**

---

## PROD-DETAIL-UX-1 — Product detail page

| Field | Value |
|-------|-------|
| **Status** | **APPROVED / CLOSED** |
| **Owner** | App UX agent |
| **Scope** | `ProductDetailPage` — frontend UI only |
| **Tests** | 168/168; build OK |

**Delivered:** Hero, professional layout, cards, characteristics, gallery, variants panel.

**Deferred:** Optional variant-level detail depth — user closed page as-is.

---

## DASHBOARD-UX-1B — Dashboard redesign

| Field | Value |
|-------|-------|
| **Status** | **APPROVED / CLOSED** |
| **Owner** | App UX agent |
| **Scope** | `Dashboard.tsx` — frontend UI only |
| **Tests** | 198/198; build OK |

**Context:** First Dashboard rejected (redundancy). 1B removed duplicate sidebar, status bar, Process Center, triple empty catalogues, KPI tasks, filler copy.

**Future:** [DASHBOARD-API-2](./TRANSVERSAL_BACKLOG.md#dashboard-api-2) — real data feed.

---

## SCROLL-LAYOUT-1 — App scroll (CLOSED)

| Field | Value |
|-------|-------|
| **Status** | **APPROVED_WITH_NOTES / CLOSED** |
| **QA** | **PASS_WITH_NOTES** |

**Minors (non-blocking):** B1 residual scroll Catálogo General; B2 regional table scroll; B3 preview header/toolbar cosmetic. **No 1C** unless user requests.

---

## PROD-DETAIL-UX-V2 — Product detail v2 (**PAUSED / DEFERRED**)

**Contract:** [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./contracts/PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md)

| Phase | Status |
|-------|--------|
| A — Variants panel | **IMPLEMENTED / QA_PENDING** |
| B — Local media | **IMPLEMENTED / QA_PENDING** |
| C0 — Types (Agent 4) | **COMPLETE** |
| C/D — Price evolution | **IMPLEMENTED / QA_PENDING** |
| B2 UI — External URL | **IMPLEMENTED / QA_PENDING** |

**Base PROD-DETAIL-UX-1 remains APPROVED / CLOSED.**

---

## VARIANT-REPRESENTATION-1 — Frontend (App UX agent)

**Contract:** [VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md](./contracts/VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md)

**Status:** **PAUSED / DEFERRED** — impl complete; QA frozen for IMPORT-FDL priority.

---

## Next planning priority

| Agent | Priority | Notes |
|-------|----------|-------|
| **User** | **IMPORT-FDL-FULL-QUALITY** | Approve Wave 2 importer batches |
| **Agent 2** | Wave 1 diagnostic → Wave 2 fixes | **TOP_PRIORITY** |
| **Agent 5** | Full-catalog audit | **TOP_PRIORITY** |
| **App UX agent** | **Idle** | ProductDetail v2 QA **PAUSED** |
| **Catalog UI agent** | **Idle** | Products smoke Wave 2 only |
| **Agent 4 / 6** | **Idle** | Paused tracks |

---

## ChatGPT chat (App UX agent)

Use the dedicated **App-Wide Accessible UX/UI** ChatGPT chat (separate from Catalog UI agent catalogue chat). Agent 3 receives summaries; App UX agent chat does not author API contracts or edit `api.ts`.

---

## Related documents

- [planning state.md](./planning state.md) — live state
- [TRANSVERSAL_BACKLOG.md](./TRANSVERSAL_BACKLOG.md)
- [engineering roles.yaml](./engineering roles.yaml) — role and ownership authority
- [TASK_EXECUTION_PROTOCOL.md](./TASK_EXECUTION_PROTOCOL.md) — task and synchronization protocol
- [TASK_HISTORY.md](./TASK_HISTORY.md) — app-wide QA and completion history
- [MANUAL_QA_APP_WIDE.md](../MANUAL_QA_APP_WIDE.md) — user manual QA (this pass)
- [MANUAL_QA_BUILDER_UI.md](../MANUAL_QA_BUILDER_UI.md) — Catalog UI agent only
