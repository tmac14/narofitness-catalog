# SOURCE-CATALOG-DP-PHASE2D-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2D slice: pass-through PDF preview artifact + cover plan in manifest (no cover rendering, no table recompose).

## Decision

**SC-DP-SLICE-9** — PDF pass-through from immutable source + recipe cover plan metadata.

## Rationale

- Proves end-to-end preview artifact pipeline before full 65-page recompose.
- Cover assets not bundled in repo; plan records intent without unsafe rendering.
- Table recompose and cover application deferred to Phase 2E+.

## Next

Phase 2E — cover asset resolution or minimal page-1 replacement when assets available.
