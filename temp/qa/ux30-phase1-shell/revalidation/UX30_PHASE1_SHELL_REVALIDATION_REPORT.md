# UX 3.0 Phase 1 Shell — Revalidation Report

**Task ID:** `APP-PLATFORM-UX-3.0-PHASE-1-SHELL-REVALIDATION`  
**Agent:** 1A — read-only QA  
**Date:** 2026-06-12  
**Verdict:** `UX30_PHASE1_SHELL_REVALIDATION_PASS_WITH_NOTES`

---

## 1. Estado

`UX30_PHASE1_SHELL_REVALIDATION_PASS_WITH_NOTES`

**P1-SHELL-001 is fixed.** All viewport boundary checks pass with exactly one navigation pattern per band and no dual chrome. Electron TitleBar touch targets verified via CDP. Note: minimize/close clicks and drag gesture were not executed during QA (session preservation); IPC handlers and CSS regions confirmed by code + CDP metrics.

---

## 2. Tests y build

| Command | Result |
|---------|--------|
| `npm run test --prefix apps/desktop` | **PASS** — 45 files, **351/351** tests |
| `npm run build --prefix apps/desktop` | **PASS** — built in ~11.5s |

**Fix verified in source:** `MobileBottomNav` class `tablet:hidden lg:hidden` (`Layout.tsx:162`).

---

## 3. Resultado por límite de viewport

| Viewport | Expected | Measured | Pass |
|----------|----------|----------|------|
| 390×844 | bottom nav only | `patterns: ["bottomNav"]`, `dualNav: false` | ✅ |
| 639×800 | bottom nav only | `patterns: ["bottomNav"]` | ✅ |
| 640×800 portrait | drawer header only | `patterns: ["tabletHeader"]`, bottom nav hidden | ✅ |
| 640×360 landscape | rail only | `patterns: ["rail"]` | ✅ |
| 1023×768 landscape | rail only | `patterns: ["rail"]` | ✅ |
| **1024×768** | **sidebar only** | `patterns: ["sidebar"]`, `bottomNav: false`, `p1Shell001Fixed: true` | ✅ |
| **1440×900** | **sidebar only** | `patterns: ["sidebar"]`, `bottomNav: false`, `p1Shell001Fixed: true` | ✅ |

**Never `dualNav: true`** across all boundary probes.

---

## 4. P1-SHELL-001

| Check | Before fix | After fix |
|-------|------------|-----------|
| 1024×768 bottom nav | Visible + sidebar | **Hidden** — sidebar only |
| 1440×900 bottom nav | Visible + sidebar | **Hidden** — sidebar only |
| Mobile/tablet bands | Unchanged | Unchanged — still correct |

**Status:** **RESOLVED** ✅

Artifacts: `viewport-1024x768-fixed.png`, `viewport-1440x900-fixed.png`, JSON metrics per viewport.

---

## 5. TitleBar Electron

**Method:** Electron launched with `--remote-debugging-port=9333`; CDP script `cdp-titlebar-check.mjs` (artifact only).

| Viewport | Minimize | Close | Title overflow |
|----------|----------|-------|----------------|
| 768×1024 (tablet) | **44×44** | **44×44** | No |
| 1024×768 (desktop) | **32×32** | **32×32** | No |
| 1440×900 (wide) | **32×32** | **32×32** | No |

- `window.narocatalog.isElectron`: true in Electron context ✅
- `.titlebar-drag` / `.titlebar-no-drag` regions present ✅
- IPC `window-minimize` / `window-close` handlers in `electron/main.cjs` ✅

**Note:** Minimize/close buttons not clicked during QA to avoid disrupting the session. Drag gesture not manually exercised.

---

## 6. Catalogue smoke (shell-only)

**Catalog:** FDL Tarifa 2026 (`b425bbbe-880e-4421-beb0-9471f57216fd`)

| Viewport | `/catalogs` | `/catalogs/:id` |
|----------|-------------|-----------------|
| 390×844 | Catálogos active; bottom nav only; no H-scroll | Editor loads; `aria-current` on Catálogos; Export PDF visible; no dual nav |
| 1024×768 | Sidebar only; Catálogos active | Editor OK; no bottom nav |
| 1440×900 | — | Editor OK; sidebar only |

Mobile “Más” sheet: opens with 4 secondary destinations ✅

---

## 7. Defectos

| ID | Severity | Description |
|----|----------|-------------|
| — | — | **No new defects** |
| REV-NOTE-01 | Info | TitleBar minimize/close click and drag not manually exercised |
| REV-NOTE-02 | Info | Initial DB empty; FDL catalog used after API repopulation (environment) |

**P1-SHELL-001:** closed.

---

## 8. Artefactos

```
temp/qa/ux30-phase1-shell/revalidation/
├── UX30_PHASE1_SHELL_REVALIDATION_REPORT.md
├── viewport-390x844.json / .png
├── viewport-639x800.json
├── viewport-640x800.json
├── viewport-640x360.json
├── viewport-1023x768.json
├── viewport-1024x768.json / viewport-1024x768-fixed.png
├── viewport-1440x900.json / viewport-1440x900-fixed.png
├── catalog-list-mobile-390x844.png
├── catalog-editor-mobile-390x844.png
├── catalog-editor-desktop-1024x768.png
├── catalog-editor-desktop-1440x900.png
├── electron-titlebar.json
└── cdp-titlebar-check.mjs (QA helper only)
```

---

## 9. Confirmación read-only

No application source, tests, or config modified. QA helper script and artefacts live only under `temp/qa/ux30-phase1-shell/revalidation/`. `db:seed:stress` was run once to populate test data when DB was empty (environment setup, not code change).

---

## 10. `LOCK-UX30-P1-SHELL`

**Recommend release** — P1-SHELL-001 fixed and revalidated; remaining Phase 1 shell behaviour matches spec. Phase 1 may move to **VALIDATED** pending team acceptance of TitleBar click/drag note.

---

## Confirmaciones adicionales

- Status Bar visible; no overlap with bottom nav on mobile (`statusBarAboveBottomNav: true` at 390×844) ✅
- No shell horizontal overflow on probed surfaces ✅
- Deep link `/catalogs/:id` keeps Catálogos `aria-current="page"` ✅
