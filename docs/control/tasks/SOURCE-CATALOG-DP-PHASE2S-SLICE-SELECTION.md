# SOURCE-CATALOG-DP-PHASE2S-SLICE-SELECTION

## Control

- Track: PHASE-2-PARITY
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2S slice: row-level cell borders from snapshot `rows[].bbox`.

## Decision

**SC-DP-SLICE-25** — `row_cell_border` capability via `snapshot_row_bbox_v1` on `regression_pages` (13 pages).

## Deferred

- Row borders on all product-content pages (Phase 2T)
- Image cell geometry
