# SOURCE-CATALOG-DP-PHASE2A-ADAPTATION-PROJECT

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Evidence

- EVID-SC-DP-PHASE2A-001

## Next Safe Action

None — task **VALIDATED**. Next: discover Phase 2B (preview job / renderer integration).

## Objective

Introduce `CatalogAdaptationProject` + immutable `CatalogAdaptationRecipeVersion` and API to create/detail from stored `SourceDocument`.

## Scope

- Allowed: migration 012, models, services, routers, schemas, tests, job_constants subject type.
- Forbidden: adaptation renderer, preview/export jobs, UI, PIM writes.
