# SOURCE-CATALOG-DP-PHASE1D-IMPORT-LINK

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Status: VALIDATED

## Evidence

- EVID-SC-DP-PHASE1D-001

## Next Safe Action

None — task **VALIDATED**. Phase 1 exit gate complete: upload → analyze → import preview from stored source. Next: discover Phase 1 formal closure or Phase 2 adaptation MVP.
- Validator: python -m ordia.cli validate --project

## Objective

Link `ImportBatch` to `SourceDocument` (+ optional snapshot) and expose import preview from stored source.

## Scope

- Allowed: migration 011, import_staging/pipeline, source_documents route, schemas, tests.
- Forbidden: importer parser changes, confirm flow changes, adaptation UI.
