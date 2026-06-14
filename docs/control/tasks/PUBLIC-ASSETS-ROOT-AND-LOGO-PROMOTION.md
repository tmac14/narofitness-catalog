# PUBLIC-ASSETS-ROOT-AND-LOGO-PROMOTION

## Control

- Track: `APP-PLATFORM-UX-3.0`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex (Agent 1B scope — shared app assets foundation)
- Validator: automated desktop tests/build + `control:validate`
- Status: `VALIDATED`
- Priority: `ACTIVE_UI_TRACK`
- Created: 2026-06-13
- Last updated: 2026-06-13

## Objective

Establish a canonical root `public/` directory for shared runtime assets and
promote the approved logo pack from `wireframes/assets/logos/` into
`public/brand/logos/`.

## Context and Diagnosis

- Distilled context: the monorepo had design assets under `wireframes/` but no
  runtime asset root shared by web, desktop, and future mobile clients.
- Root problem: Vite had no `publicDir`, logos lived only in wireframes, and UI
  code had no typed asset registry.
- Approval source: explicit user instruction with `Protocol: CODEX_IMPLEMENTATION`.

## Plan

1. Create `public/` layout (`brand/logos`, `icons`, reserved `backgrounds/`,
   `placeholders/`).
2. Promote all 17 logos from `wireframes/assets/logos/`.
3. Derive `public/icons/app-mark.png` from logo `03`.
4. Point Vite `publicDir` to the root `public/`.
5. Add `appAssets.ts` typed paths and `manifest.json` source mapping.
6. Wire favicon and Electron builder icon paths.
7. Validate with desktop tests, build, and control validation.

- Plan status: `APPROVED`
- Approval date: 2026-06-13

## Scope

- Allowed: `public/**`, `apps/desktop/vite.config.ts`, `apps/desktop/index.html`,
  `apps/desktop/electron-builder.config.cjs`, `apps/desktop/src/lib/appAssets.ts`,
  `apps/desktop/src/lib/appAssets.test.ts`.
- Blocked: backend, API, importer, parser, grouping, PDF, jobs, unrelated UI
  refactors.

## Actual Files Changed

- `public/README.md`
- `public/manifest.json`
- `public/brand/logos/*` (17 promoted PNGs)
- `public/icons/app-mark.png`
- `public/backgrounds/.gitkeep`
- `public/placeholders/.gitkeep`
- `apps/desktop/vite.config.ts`
- `apps/desktop/index.html`
- `apps/desktop/electron-builder.config.cjs`
- `apps/desktop/src/lib/appAssets.ts`
- `apps/desktop/src/lib/appAssets.test.ts`

## Dependencies and Locks

- Dependencies: none.
- Locks: none required; parallel-safe assets-only scope.
- Parallel safety: `SAFE_FRONTEND_ASSETS_ONLY`
- Related follow-on: `APP-CHROME-3.0-MAIN-TOPBAR-BRAND-SYSTEM` consumes
  `APP_BRAND_LOGOS.catalogGrid` via `BrandLockup`.

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| Root `public/` exists with documented layout | PASS |
| All 17 wireframe logos promoted to `public/brand/logos/` | PASS |
| `manifest.json` records source → runtime mapping | PASS |
| Vite serves root `public/` in dev and build | PASS |
| Typed `appAssets.ts` paths available to UI | PASS |
| Favicon references `icons/app-mark.png` | PASS |
| Electron builder icon path configured | PASS |
| `npm test --prefix apps/desktop` | PASS |
| `npm run build --prefix apps/desktop` | PASS |
| `npm run control:validate` | PASS |

## Evidence

- `EVID-PUBLIC-001` — full desktop test suite, production build, control
  validation (this packet).

## Validation Commands

```bash
npm run control:validate
npm test --prefix apps/desktop
npm run build --prefix apps/desktop
```

## Risks and Follow-Ups

| Item | Disposition |
|------|-------------|
| Logo PNG weight (~20 MB total) | Deferred — optimize with approved WebP derivatives task |
| Background/placeholder promotion | Deferred — promote from `wireframes/assets/` when visually approved |
| Mobile native asset packaging | Deferred — future shared assets package or per-platform copy |
| Manual Electron installer icon QA | Optional — config only validated in this task |

## Current State

- State: `VALIDATED`
- Next safe action: promote approved backgrounds/placeholders when the visual
  identity pack is ready; consider WebP derivatives for shell logos
