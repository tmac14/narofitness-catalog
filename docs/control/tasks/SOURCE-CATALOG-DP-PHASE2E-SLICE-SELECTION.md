# SOURCE-CATALOG-DP-PHASE2E-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2E slice: main cover full-bleed replace with asset resolution + branded stub fallback.

## Decision

**SC-DP-SLICE-10** — `direct.main_cover_replace` on page 1 only; section covers deferred.

## Rationale

- Cover assets (`wireframes/portadas-fdl`) not bundled; stub proves renderer path without blocking on assets.
- Asset resolver ready for when files are mounted via `ADAPTATION_ASSETS_ROOT`.
- Section dividers and table recompose remain Phase 2F+.
