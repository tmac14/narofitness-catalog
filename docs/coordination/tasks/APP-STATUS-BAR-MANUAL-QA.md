# APP-STATUS-BAR-MANUAL-QA

## Control

- Track: `APP-WIDE-UX`
- Status: `PAUSED`
- Resume gate: explicit user authorization
- Owner on resume: `Agent 1B - App-Wide Accessible UX/UI`
- Manual checklist: `docs/MANUAL_QA_APP_WIDE.md`

## Objective

Complete the pending visual/manual QA for the implemented App Status Bar and
Process Center health panel.

## Current Proven State

- Implementation and automated tests/build completed.
- Historical SHARED-4 lock released.
- ProcessRegistry, jobs, PDF background jobs, and backend changes were not part
  of the delivered slice.

## Required Validation

- Run the Status Bar checklist in `MANUAL_QA_APP_WIDE.md`.
- Validate layout, responsive behavior, health state, accessibility, and
  Process Center interaction.
- Do not silently expand into future jobs/background processing.

## Next Safe Action

Wait for explicit resume, then create a QA-mode task.
