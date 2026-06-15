# APP-PLATFORM-UX30-P3-DASHBOARD

## Control

- Track: APP-PLATFORM-UX-3.0
- Owner: agent-frontend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths:
  - apps/desktop/src/pages/Dashboard.tsx
  - apps/desktop/src/components/dashboard/DashboardHero.tsx
  - apps/desktop/src/components/dashboard/DashboardKpiCard.tsx
  - apps/desktop/src/lib/dashboardPageResponsive.test.tsx
- Validator: python -m ordia.cli validate --project
- Status: VALIDATED
- Priority: high
- preferred_intent: implement_ui
- model_tier: T1
- model_approval: "Default T1 — dashboard UI slice (2026-06-14)"
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Apply UX30 Phase 3 touch-first patterns to Dashboard (hero CTAs, KPI link targets, platform hook).

## Context

- Prior slice: `APP-PLATFORM-UX30-P3-SETTINGS` **VALIDATED**.
- Discovery: Categories tree already UX30-ready; Dashboard hero used `size="sm"` without `min-h-11`.
- User **adelante** (2026-06-14) authorizes next Phase 3 slice per `ORCHESTRATION_STATE` §0.

## Plan

1. Hero CTAs: `min-h-11`, full-width mobile.
2. KPI cards: touch link wrapper `min-h-11`.
3. `usePlatform()` on dashboard root.
4. Regression tests.

- Plan status: APPROVED (user adelante)

## Scope

- Allowed: Dashboard components listed above.
- Blocked: `lib/api.ts`, catalog-builder, ProductDetail.

## Next Safe Action

None — task **VALIDATED**.
