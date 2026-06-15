# SOURCE-CATALOG-DP-PHASE2N-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2N slice: expand price-cell borders to all product-content pages.

## Decision

**SC-DP-SLICE-19** — `price_cell_border.scope: product_content`; reuse overlay `price_rects_by_page` on every priced page.

## Deferred

- Full row/cell geometry redraw (non-price columns).
- Image cell collage and border redraw after images.
