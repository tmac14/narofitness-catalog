# SOURCE-CATALOG-DP-PHASE3-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-frontend + agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: DECIDED

## Objective

Select first Phase 3 slice after Phase 2 Preview MVP closure.

## Decision

**SC-DP-SLICE-22** — Phase 3 first slice: **Source document intake shell** (`PHASE3-SOURCE-INTAKE`)

- Surface: upload PDF → show detected profile/capabilities → actions for **Adaptar** vs **Importar**
- Backend: reuse Phase 1/2 APIs (`source-documents`, `adaptations`, `import-preview`)
- Forbidden in slice 1: full Adaptation Studio QA UI, approval workflow, final export

## Rationale

Matches plan Phase 3 exit gate (“launch either path from one source”) with lowest collision vs in-flight `PHASE-2-PARITY` renderer work.

## Next after slice 1

- **SC-DP-SLICE-34** — export list + authorized download APIs
- **SC-DP-SLICE-35** — ephemeral delivery + TTL sweeper
- **SC-DP-SLICE-36** — Adaptation Studio UI: output profile + delivery mode
- **SC-DP-SLICE-37** — approval + final export (persist only)
- Adaptation Studio preview/QA shell (overlaps 36)

Backend parity slices **SC-DP-SLICE-31..33** (renderer profiles) can proceed in parallel with slice 22.

Full plan: [ADAPTATION_OUTPUT_DELIVERY_PLAN.md](../../product/planning/ADAPTATION_OUTPUT_DELIVERY_PLAN.md)
