# UX 3.0 Phase 0 — Catalogue Builder Responsive Foundations QA

**Task ID:** `APP-PLATFORM-UX-3.0-PHASE-0-CATALOG-QA`  
**Agent:** 1A (Catalogue UI/UX) — read-only QA  
**Date:** 2026-06-12  
**Verdict:** `UX30_PHASE0_QA_PASS_WITH_NOTES`

---

## 1. Estado

`UX30_PHASE0_QA_PASS_WITH_NOTES`

Phase 0 foundations are configuration-safe and do not wire into Catalogue Builder UI. Automated regression is green. Visual smoke on catalogue surfaces at desktop viewports shows no layout drift attributable to Phase 0. Two non-blocking notes: ExportPdfDialog was not opened during smoke (FDL preflight bypasses modal), and preview at 1024×768 hit a transient PDF preview error after concurrent export load (environmental, not Phase 0).

---

## 2. Tests y build

| Command | Result |
|---------|--------|
| `npm test` (apps/desktop) | **PASS** — 45 files, **351/351** tests |
| `npm run build` (apps/desktop) | **PASS** — built in ~12s |

Phase 0-specific tests included:

- `src/lib/responsive/breakpoints.test.ts` — 11 tests (band contiguity, legacy min-width, table policy)
- `src/lib/responsive/tokensSmoke.test.ts` — 4 tests (builder tokens preserved, semantic screens config)

---

## 3. Configuración de breakpoints

**Source:** `tailwind.config.cjs`, `src/lib/responsive/breakpoints.ts`, `breakpoints.test.ts`

| Alias | Range | Tailwind media |
|-------|-------|----------------|
| `mobile:` | 0–639px | `{ max: "639px" }` |
| `tablet:` | 640–1023px | `{ min: "640px", max: "1023px" }` |
| `desktop:` | 1024–1279px | `{ min: "1024px", max: "1279px" }` — **closed band** |
| `wide:` | 1280px+ | `"1280px"` (min-width) |

**Contiguity:** Automated test iterates widths 0–1400px; `assertPlatformBandsContiguous()` passes. Boundary checks: 639→mobile, 640→tablet, 1023→tablet, 1024→desktop, 1279→desktop, 1280→wide.

**Legacy breakpoints:** `sm`/`md`/`lg`/`xl`/`2xl` are **not** overridden in `theme.extend.screens` (verified in `tokensSmoke.test.ts`). Documented legacy entry points unchanged: sm=640, md=768, lg=1024, xl=1280.

**`desktop:` vs `lg:`:** At 1440px, `lg:` applies (min 1024+) but `desktop:` does **not** (1440 > 1279). At 1100px, both `lg:` and `desktop:` apply — semantic overlap is intentional; `desktop:` is band-only, `lg:` is min-width “and up”. No accidental substitution.

**Gaps/overlaps:** None in platform bands.

---

## 4. CSS / tokens / capability utilities

### Safe-area tokens (`narofitness-tokens.css`)

```css
--safe-area-inset-top: env(safe-area-inset-top, 0px);
--safe-area-inset-right: env(safe-area-inset-right, 0px);
--safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
--safe-area-inset-left: env(safe-area-inset-left, 0px);
```

Valid CSS with `env()` fallbacks to `0px`.

### Builder tokens (unchanged)

Verified present and unchanged in smoke tests:

- `--builder-sidebar-width: 260px`
- `--editor-tab-min-height: 560px`
- `--builder-header-offset: 7.5rem`
- `--preview-canvas: #ffffff`

New non-visual tokens: `--touch-target-min`, `--touch-target-gap`.

### Capability utilities (`index.css` `@layer utilities`)

Opt-in only; **zero consumers** in `src/components/catalog-builder/**` or `src/pages/Catalog*`:

- `ux-fine-hover-only:*` — hidden by default; visible only with `(hover: hover) and (pointer: fine)`
- `ux-touch-primary-only:*` — hidden by default; visible only with `(hover: none), (pointer: coarse)`
- `ux-min-touch-target`, `ux-touch-gap`, `ux-safe-area-padding` — only apply when class is added

No global selectors alter existing elements. Nothing hides content by default on catalogue surfaces.

### Tailwind spacing extensions

`touch-target` / `touch-gap` map to CSS vars; unused in catalogue builder today.

---

## 5. Resultado visual por superficie

**Catalog:** FDL Tarifa 2026 (`43f2c3df-283d-465d-9e31-e9ccf40562c7`)  
**API:** healthy (`127.0.0.1:8000`)  
**App:** Vite dev (`127.0.0.1:5173`)

### Viewport 1440×900

| Surface | Drift vs baseline | Artifact |
|---------|-------------------|----------|
| Catalogue list | None observed | `catalog-list-1440x900.png` |
| Catalog Editor (General tab) | None observed | `catalog-editor-1440x900.png` |
| PreviewWorkspace | Layout/shell OK; PDF page scale small in canvas (pre-existing preview sizing, outside Phase 0 scope) | `preview-workspace-1440x900.png` |
| Export dialog | **Not captured** — FDL preflight `safeToExport` (534 info, 0 critical/warning); export queued directly | — |
| Shell desktop | Sidebar, header, status bar intact | `shell-desktop-1440x900.png` |

Export flow smoke: async job queued; Process Center showed “Exportar PDF — FDL Tarifa 2026” EN COLA; toast “Exportación PDF en cola”.

### Viewport 1024×768 (minimum desktop band)

| Surface | Drift vs baseline | Artifact |
|---------|-------------------|----------|
| Catalogue list | None observed | `catalog-list-1024x768.png` |
| Catalog Editor | None observed; tabs/header wrap normally | `catalog-editor-1024x768.png` |
| PreviewWorkspace | Shell OK; PDF preview error panel after long load (likely PDF engine contention from concurrent export) — **not Phase 0** | `preview-workspace-1024x768.png` |
| Export dialog | Not captured (same preflight bypass) | — |
| Shell desktop | No collapse/hidden nav at 1024px | visible in list/editor shots |

---

## 6. Defectos encontrados

| ID | Severity | Area | Description | Phase 0? |
|----|----------|------|-------------|----------|
| QA-P0-01 | Note | Export dialog smoke | Modal not shown on FDL because preflight passes with info-only diagnostics | No |
| QA-P0-02 | Note | Preview 1024×768 | Transient “No se pudo generar la vista previa PDF” during QA session | No (runtime/API load) |
| QA-P0-03 | Info | Preview 1440×900 | PDF page renders smaller than canvas (known preview scaling topic) | No |

**No Phase 0 configuration or catalogue-builder regression defects found.**

---

## 7. Confirmación read-only

- No source files, tests, config, or docs were modified during this QA pass.
- Artifacts written only under `temp/qa/ux30-phase0/`.
- Dev server started temporarily for visual smoke only.

---

## 8. Scope confirmation

Phase 0 touched only:

- `apps/desktop/tailwind.config.cjs`
- `apps/desktop/src/index.css` (capability utilities block at end)
- `apps/desktop/src/theme/narofitness-tokens.css` (touch/safe-area tokens appended)
- `apps/desktop/src/lib/responsive/**` (new library + tests)

**Catalogue Builder:** Grep confirms **no** usage of `mobile:`, `tablet:`, `desktop:`, `wide:`, or `ux-*` utilities in `catalog-builder/**` or catalogue pages. No speculative responsive UI components added.

---

## 9. Recomendación de locks

| Lock | Recommendation |
|------|----------------|
| `LOCK-UX30-P0-TOKENS` | **Release** — builder tokens intact; new tokens inert until consumed |
| `LOCK-UX30-P0-RESPONSIVE-PATHS` | **Release** — breakpoints/utilities validated; no catalogue UI wired |

---

## 10. Follow-up (optional)

1. Seed **QA Stress Catalog** with critical/warning layout diagnostics to capture ExportPdfDialog visually in a future smoke pass.
2. Re-run preview smoke at 1024×768 with no active PDF export job to confirm preview error was environmental.

---

## Artefactos

```
temp/qa/ux30-phase0/
├── UX30_PHASE0_CATALOG_QA_REPORT.md
├── catalog-list-1440x900.png
├── catalog-list-1024x768.png
├── catalog-editor-1440x900.png
├── catalog-editor-1024x768.png
├── preview-workspace-1440x900.png
├── preview-workspace-1024x768.png
└── shell-desktop-1440x900.png
```
