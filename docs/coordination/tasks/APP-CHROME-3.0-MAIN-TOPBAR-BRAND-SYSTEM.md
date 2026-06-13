# APP-CHROME-3.0-MAIN-TOPBAR-BRAND-SYSTEM

## Control

- Track: `APP-PLATFORM-UX-3.0`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex (Agent 1B scope — app chrome / layout)
- Validator: automated desktop tests/build + web visual smoke
- Status: `VALIDATED`
- Priority: `ACTIVE_UI_TRACK`
- Created: 2026-06-13
- Last updated: 2026-06-13

## Objective

Implement App Chrome 3.0 main top bar with HTML/CSS brand lockup (`NAROCATALOG` /
`by NAROFITNESS`), local Rajdhani typography, route context, and Electron window
controls integrated into a premium dark technical shell.

## Context and Diagnosis

- Distilled context: Phase 1 shell existed but the Electron title bar felt generic
  (plain text + small mark, no product identity).
- Root problem: missing brand system, no selectable HTML lockup, fonts from CDN,
  top bar hidden outside Electron, duplicated route label on tablet portrait.
- Approval source: explicit user task packet with `Protocol: CODEX_IMPLEMENTATION`.

## Plan

1. Add local Rajdhani (500/700) under `public/assets/fonts/rajdhani/`.
2. Create `BrandLockup` + `AppTopBar` with route context and window controls.
3. Apply responsive chrome tokens (64px desktop / 56px mobile-tablet).
4. Wire into global `Layout`; extract `shellNav` helpers.
5. Follow-ups: local Inter, tablet portrait route dedupe, explicit Tailwind
   orientation variants, logo load hint (no asset modification).
6. Validate with desktop tests, build, and web smoke.

- Plan status: `APPROVED`
- Approval date: 2026-06-13

## Scope

- Allowed: layout/topbar, brand lockup, CSS tokens, Tailwind config, local fonts,
  `public/brand/logos/09_catalog_grid_equipment_tiles_nr.png`, related tests.
- Blocked: backend, API, importer, parser, grouping, PDF, jobs, coordination
  docs except limited control updates.

## Actual Files Changed

- `public/assets/fonts/rajdhani/*`
- `public/assets/fonts/inter/*` (follow-up — remove Google Fonts CDN)
- `apps/desktop/src/components/brand/BrandLockup.tsx`
- `apps/desktop/src/components/AppTopBar.tsx`
- `apps/desktop/src/lib/shellNav.ts`
- `apps/desktop/src/lib/shellNav.test.ts`
- `apps/desktop/src/components/Layout.tsx`
- `apps/desktop/src/index.css`
- `apps/desktop/src/theme/narofitness-tokens.css`
- `apps/desktop/tailwind.config.cjs`
- `apps/desktop/index.html`
- Removed: `apps/desktop/src/components/TitleBar.tsx`

## Dependencies and Locks

- Dependencies: UX 3.0 Phase 1 shell (`LOCK-UX30-P1-SHELL` released).
- Locks: none required; parallel-safe frontend-only scope.
- Parallel safety: `SAFE_FRONTEND_CHROME_ONLY`

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| Rajdhani local woff2, no CDN | PASS |
| Inter local woff2, no Google Fonts CDN in app | PASS |
| HTML selectable lockup text | PASS |
| Logo mark separate image (`09_catalog…`) | PASS |
| Responsive desktop/tablet/mobile | PASS |
| Window controls in Electron | PASS (unchanged behavior) |
| Sidebar/status bar not broken | PASS |
| `npm test --prefix apps/desktop` | PASS (370 tests) |
| `npm run build --prefix apps/desktop` | PASS |

## Evidence

- `EVID-UX30-CHROME-001` — desktop tests + production build (this packet).
- Web visual smoke: `http://127.0.0.1:5173` — top bar brand lockup verified.

## Validation Commands

```bash
npm test --prefix apps/desktop
npm run build --prefix apps/desktop
npm run control:validate
```

## Risks and Follow-ups

| Item | Disposition |
|------|-------------|
| Inter CDN | **Closed** — migrated to `public/assets/fonts/inter/` |
| Tablet portrait route duplication | **Closed** — route only in top bar |
| `tablet:landscape` / `tablet:portrait` ambiguity | **Closed** — explicit `tablet-landscape` / `tablet-portrait` Tailwind variants |
| Logo PNG ~1.1 MB | **Deferred** — cannot modify `09_` asset per brand rules; needs approved derivative asset task |
| Manual Electron drag-region QA | Optional — web smoke only in this validation |

## Current State

- State: `VALIDATED`
- Next safe action: none for this task; continue UX30 track per registry priority
