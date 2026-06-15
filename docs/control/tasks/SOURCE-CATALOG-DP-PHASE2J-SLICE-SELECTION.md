# SOURCE-CATALOG-DP-PHASE2J-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2J slice: regression-page table presentation chrome (footer + section ribbon).

## Decision

**SC-DP-SLICE-15** — `direct.table_recompose` `presentation_chrome_v1` on page 11; full cell redraw deferred.

## Rationale

- Proves table_recompose hook in renderer pipeline before semantic redraw.
- Matches baseline footer/ribbon intent from recipe fixture.
- Cell borders and image cells remain Phase 2K+.
