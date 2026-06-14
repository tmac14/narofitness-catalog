# FRONTEND-LINT-TYPE-FORMAT-REMEDIATION

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: frontend quality commands, desktop tests/build, runtime smoke, and
  project-control validation
- Status: `CLOSED`
- Priority: `SEQUENTIAL_MODERNIZATION_PR_06`
- Created: 2026-06-13
- Last updated: 2026-06-13

## Objective

Remove the measured frontend lint, type, and format debt without weakening
quality rules or changing intended product behavior.

## Context and Diagnosis

- Distilled context: PR-05 configured the approved frontend quality stack and
  recorded an audit-only baseline.
- Evidence available: `EVID-CTRL-008`.
- Root problem:
  - ESLint: `121` errors and `18` warnings across `45` files;
  - Prettier: `194` files needing formatting;
  - TypeScript: `57` errors across `19` files.
- ESLint concentration:
  - async promise handling: `29` no-misused-promises, `19`
    no-floating-promises, `13` require-await;
  - React state/effects: `26` set-state-in-effect and `4` exhaustive-deps;
  - React Refresh export boundaries: `14` warnings;
  - typing/cleanup: remaining unsafe, unused, unbound, empty-object, and
    assertion findings.
- TypeScript concentration: contract fixture drift, product variant list/detail
  type mixing, PDF canvas nullability/API drift, and smaller local typing
  defects.
- Assumptions: quality remediation must preserve contracts and behavior; tests
  may be updated only to express current required types or validate a corrected
  refactor.

## Plan

1. Apply deterministic Prettier formatting to `apps/desktop/**`.
2. Fix TypeScript errors without weakening strictness or API contracts.
3. Fix ESLint findings by root cause:
   - make async event boundaries explicit;
   - replace effect-driven derived/reset state with event-driven, keyed, or
     derived-state designs;
   - separate React component exports from helpers/constants where required;
   - improve types and remove dead code.
4. Re-run lint, format, and typecheck after each coherent batch.
5. Run desktop tests/build and runtime smoke on behaviorally touched surfaces.
6. Confirm the Python debt baseline and non-blocking CI policy remain outside
   this PR.

- Plan status: `APPROVED`
- Approval source: explicit user start of PR-06
- Approval date: 2026-06-13

## Scope

- Allowed:
  - `apps/desktop/**` source, tests, Electron files, and frontend tooling files;
  - formatting required by the approved Prettier configuration;
  - frontend-focused task/control records under limited update permission.
- Blocked:
  - backend/API contract changes, importer, data, migrations, and Python debt;
  - quality-rule weakening, broad suppressions, permanent baselines, or
    disabling strict TypeScript;
  - dependency hygiene, blocking CI gates, and paused-workstream feature work;
  - intentional UX, catalogue, PDF, or product behavior changes.
- Probable write paths: `apps/desktop/**`.
- Actual files changed:
  - `apps/desktop/src/pages/CatalogsPage.tsx`
  - `apps/desktop/src/pages/CategoriesPage.tsx`
  - `apps/desktop/src/pages/ImportPage.tsx`
  - `apps/desktop/src/pages/CatalogEditorPage.tsx`
  - `apps/desktop/src/hooks/useDashboardData.ts`
  - `apps/desktop/src/lib/api.ts`
  - `apps/desktop/src/lib/exportPdf.ts`
  - `apps/desktop/src/components/catalog-builder/CatalogPresentationBuilder.tsx`
  - `apps/desktop/src/context/StatusBarContext.tsx`
  - `apps/desktop/src/context/useStatusBar.ts`
  - `apps/desktop/src/context/statusBarContextShared.ts`
  - `apps/desktop/src/components/dashboard/DashboardSystemAlert.tsx`
  - `apps/desktop/src/components/dashboard/DashboardProcessModule.tsx`
  - `apps/desktop/src/components/status-bar/AppStatusBar.tsx`
  - `apps/desktop/src/components/status-bar/ProcessCenterPanel.tsx`
  - `apps/desktop/src/pages/Dashboard.tsx`
  - `apps/desktop/src/components/products/ProductMasterCard.tsx`
  - `apps/desktop/src/components/products/ProductMasterCardList.tsx`
  - `apps/desktop/src/components/products/ProductVariantExpandSheet.tsx`
  - `apps/desktop/src/components/products/productMasterCardMeta.ts`
  - `apps/desktop/src/components/products/productVariantExpandSheetFocus.ts`
  - `apps/desktop/src/components/ui/badge.tsx`
  - `apps/desktop/src/components/ui/button.tsx`
  - `apps/desktop/src/components/ui/badgeVariants.ts`
  - `apps/desktop/src/components/ui/buttonVariants.ts`
  - `apps/desktop/src/pages/ProductsPage.tsx`
  - frontend tests under `apps/desktop/src/lib/**` covering responsive
    products, product detail metadata, catalog preview/export, API fixtures,
    jobs, and source-page flows

## Dependencies and Decisions

- Dependencies: `ENGINEERING-QUALITY-TOOLING` / `EVID-CTRL-008`.
- Dependents: PR-10 blocking CI enforcement.
- Required decisions: none.
- Decision-log references: `ENG-D001`.

## Parallel Safety and Locks

- Parallel safety: `SERIALIZED_FRONTEND_BASELINE`; no frontend implementation
  may run in parallel because any edit would invalidate the remediation
  baseline.
- Active/in-flight conflicts checked: no active tasks, assignments, or locks.
- Locks required: `LOCK-PR06-DESKTOP-REMEDIATION` on `apps/desktop/**`.
- Must not run in parallel with: Agent 1A, Agent 1B, or Agent 4 frontend writes.

## Acceptance Criteria

- [x] `npm run lint:frontend` passes with zero errors and warnings.
- [x] `npm run format:check:frontend` passes.
- [x] `npm run typecheck:frontend` passes without weakening strictness.
- [x] Desktop tests and production build pass.
- [x] Runtime smoke passes for behaviorally touched surfaces.
- [x] No quality rule is weakened or broadly suppressed.
- [x] No backend, Python, API contract, or paused feature scope is changed.
- [x] Required evidence is durable and indexed.
- [x] No required evidence pending.

## Validation and Evidence

- Validation plan:
  - canonical frontend lint, format check, and typecheck;
  - desktop Vitest suite and Vite production build;
  - focused runtime smoke after semantic React refactors;
  - `npm run control:test` and `npm run control:validate`.
- Evidence IDs:
  - `EVID-CTRL-009`
- Result: `PASS`
- Validation result:
  - `npm run lint:frontend` -> PASS
  - `npm run format:check:frontend` -> PASS
  - `npm run typecheck:frontend` -> PASS
  - `npm run test --prefix apps/desktop` -> PASS (`47/47` files, `367/367`
    tests)
  - `npm run build --prefix apps/desktop` -> PASS
  - `npm run control:validate` -> PASS
  - runtime smoke -> PASS on `Dashboard`, `Products` mobile cards and variant
    Sheet, `Catalogs`, `CatalogEditor`, `Import`, and `Categories` with zero
    browser console errors
- Notes:
  - In this environment, Vitest and the Vite production build required
    execution outside the sandbox because `esbuild` returned `spawn EPERM`
    inside the sandbox.

## Risks and Follow-Ups

- Risks:
  - formatting creates a broad but deterministic diff;
  - effect refactors can alter reset/focus timing if not validated;
  - contract-fixture fixes can conceal a real contract mismatch if handled
    with casts instead of correct builders/types.
- Follow-ups:
  - PR-07 Python Ruff remediation;
  - PR-08 Python type-safety remediation;
  - PR-09 dependency hygiene;
  - PR-10 blocking CI gates.

## Next Safe Action

No action; PR-06 is implemented and validated. Select the next explicit task
and protocol before any new writes.
