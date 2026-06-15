# SOURCE-CATALOG-DP-PHASE2F-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2F slice: section divider full-bleed replace (8 FDL category pages).

## Decision

**SC-DP-SLICE-11** — `direct.section_cover_replace` on recipe `covers.sections`; asset or branded stub per `section_key`.

## Rationale

- Completes cover layer before table recompose.
- Reuses cover_render + asset resolver from 2E.
- Assets still not bundled; stubs prove all 9 cover pages transform.
