# SOURCE-CATALOG-DP-PHASE2K-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2K slice: expand table presentation chrome to all regression pages.

## Decision

**SC-DP-SLICE-16** — `table_recompose.scope: regression_pages`; footer on all 13 pages; ribbon only on first (page 3).

## Rationale

- Extends 2J chrome without cell redraw.
- Honors `section_start_ribbon: rectangular_centered_first_content_page_only`.
- Cell borders and image cells remain Phase 2L+.
