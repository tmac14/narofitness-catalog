# APP-CHROME-3.1-TOPBAR-PALETTE-CONTEXT-ACTIONS

## Control

- Track: `APP-PLATFORM-UX-3.0`
- Protocol: `IMPLEMENTATION`
- Owner: Agent 1B (phase 1); Agent 1A (phase 2)
- Validator: Automated desktop tests/build + web visual smoke
- Status: `VALIDATED`
- Priority: `COMPLETED_SLICE`
- Created: 2026-06-13
- Last updated: 2026-06-13

## Objective

Add a global command palette (`Ctrl+K` / top-bar trigger) and a contextual route-actions
slot (0–2 compact actions) to the fixed `AppTopBar`, with catalog editor as first route target.

## Context and Diagnosis

- Distilled context: `APP-CHROME-3.0-MAIN-TOPBAR-BRAND-SYSTEM` delivered brand lockup and
  window controls; route labels removed as redundant with sidebar/bottom nav.
- Root problem: top bar lacked actionable value; preview/export lived only in page headers.
- Approval source: explicit user instruction — CHROME-D31.

## Plan

### Phase 1 — Agent 1B — VALIDATED

Top bar layout, command palette, route-actions registration API, Layout wiring, tests.

### Phase 2 — Agent 1A — VALIDATED

Catalog editor Preview + Export in top bar; header dedupe on tablet+; mobile inline actions preserved.

## Files Changed (full task)

**Phase 1:** `AppTopBar.tsx`, `AppCommandPalette.tsx`, `topbar/*`, `context/*`,
`lib/commandPalette.ts`, `lib/shellNav.ts`, `Layout.tsx`, CSS tokens, related tests.

**Phase 2:** `CatalogEditorPage.tsx`, `CatalogEditorHeader.tsx`,
`lib/catalogEditorHeaderRouteActions.test.tsx`.

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| Top bar layout: brand · drag · route actions · ⌘K · controls | PASS |
| Command palette + keyboard shortcut | PASS |
| Entity search (catalogs/variants/suppliers) | PASS |
| Route-actions API (0–2, auto-clear) | PASS |
| Catalog Preview + Export in top bar | PASS |
| Header dedupe ≥ sm; mobile inline preserved | PASS |
| Sidebar/bottom nav/status bar unchanged | PASS |
| Desktop tests/build/control validate | PASS |

## Validation and Evidence

- `EVID-UX30-CHROME-002` — phase 1 — `PASS_WITH_NOTES` (web smoke not run)
- `EVID-UX30-CHROME-003` — phase 2 + full task — `PASS_WITH_NOTES` (web smoke not run)
- Final metrics: **393** desktop tests, build PASS, control validate PASS

## Responsive dedupe (phase 2)

- ≥ `sm`: inline Preview/Export hidden when `hideInlineRouteActions` (`sm:hidden` on action group).
- < `sm`: inline actions remain for touch access.
- Preview mode: no top-bar registration; header shows “Volver a catálogos”.

## Risks and Follow-Ups

- Optional web smoke on `/catalogs/:id` top-bar actions.
- Entity search caching if catalog/supplier lists grow large.
- Future slices: route actions for product detail, import, etc.

## Current State

- State: `VALIDATED`
- Next safe action: none for this task
