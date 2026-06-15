# APP-PLATFORM-UX30-P3-CATEGORIES

## Control

- Track: APP-PLATFORM-UX-3.0
- Owner: agent-frontend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths:
  - apps/desktop/src/pages/CategoriesPage.tsx
  - apps/desktop/src/components/categories/CategoryFormCard.tsx
  - apps/desktop/src/lib/categoriesPageFormResponsive.test.tsx
- Validator: python -m ordia.cli validate --project
- Status: VALIDATED
- Priority: high
- preferred_intent: implement_ui
- model_tier: T1
- model_approval: "Default T1 — categories form UI slice (2026-06-14)"
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Apply UX30 Phase 3 touch-first patterns to Categories form and page shell (tree already UX30-ready).

## Context

- Prior slices: Settings + Dashboard **VALIDATED**.
- Discovery: `CategoryTree` already has `min-h-11` nodes; form card and delete dialog footer need Settings/Dashboard parity.
- User **Continuamos con la siguiente next safe action** (2026-06-14) authorizes Categories form polish per `ORCHESTRATION_STATE` §0.

## Plan

1. `CategoryFormCard`: `w-full max-w-md`, touch fields, stacked action buttons.
2. `CategoriesPage`: `usePlatform()`, `ux30-categories-page`, stacked delete dialog footer.
3. Regression tests (form contract).

- Plan status: APPROVED (user continue next safe action)

## Scope

- Allowed: Categories page/form components listed above.
- Blocked: `lib/api.ts`, catalog-builder, ProductDetail.

## Next Safe Action

None — task **VALIDATED**.

## Evidence

- EVID-UX30-P3-CATEGORIES-001 — tests 5/5 (form+tree), typecheck PASS, desktop build PASS
