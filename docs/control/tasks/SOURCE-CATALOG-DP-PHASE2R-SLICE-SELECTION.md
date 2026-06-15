# SOURCE-CATALOG-DP-PHASE2R-SLICE-SELECTION

## Control

- Track: PHASE-2-PARITY
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2R slice: wire snapshot price-slot bboxes into preview renderer.

## Decision

**SC-DP-SLICE-24** — `geometry_source: snapshot_bbox_v1` for price overlay; merged rects for cell borders; renderer **0.13.0**.

## Deferred

- Row-level full cell redraw from row_bbox
- Image group geometry
