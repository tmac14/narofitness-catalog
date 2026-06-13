# UX 3.0 Phase 1 — Responsive Shell QA Report

**Task ID:** `APP-PLATFORM-UX-3.0-PHASE-1-SHELL-QA`  
**Agent:** 1A (Catalogue UI/UX) — read-only QA  
**Date:** 2026-06-12  
**Verdict:** `UX30_PHASE1_SHELL_QA_FAIL`

---

## 1. Estado

`UX30_PHASE1_SHELL_QA_FAIL`

Mobile, tablet portrait/landscape, accessibility, Status Bar coexistence, and catalogue shell smoke largely pass. **Desktop/wide (≥1024px) fails:** bottom navigation remains visible alongside the full sidebar because `MobileBottomNav` uses `tablet:hidden` only (hides 640–1023px) and lacks `lg:hidden` for desktop band.

---

## 2. Tests y build

| Command | Result |
|---------|--------|
| `npm run test --prefix apps/desktop` | **PASS** — 45 files, **351/351** tests |
| `npm run build --prefix apps/desktop` | **PASS** — built in ~16s |

No dedicated shell component unit tests found; regression suite green.

---

## 3. Resultado por viewport

| Viewport | Expected shell | Observed | Pass |
|----------|----------------|----------|------|
| 360×800 mobile | Bottom nav only | Bottom nav only; targets ≥47px | ✅ |
| 390×844 mobile | Bottom nav only | Bottom nav only; no horizontal overflow | ✅ |
| 639×800 mobile max | Bottom nav only | Bottom nav only | ✅ |
| 640×800 tablet portrait start | Header + drawer; no bottom nav | `tabletHeader` only; bottom nav hidden | ✅ |
| 640×360 landscape boundary | Rail only | Rail only; 8 icons | ✅ |
| 768×1024 tablet portrait | Header + drawer | Header + drawer; drawer 44×44 | ✅ |
| 1023×768 tablet landscape | Rail only | Rail only; 8×44px; Catálogos `aria-current` | ✅ |
| **1024×768 desktop boundary** | **Sidebar only** | **Sidebar + bottom nav (~48px)** | ❌ |
| **1440×900 wide** | **Sidebar only** | **Sidebar + bottom nav** | ❌ |

---

## 4. Resultado por patrón de navegación

### Mobile (390×844)

| Check | Result |
|-------|--------|
| Only bottom nav visible | ✅ |
| Primary destinations (Inicio, Importar, Productos, Catálogos) | ✅ Present and navigable |
| “Más” opens Sheet | ✅ |
| Four secondary destinations in Sheet | ✅ Proveedores, Categorías, Comparar tarifas, Configuración |
| Secondary route activates “Más” (`aria-current="page"`) | ✅ Verified on `/settings` |
| Bottom nav above Status Bar (no overlap) | ✅ `statusBarAboveBottomNav: true` |

### Tablet portrait (768×1024)

| Check | Result |
|-------|--------|
| Header + drawer trigger only | ✅ |
| Drawer opens from left | ✅ |
| Eight destinations in drawer | ✅ |
| Navigate closes drawer | ✅ `/products` from drawer |
| Initial focus on “Cerrar panel” | ✅ |

### Tablet landscape (1023×768)

| Check | Result |
|-------|--------|
| Rail visible; no bottom nav / sidebar / drawer header | ✅ |
| Eight icon links with `sr-only` labels | ✅ `railCount: 8`, `minRailTargetPx: 44` |
| Active state on `/catalogs` | ✅ `aria-current="page"` |

### Desktop/wide (1024×768, 1440×900)

| Check | Result |
|-------|--------|
| Sidebar completa | ✅ |
| Sin bottom nav | ❌ **Visible at 1024+** |
| Sin drawer header ni rail | ✅ |
| Regresión vs shell anterior | ❌ Bottom nav steals ~48px vertical space |

**Root cause (read-only inspection):** `Layout.tsx` line 162 — `className="... tablet:hidden"` on `MobileBottomNav`. Semantic `tablet:` is a closed band (640–1023px); at 1024px+ the utility does not apply.

**Suggested fix (out of QA scope):** Add `lg:hidden` (or equivalent mobile-only visibility) to `MobileBottomNav`.

---

## 5. Resultado de foco y teclado

| Check | Result |
|-------|--------|
| “Más” Sheet: initial focus on “Cerrar panel” | ✅ |
| Tablet drawer: initial focus on “Cerrar panel” | ✅ |
| Escape closes “Más” Sheet | ✅ |
| Focus returns to “Más secciones” trigger after Escape | ✅ |
| Skip link focuses `#main-content` | ✅ |
| `aria-current` on deep links | ✅ `/products/:id` → Productos; `/catalogs/:id` → Catálogos |
| Focus trap behind Sheet | ⚠️ Not exhaustively probed (Radix default); no escape observed during smoke |
| Tab order after close button | ⚠️ Not fully scripted; manual spot-check deferred |

No hover-only navigation actions observed in shell (links/buttons work on tap).

---

## 6. Status Bar / Process Center

| Check | Result |
|-------|--------|
| Bottom nav stacked above Status Bar (mobile) | ✅ No overlap |
| Process Center opens on mobile | ✅ |
| Process Center closes | ✅ “Cerrar” |
| Sheet covers bottom nav when open | ✅ `pcCoversBottomNav: true` |
| Process Center not hidden behind bottom nav | ✅ |

---

## 7. Catalogue smoke (shell-only)

Validated `/catalogs` and `/catalogs/:id` — shell must not block access, keep Catálogos active, avoid horizontal scroll, allow editor entry.

| Viewport | `/catalogs` | `/catalogs/:id` editor |
|----------|-------------|------------------------|
| 390×844 | ✅ Bottom nav; Catálogos reachable | ✅ Entry OK; no shell horizontal overflow |
| 768×1024 | ✅ Drawer header “Catálogos”; list accessible | ✅ Export button visible; `bottomNav: false` |
| 1023×768 | ✅ Rail; Catálogos active | ✅ (list smoke; editor not re-shot) |
| 1024×768 | ⚠️ List usable but **dual nav chrome** | ⚠️ Editor loads; bottom nav consumes space |
| 1440×900 | ⚠️ Same dual-nav defect | — |

No shell-induced horizontal overflow on catalogue surfaces tested.

---

## 8. Electron TitleBar

| Check | Result |
|-------|--------|
| Runtime validation with `npm run dev` | ⚠️ **Not executed** (web-only smoke via `npm run dev:web`) |
| Code review `TitleBar.tsx` | ✅ Buttons `h-11 w-11` (44px) below `lg`; compact `lg:h-8 lg:w-8` at 1024+ |
| Web build | TitleBar returns `null` when not Electron — expected |
| Drag region | ✅ `.titlebar-drag` / `.titlebar-no-drag` in `index.css` |

**Follow-up:** Manual Electron QA at 768px and 1024px widths recommended before lock release.

---

## 9. Defectos

| ID | Severity | Area | Reproducción |
|----|----------|------|--------------|
| **P1-SHELL-001** | **Major** | Desktop/wide shell | 1. Open app at 1024×768 or 1440×900. 2. Observe full sidebar **and** bottom navigation bar simultaneously. 3. ~48px vertical chrome lost; violates “Sin bottom nav” on desktop. |
| P1-SHELL-002 | Note | Electron TitleBar | Runtime targets not verified in Electron session |
| P1-SHELL-003 | Note | Focus trap / Tab order | Full keyboard walk-through not automated |

---

## 10. Artefactos generados

```
temp/qa/ux30-phase1-shell/
├── UX30_PHASE1_SHELL_QA_REPORT.md
├── shell-metrics.json
├── mobile-360x800-home.png
├── mobile-390x844-home.png
├── mobile-390x844-settings-mas-active.png
├── mobile-process-center-open.png
├── catalog-editor-mobile-390x844.png
├── catalog-list-tablet-portrait-768x1024.png
├── catalog-editor-tablet-portrait-768x1024.png
├── catalog-list-tablet-landscape-1023x768.png
├── desktop-boundary-1024x768-defect.png
├── catalog-editor-desktop-1024x768.png
├── desktop-wide-1440x900.png
└── boundary-640x360-landscape.png
```

---

## 11. Confirmación read-only

- No source files, tests, config, or docs modified.
- Artefacts only under `temp/qa/ux30-phase1-shell/`.
- `npm run dev:web` started temporarily for browser smoke.

---

## 12. Recomendación sobre `LOCK-UX30-P1-SHELL`

**Do not release** until **P1-SHELL-001** is fixed and desktop/wide re-validated.

After fix: add `lg:hidden` to `MobileBottomNav`, re-run viewports 1024×768 and 1440×900, confirm sidebar-only shell.

---

## Summary matrix

| Area | Status |
|------|--------|
| Automated tests/build | ✅ |
| Mobile navigation | ✅ |
| Tablet portrait drawer | ✅ |
| Tablet landscape rail | ✅ |
| Desktop/wide sidebar-only | ❌ |
| Deep links / aria-current | ✅ |
| Sheet a11y (focus, Escape) | ✅ |
| Status Bar coexistence | ✅ |
| Catalogue shell smoke | ✅ (with desktop chrome note) |
| Electron TitleBar runtime | ⚠️ Pending |
