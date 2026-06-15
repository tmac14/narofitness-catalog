# APP-PLATFORM-UX30-P3-SETTINGS

## Control

- Track: APP-PLATFORM-UX-3.0
- Owner: agent-frontend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths:
  - apps/desktop/src/pages/SettingsPage.tsx
  - apps/desktop/src/hooks/useDataViewMode.ts
  - apps/desktop/src/lib/settingsPageResponsive.test.tsx
- Validator: npm run ordia:validate
- Status: VALIDATED
- Priority: high
- preferred_intent: implement_ui
- model_tier: T1
- model_approval: "Default T1 — forms-only UI slice (2026-06-14)"
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Apply UX30 Phase 3 touch-first responsive patterns to `SettingsPage` (forms, backup, dialogs).

## Context and Diagnosis

- User confirmed Phase 3 slice: **Settings** (UX30-P3).
- Prior work: Phase 2 list surfaces complete; Settings lacked `min-h-11` touch targets and mobile-full-width actions.

## Plan

1. Add `usePlatform()` hook for platform-aware layout.
2. Touch-first fields/buttons (`min-h-11`, full-width on mobile).
3. Responsive dialog footer stacking.
4. Regression tests in `settingsPageResponsive.test.tsx`.

- Plan status: APPROVED
- Approval source: user confirmation (2026-06-14)

## Scope

- Allowed: Settings page + hook + tests only.
- Blocked: `lib/api.ts`, `ProductDetailPage`, catalog-builder.

## Acceptance Criteria

- [x] Touch targets ≥44px on interactive controls.
- [x] Full-width primary actions on mobile (`w-full sm:w-auto`).
- [x] Frontend tests pass.
- [x] Build pass.
- [x] Evidence indexed.

## Validation and Evidence

- Commands: `npm test --prefix apps/desktop`, `npm run typecheck:frontend`, `npm run desktop:build`
- Evidence IDs: EVID-UX30-P3-SETTINGS-001
- Result: PASS — tests 3/3, typecheck PASS, vite build PASS

## Next Safe Action

None — task **VALIDATED**. Orchestrator selects next Phase 3 slice via `discover` + `PROFILE.md` when authorized.
