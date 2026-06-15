# SOURCE-CATALOG-DP-PHASE2Q-SLICE-SELECTION

## Control

- Track: PHASE-2-PARITY
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2Q slice: real analyzer geometry for price slots and rows.

## Decision

**SC-DP-SLICE-23** — propagate `text_layout_v1` bboxes from `fdl_pdf_v1` parser into `DocumentAnalysisSnapshot`; analyzer **0.2.0**; `geometry_summary.resolve_rate` on manifest.

## Deferred

- Image group geometry
- Renderer consumption of snapshot bboxes (Phase 2R)
- Full table cell redraw
