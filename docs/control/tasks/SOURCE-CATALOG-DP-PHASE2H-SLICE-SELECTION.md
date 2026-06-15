# SOURCE-CATALOG-DP-PHASE2H-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2H slice: full product-content price overlay via text search.

## Decision

**SC-DP-SLICE-13** — `price_overlay.scope: product_content` (all snapshot priced pages).

## Rationale

- Reuses text_search_v1 from 2G without table recompose.
- Regression page proof extended to full catalog priced pages.
- Table recompose deferred to Phase 2I+.
