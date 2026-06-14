# Manual QA â€” App-Wide UX (Agent 1B)

Checklist for **usability, accessibility, and plain-language clarity** across the desktop app **outside the catalogue builder**.

Complements:

- [MANUAL_QA_BUILDER_UI.md](./MANUAL_QA_BUILDER_UI.md) â€” catalogue builder (Agent 1A)
- [MANUAL_QA_PRESENTATION_BUILDER.md](./MANUAL_QA_PRESENTATION_BUILDER.md) â€” presentation/PDF functional QA (Agent 1A)

Coordination reference: [docs/control/APP_WIDE_UX_SCOPE.md](./control/APP_WIDE_UX_SCOPE.md)

**Verdict context (Agent 1B):** Iterations 1â€“5 accepted **pending this user manual QA pass**. Target user: a **non-technical person** who may not be fast or intuitive with software.

---

## 1. Purpose

This checklist validates that the app is **easy, safe, and understandable** for everyday work â€” not just for developers.

You are checking:

- Plain Spanish labels (no unnecessary jargon)
- Obvious primary actions and guided flows
- Helpful empty, loading, and error states
- Keyboard access and visible focus
- Navigation and app shell behaviour

You are **not** testing catalogue builder internals, backend logic, PDF rendering quality, or import parser accuracy in depth.

---

## 2. Scope

### Covered

| Area | App section |
|------|-------------|
| App shell / navigation | Sidebar, skip link, API status |
| Inicio | Dashboard home |
| Importar tarifa | PDF import and review flow |
| Productos | Product list |
| Proveedores | Supplier list and selection |
| Comparar tarifas | Price list comparison |
| Product detail | Single product page |
| ConfiguraciÃ³n | Settings and restore |
| CategorÃ­as | Category tree management |
| Shared states | Loading, empty, error, retry |

### Not covered

| Area | Use instead |
|------|-------------|
| Catalogue builder (editor, preview workspace, presentation tab, export modal internals) | [MANUAL_QA_BUILDER_UI.md](./MANUAL_QA_BUILDER_UI.md) |
| Backend / API contracts | Agent 2 / automated tests |
| PDF visual parity | Manual comparison only |
| Schema / import parser internals | Developer review |

---

## Before you start

| Item | Detail |
|------|--------|
| **App** | Desktop (Electron) app running with API available |
| **Language** | UI in Spanish â€” expect plain language, not developer terms |
| **Estimated time** | ~60 minutes full pass; ~20 minutes smoke (sections 4 + 9) |
| **Record** | Date, app version/branch, Windows display scale, API up/down |

### Pass / fail recording template

| ID | Pass / Fail | Notes | Screenshot / log |
|----|-------------|-------|------------------|
| NAV-1 | | | |
| INI-1 | | | |
| â€¦ | | | |

**Pass** = expected result matches. **Fail** = any â€œBug ifâ€ condition occurs.

---

## 3. How to report issues

For each failure, collect:

| Field | What to write |
|-------|---------------|
| **Screen / page** | e.g. â€œImportar tarifaâ€, â€œProductosâ€ |
| **Action performed** | Step-by-step what you clicked or typed |
| **Expected result** | What you thought should happen |
| **Actual result** | What happened instead |
| **Screenshot** | Full window if possible |
| **Console / API logs** | If you can open DevTools (optional): red errors or failed network calls |
| **Blocks work?** | Yes / No â€” can you continue with another path? |

Send failures to the team with checklist ID (e.g. `IMP-3`) when possible.

---

## 4. Checklist â€” Navigation and shell

### NAV-1. Skip link (saltar al contenido)

| | |
|---|---|
| **Screen** | Any page with sidebar |
| **Action** | Press **Tab** once after opening the app |
| **Expected** | First focus is a â€œSaltar al contenidoâ€ (or similar) link; activating it moves focus to main content |
| **Bug if** | No skip link; skip link does nothing; focus lands inside sidebar without skip option |

### NAV-2. Keyboard navigation â€” sidebar

| | |
|---|---|
| **Screen** | Any page |
| **Action** | Use **Tab** / **Shift+Tab** to move through sidebar links |
| **Expected** | Every nav item reachable; focus ring clearly visible on each item |
| **Bug if** | Focus invisible; trap in sidebar with no escape; cannot reach main content |

### NAV-3. Active page state

| | |
|---|---|
| **Screen** | Click **Productos**, then **Inicio**, then **Importar tarifa** |
| **Action** | Observe sidebar while switching pages |
| **Expected** | Current page visually distinct; screen reader / accessibility tree shows current page (e.g. `aria-current`) |
| **Bug if** | No indication which page is active; multiple items look selected |

### NAV-4. API status badge

| | |
|---|---|
| **Screen** | Sidebar footer or status area |
| **Action** | With API running, read badge; stop API and refresh if safe |
| **Expected** | Plain Spanish: â€œConexiÃ³n activaâ€, â€œSin conexiÃ³nâ€, or â€œConectandoâ€¦â€; updates announced politely (live region) when status changes |
| **Bug if** | Only technical codes (e.g. â€œAPI conectadaâ€); no feedback when API down |

### NAV-5. Focus visibility (general)

| | |
|---|---|
| **Screen** | Any form or list page |
| **Action** | Tab through buttons, links, inputs |
| **Expected** | Clear focus outline on all interactive elements |
| **Bug if** | Focus disappears on buttons or links |

### NAV-6. Main content landmark

| | |
|---|---|
| **Screen** | After using skip link |
| **Action** | Skip to main content; start reading/interacting |
| **Expected** | Main area contains page title and primary content (not sidebar) |
| **Bug if** | Skip target wrong; main content still includes nav |

### NAV-7. â€œInicioâ€ label (not â€œDashboardâ€)

| | |
|---|---|
| **Screen** | Sidebar |
| **Action** | Read first/home nav item |
| **Expected** | Label says **Inicio** (or equally clear Spanish), not English â€œDashboardâ€ |
| **Bug if** | â€œDashboardâ€ or other unexplained English |

---

## 5. Checklist â€” Inicio

### INI-1. Title and description clarity

| | |
|---|---|
| **Screen** | **Inicio** (`/`) |
| **Action** | Read page title and short description |
| **Expected** | Non-technical person understands what this page is for without training |
| **Bug if** | Jargon-only title; no explanation of what to do next |

### INI-2. Empty states on cards/sections

| | |
|---|---|
| **Screen** | Inicio with little or no data |
| **Action** | Observe sections with no items |
| **Expected** | Friendly empty message; suggests what to do (e.g. import, add products) |
| **Bug if** | Blank area with no explanation |

### INI-3. Retryable errors

| | |
|---|---|
| **Screen** | Inicio when API fails or data cannot load |
| **Action** | Simulate error if possible (stop API) or use failing network |
| **Expected** | Clear error message in Spanish; **Reintentar** (or similar) button; no Docker/technical stack trace |
| **Bug if** | Infinite loading; technical error only; no way to retry |

### INI-4. â€œVer todasâ€ / â€œVer todosâ€ links

| | |
|---|---|
| **Screen** | Inicio summary sections |
| **Action** | Click â€œVer todasâ€ or â€œVer todosâ€ where shown |
| **Expected** | Navigates to correct list page (Productos, CatÃ¡logos, etc.) |
| **Bug if** | Link missing, broken, or goes to wrong page |

---

## 6. Checklist â€” Importar tarifa

### IMP-1. Upload loading overlay

| | |
|---|---|
| **Screen** | **Importar tarifa** |
| **Action** | Drop or select a PDF to upload |
| **Expected** | Dropzone shows loading overlay while uploading; you know something is happening |
| **Bug if** | No feedback during upload; UI looks frozen |

### IMP-2. Failed upload â€” inline error

| | |
|---|---|
| **Screen** | Importar tarifa |
| **Action** | Upload invalid file or trigger failure if possible |
| **Expected** | Error near dropzone in plain Spanish; explains what to try next |
| **Bug if** | Only toast with no context; silent failure |

### IMP-3. Step guidance

| | |
|---|---|
| **Screen** | Import flow after upload |
| **Action** | Read steps / instructions at top of flow |
| **Expected** | Clear 5-step order: subir PDF â†’ asignar categorÃ­as â†’ aplicar cambios â†’ revisar filas â†’ confirmar importaciÃ³n; you know which step you are on |
| **Bug if** | No steps; user lost about what to do next |

### IMP-4. Stat pills and filters in Spanish

| | |
|---|---|
| **Screen** | Import review / mapping area |
| **Action** | Read filter labels and stat pills |
| **Expected** | Plain Spanish; counts understandable |
| **Bug if** | English-only labels; unexplained abbreviations |

### IMP-5. 500+ row warning

| | |
|---|---|
| **Screen** | Large import batch (if available) |
| **Action** | Import or review batch with many rows |
| **Expected** | Clear warning that large imports may be slow or need care |
| **Bug if** | No warning; app becomes unusable without explanation |

### IMP-6. Mapping flow confusion (known risk)

| | |
|---|---|
| **Screen** | Category mapping sub-panels |
| **Action** | Try to map or ignore a source category |
| **Expected** | Plain Spanish labels (e.g. â€œCategorÃ­a encontrada en el PDFâ€, â€œCategorÃ­a de destino en la appâ€, â€œPendiente de revisarâ€); inline error with retry on confirm failures |
| **Bug if** | Primary labels show technical terms (`unmapped_category`, `master_key`, â€œDestino canÃ³nicoâ€); confirm errors only as toast |

---

## 7. Checklist â€” Productos / Proveedores / Comparar tarifas

### PRD-1. Product search label

| | |
|---|---|
| **Screen** | **Productos** |
| **Action** | Find search field; read its label or placeholder |
| **Expected** | Label explains what you are searching (products by name, etc.) |
| **Bug if** | Unlabeled search; placeholder only with jargon |

### PRD-2. No â€œmaestrosâ€ jargon

| | |
|---|---|
| **Screen** | Productos â€” title, headers, empty states |
| **Action** | Read page title and table headers |
| **Expected** | Says **Productos** or similar; does **not** say â€œmaestrosâ€ or other PIM jargon |
| **Bug if** | â€œProductos (maestros)â€ or â€œmaestrosâ€ visible to end user |

### PRD-3. Retryable error (Productos)

| | |
|---|---|
| **Screen** | Productos with API error |
| **Action** | Trigger or observe load failure |
| **Expected** | Error state with retry; not infinite skeleton |
| **Bug if** | Blank page; spinner forever |

### PRD-4. Empty paginator hidden

| | |
|---|---|
| **Screen** | Productos with zero results or empty list |
| **Action** | Search for nonsense or use empty database |
| **Expected** | No pagination bar when there is nothing to paginate |
| **Bug if** | Empty pager â€œPage 1 of 0â€ confuses user |

### PRO-1. Proveedores â€” empty state

| | |
|---|---|
| **Screen** | **Proveedores** â€” no suppliers |
| **Action** | Open with empty data |
| **Expected** | Clear empty message; import CTA if appropriate |
| **Bug if** | Generic or technical empty text |

### PRO-2. Proveedores â€” error state

| | |
|---|---|
| **Screen** | Proveedores â€” API error |
| **Expected** | Different from empty; offers retry |
| **Bug if** | Same as empty; no retry |

### PRO-3. Proveedores â€” no selection / no profiles

| | |
|---|---|
| **Screen** | Proveedores â€” select a row |
| **Action** | Select supplier with and without profile data |
| **Expected** | Distinct messages for â€œnothing selectedâ€ vs â€œno profiles for this supplierâ€ |
| **Bug if** | All states look the same |

### PRO-4. Proveedores â€” Spanish columns

| | |
|---|---|
| **Screen** | Proveedores table |
| **Expected** | Column headers in understandable Spanish |
| **Bug if** | English headers or internal field names |

### CMP-1. Comparar tarifas â€” zero results

| | |
|---|---|
| **Screen** | **Comparar tarifas** |
| **Action** | Apply filters so no rows match |
| **Expected** | Message like **Sin cambios con estos filtros** (or equivalent); not a broken table |
| **Bug if** | Empty table with no explanation |

### CMP-2. â€œCambio mÃ­nimo (%)â€ label visible

| | |
|---|---|
| **Screen** | Comparar tarifas â€” toolbar |
| **Action** | Find minimum change filter |
| **Expected** | Visible text label **Cambio mÃ­nimo (%)** (not icon-only) |
| **Bug if** | Unlabeled number field; meaning unclear |

### CMP-3. â€œDiferenciaâ€ columns

| | |
|---|---|
| **Screen** | Comparar tarifas results table |
| **Expected** | Difference columns labeled clearly (e.g. **Diferencia**) |
| **Bug if** | Cryptic abbreviations |

---

## 8. Checklist â€” Product detail / ConfiguraciÃ³n / CategorÃ­as

### DET-1. Invalid product URL

| | |
|---|---|
| **Screen** | Open `/products/invalid-id` or deleted product |
| **Action** | Navigate to bad product link |
| **Expected** | Clear 404 / not found message; not infinite loading skeleton |
| **Bug if** | Spinner never stops |

### DET-2. Price history table

| | |
|---|---|
| **Screen** | Valid product detail |
| **Action** | Open price history section |
| **Expected** | Table readable; headers in Spanish; keyboard can reach rows/controls |
| **Bug if** | Inaccessible table; no headers |

### DET-3. Image alt text

| | |
|---|---|
| **Screen** | Product with image |
| **Action** | Inspect or use screen reader if available |
| **Expected** | Image has descriptive alt text |
| **Bug if** | Empty or filename-only alt |

### DET-4. Expandable sections (`aria-expanded`)

| | |
|---|---|
| **Screen** | Product detail collapsible sections |
| **Action** | Expand/collapse with mouse and keyboard |
| **Expected** | State announced; content shown/hidden correctly |
| **Bug if** | Keyboard cannot toggle |

### SET-1. Settings load error

| | |
|---|---|
| **Screen** | **ConfiguraciÃ³n** â€” API error |
| **Expected** | Load error with retry or clear message |
| **Bug if** | Blank settings page |

### SET-2. Restore confirmation â€” RESTAURAR

| | |
|---|---|
| **Screen** | ConfiguraciÃ³n â€” restore defaults |
| **Action** | Start restore; read dialog |
| **Expected** | Dialog explains risk; must type **RESTAURAR** to confirm |
| **Bug if** | One-click destroy without confirmation |

### SET-3. Template label â€œCon portada e Ã­ndiceâ€

| | |
|---|---|
| **Screen** | ConfiguraciÃ³n â€” catalogue template option |
| **Expected** | Option labeled **Con portada e Ã­ndice** (or clear equivalent) |
| **Bug if** | Technical template id shown to user |

### CAT-1. Categories retryable error

| | |
|---|---|
| **Screen** | **CategorÃ­as** â€” API error |
| **Expected** | Error with retry |
| **Bug if** | Silent failure |

### CAT-2. Parent dropdown indentation

| | |
|---|---|
| **Screen** | CategorÃ­as â€” create/edit category |
| **Action** | Open parent category selector |
| **Expected** | Child categories visually indented; hierarchy understandable |
| **Bug if** | Flat list; cannot tell parent/child |

### CAT-3. Delete button hierarchy

| | |
|---|---|
| **Screen** | CategorÃ­as â€” edit category |
| **Expected** | Delete is visible but **less prominent** than Save/Cancel |
| **Bug if** | Delete is primary red button same size as Save |

---

## 9. Keyboard-only smoke test

Perform this sequence **using only keyboard** (Tab, Shift+Tab, Enter, Space, arrows where applicable):

| Step | Action | Pass if |
|------|--------|---------|
| K-1 | Start app; Tab to skip link; activate | Main content focused |
| K-2 | Tab to **Inicio**; Enter | Inicio loads |
| K-3 | Tab to **Importar tarifa**; Enter | Import page loads |
| K-4 | Tab to file input / dropzone; select file if possible | Upload starts or focus clear |
| K-5 | Tab to **Productos**; Enter | Productos loads |
| K-6 | Tab to search field; type a query | Search works |
| K-7 | Tab to **ConfiguraciÃ³n**; Enter | Settings loads |
| K-8 | Open restore dialog; Esc to close | Dialog closable without mouse |

**Smoke pass:** All K-1â€“K-8 completable without mouse.

---

## 10. Known remaining issues (Agent 1B QA)

These are **documented limitations** â€” fail only if worse than described.

| ID | Area | Known issue |
|----|------|-------------|
| KN-1 | Import flow | Screen remains dense; cognitive load high on large PDFs |
| KN-2 | Import confirm gate | No hard UI block if category mapping not re-applied (backend dependency) |
| KN-3 | Import tabs | Roving tabindex not implemented; basic tab/panel ARIA only |
| KN-4 | Import inline edit | Row edit panel has no focus trap |
| KN-5 | Proveedores | Selection pattern uses `aria-pressed`; may need further refinement |
| KN-6 | CategorÃ­as delete | Dialog confirm (not typed RESTAURAR-style); acceptable for Iteration 6 |
| KN-7 | Theme tokens | Optional future split for `--card` semantic token |
| KN-8 | Theme rollback | Future cleanup of light-theme rollback comment block in CSS |

If you hit these, note **â€œmatches known issue KN-xâ€** in your report.

---

## 11. Iteration 6 â€” complete (2026-06-07)

**Iteration 6 delivered** under **SHARED-2** (released). Re-verify after deploy:

| Check | What to verify |
|-------|----------------|
| IMP-3 / IMP-6 | 5-step guidance; plain mapping labels; inline confirm errors with retry |
| NAV-4 | â€œConexiÃ³n activaâ€ / â€œSin conexiÃ³nâ€ badge |
| CAT-3 | Delete opens accessible dialog (not browser `confirm`) |
| Shared primitives | `LoadingPage` busy state; `PageHeader` decorative icons hidden; dialog close focus-visible |

**Postâ€“Iteration 6 gate:** Agent 1A catalogue smoke/regression on shared surfaces â€” see [APP_WIDE_UX_SCOPE.md](./control/APP_WIDE_UX_SCOPE.md).

---

## 12. Theme v2.0 â€” dark-premium (SHARED-3)

**Status:** **COMPLETE** â€” SHARED-3 **RELEASED / CLOSED** (2026-06-08). Phases Aâ€“E done. Agent 1A catalogue smoke **PASS**. Tests **70/70**; build OK.

**Reference:** [NAROFITNESS_DESIGN_SYSTEM_v2.md](./design/NAROFITNESS_DESIGN_SYSTEM_v2.md)

### When to run this checklist

| Who | When |
|-----|------|
| **User** | After deploy or when validating theme regressions |
| **Agent 1A** | After future changes to `components/ui/**`, `index.css`, or theme tokens |

### Out of scope (do not fail Theme v2 QA for these)

| Item | Reason |
|------|--------|
| PDF export document appearance | **Agent 6** â€” separate print renderer |
| Preview iframe / PDF canvas background | Must stay **print-like white** by design |
| Import parser / backend data | Agent 2 â€” not theme |
| Catalogue presentation features (cover images, description column, paginated preview) | Separate Agent 1A / 2 / 6 tracks |

### Theme v2 checks (app chrome only)

| ID | Area | Check |
|----|------|-------|
| TH-1 | Global | Dark-premium palette consistent across routes (not catalogue PDF) |
| TH-2 | Shell | Sidebar, title bar, nav readable; API badge visible |
| TH-3 | Tokens | Buttons, inputs, tables use shared `ui/**` styles â€” no random one-off colors |
| TH-4 | Focus | Keyboard focus rings visible on dark backgrounds |
| TH-5 | Contrast | Primary text and labels meet readable contrast on dark surfaces |
| TH-6 | Preview | Builder preview **iframe** remains white/print-like â€” app dark theme does not bleed into PDF preview canvas |
| TH-7 | Export modal | Export dialog uses app theme; downloaded PDF content unchanged vs pre-theme baseline |
| TH-8 | Motion | `prefers-reduced-motion` respected |
| TH-9 | Forms | Inputs/selects use elevated `bg-secondary`; disabled states readable |
| TH-10 | Toasts | Success/error/warning toasts readable on dark (`richColors` + borders) |
| TH-11 | Destructive | Delete/restore dialogs use red destructive variant, not green |

### Cross-agent smoke (complete 2026-06-08)

**Agent 1A** on QA Stress Catalog:

- Catalogue builder opens; tables usable under new `ui/**` primitives
- Export modal opens; preview workspace iframe still white
- No regressions on DnD, pagination bars, dialogs from shared component changes

Report blockers to Agent 3; route PDF output issues to **Agent 6**, not Agent 1B.

---


### App Status Bar (SHARED-4 Phase 1 + 1.1)

**Coordination status:** **`IMPLEMENTED` / `VISUAL_QA_PENDING`** — SHARED-4 **RELEASED** (2026-06-08). Automated tests/build passed; **manual checks below pending**.


| ID | Area | Check |
|----|------|-------|
| SB-1 | Footer | Green bar visible at bottom, ~32px, full width |
| SB-2 | Layout | Main content not hidden behind footer |
| SB-3 | Left zone | Shows Conexión activa / Sin conexión / Conectando… |
| SB-4 | Center | Shows Sin tareas activas (no fake progress) |
| SB-5 | Panel | Click or Enter on bar opens Centro de procesos |
| SB-6 | Panel | Escape closes; focus returns to bar |
| SB-7 | PDF degraded | Right chip PDF no disponible when engine missing |
| SB-8 | Sidebar | API/PDF badges removed from sidebar (moved to bar) |

## Related documents

- [MANUAL_QA_BUILDER_UI.md](./MANUAL_QA_BUILDER_UI.md) â€” catalogue builder QA (Agent 1A)
- [docs/control/APP_WIDE_UX_SCOPE.md](./control/APP_WIDE_UX_SCOPE.md) â€” Agent 1B scope and implementation record
- [docs/control/tasks/APP-STATUS-BAR-MANUAL-QA.md](./control/tasks/APP-STATUS-BAR-MANUAL-QA.md) â€” pending Status Bar QA gate
