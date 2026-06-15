# APP-PLATFORM-UX30-PHASE-3-SLICE-SELECTION

## Control

- Track: APP-PLATFORM-UX-3.0
- Owner: orchestrator
- Runtime: ONLY_CURSOR
- Protocol: ORCHESTRATION
- planned_write_paths: []  # discovery — no product edits
- Validator: npm run ordia:validate
- Status: VALIDATED
- Priority: high
- preferred_intent: discover
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Select the first **Phase 3** slice (Forms & detail surfaces) for APP-PLATFORM-UX-3.0 and produce an Ordia-ready implementation plan with locks, agent owner, and validation gates.

## Context and Diagnosis

**Phase 2 status:** COMPLETE (2A–2D VALIDATED). UX30-D7 DECIDED (2B → 2C).

**Phase 3 scope (roadmap):** Forms & detail surfaces — explicitly **out of Phase 2** scope. Surfaces mentioned: ProductDetail, Import, Dashboard, Settings.

**Collision scan:**

| Surface | UX30 Phase 3 fit | Track status | Risk |
|---------|------------------|--------------|------|
| `SettingsPage.tsx` | Strong — pure forms (backup, logo, prefs) | No paused work | **Low** — no API contract changes expected |
| `Dashboard.tsx` | Medium — layout/shell already UX30 Phase 1 | DASHBOARD-UX-1B **CLOSED** | Low — responsive polish only |
| `ImportPage.tsx` | Phase 4 in roadmap | UX30-D2 undecided (mobile import scope) | **Blocked** until UX30-D2 |
| `ProductDetailPage.tsx` | Detail/forms heavy | PROD-DETAIL-UX-V2 **PAUSED/DEFERRED** | **High** — guardrails forbid reactivation |
| `CategoriesPage.tsx` | Tree/detail hybrid | Phase 2B VALIDATED (list); detail pane may need Phase 3 | Medium — partial overlap with 2B |

**Code signals:**

- `SettingsPage.tsx` — 310 lines; forms, dialogs, file upload; **no** `useDataViewMode` / responsive UX30 patterns yet
- `ProductDetailPage.tsx` — complex; paused PROD-DETAIL-UX-V2 contract
- Tests exist for list surfaces (P2A–2D); no `settingsPageResponsive.test.tsx`

**Assumptions:**

- User wants to **demonstrate full Ordia lifecycle** on Narofitness, starting with Phase 3.
- Implementation agent: `agent-frontend` (`apps/desktop/`).
- No `lib/api.ts` changes in first slice (Agent 4 not required).

## Plan

1. **Discovery** (this packet): compare Phase 3 slice options — **complete**.
2. **Plan** (`plan` intent): user picks slice; fill locks + acceptance criteria.
3. **Approve** → `LOCKS_CONFIRMED` → `MODEL_TIER_APPROVED` → `IN_FLIGHT`.
4. **Implement** with `implement_ui` or `implement_ux` intent.
5. **Validate** → `VALIDATED` + evidence in `temp/qa/`.

### Recommendation (Plan Mode)

**Primary recommendation: `SettingsPage` first (slice ID: UX30-P3-SETTINGS`)**

| Criterion | Settings | Dashboard | Categories detail |
|-----------|----------|-----------|-------------------|
| Paused-track risk | None | None | Low |
| Pattern reuse from P2 | Forms + empty/error states | Shell already done | Tree + detail split |
| Touch-first gap | High (dense desktop form) | Medium | Medium |
| Scope clarity | High | Medium | Medium |
| Agent scope fit | `agent-frontend` only | `agent-frontend` | `agent-frontend` |

**Defer:** ProductDetail (paused), Import (UX30-D2 / Phase 4).

- Plan status: PLAN_READY (pending user slice confirmation)
- Approval source: discovery recommendation
- Approval date: 2026-06-14

## Scope

- Allowed (next phase): `apps/desktop/src/pages/SettingsPage.tsx` and directly related components only.
- Blocked: `ProductDetailPage*`, `catalog-builder/**`, `lib/api.ts`, `apps/api/**`.
- Probable write paths (if Settings approved):
  - `apps/desktop/src/pages/SettingsPage.tsx`
  - `apps/desktop/src/components/**` (new responsive helpers if needed)
  - `apps/desktop/src/**/*.test.tsx`

## Dependencies and Decisions

- Dependencies: Phase 2 COMPLETE; UX30-D7 DECIDED.
- Required decisions: User confirms Phase 3 slice (recommended: Settings).
- Decision-log references: UX30-D7

## Parallel Safety and Locks

- Parallel safety: single frontend slice; no `ready_for_parallel` batch yet.
- Locks required (after approval): per-file locks on `SettingsPage.tsx` before implementation.

## Acceptance Criteria

- [ ] User confirms Phase 3 slice.
- [ ] Task transitions to `APPROVED` with explicit `planned_write_paths`.
- [ ] Responsive/touch-first behavior on mobile and tablet for chosen surface.
- [ ] `npm run typecheck:frontend` + `npm test` + build pass.
- [ ] QA evidence indexed before `VALIDATED`.

## Validation and Evidence

- Validation plan: frontend test suite + manual QA checklist for chosen surface.
- Commands: `npm run typecheck:frontend`, `npm run test --prefix apps/desktop`, `npm run desktop:build`
- Evidence IDs: (pending implementation)
- Result: DISCOVERY complete — awaiting user slice decision

## Risks and Follow-Ups

- Risks: Choosing ProductDetail or Import reactivates paused tracks.
- Follow-ups: After Settings (if approved), consider Dashboard responsive polish or Categories detail pane.

## Next Safe Action

**User confirmed:** **SettingsPage** (2026-06-14). Decision **UX30-P3-SLICE** recorded. Implementation task: `APP-PLATFORM-UX30-P3-SETTINGS`.
