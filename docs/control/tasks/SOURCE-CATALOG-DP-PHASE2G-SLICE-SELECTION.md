# SOURCE-CATALOG-DP-PHASE2G-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2G slice: regression-page price overlay via text search (page 11).

## Decision

**SC-DP-SLICE-12** — `direct.price_overlay` text_search_v1 on recipe `price_overlay.pages: [11]`.

## Rationale

- Snapshot lacks per-slot geometry; text search matches FDL parser price format.
- Page 11 is dense regression baseline page.
- Full catalog price overlay deferred to Phase 2H+.
