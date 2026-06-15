# SOURCE-CATALOG-DP-PHASE2L-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2L slice: expand table footer chrome to all product-content pages.

## Decision

**SC-DP-SLICE-17** — `table_recompose.scope: product_content`; footer only (no ribbon); cell borders deferred.

## Deferred

- Table cell border redraw (needs real price-slot geometry).
- Image cell collage and border redraw.
