# CATALOGUE-PRESENTATION-MANUAL-QA

## Control

- Track: `CATALOGUE-PRESENTATION`
- Status: `PAUSED`
- Resume gate: explicit user authorization
- Owner on resume: `Agent 1A - Catalogue Builder UI/UX`
- Registry: `docs/control/CATALOG_PRESENTATION_BACKLOG.md`

## Objective

Complete manual visual QA for the integrated
`show_description_column` catalogue-presentation option.

## Current Proven State

- Backend, PDF, and UI integration complete.
- Paginated PDF preview already QA PASS.
- Toggle-on/off preview/export visual validation remains pending.
- Background jobs/export queue are not part of this task.

## Required Validation

- Toggle off/on and persist.
- Confirm preview refresh and dirty-state behavior.
- Confirm Description column appears only in intended simple-product tables.
- Confirm preview/export parity.

## Next Safe Action

Wait for explicit resume, then create a catalogue QA task.
