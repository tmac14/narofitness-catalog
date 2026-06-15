# SOURCE-CATALOG-DP-PHASE2M-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2M slice: price-cell border redraw on regression pages.

## Decision

**SC-DP-SLICE-18** — `price_cell_border` capability via `text_search_v1` on `regression_pages` subset; footer on all product pages unchanged.

## Deferred

- Full row/cell geometry from snapshot bboxes.
- Image cell collage and border redraw after images.
