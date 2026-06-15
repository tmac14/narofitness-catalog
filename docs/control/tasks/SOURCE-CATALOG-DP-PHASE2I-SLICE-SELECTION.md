# SOURCE-CATALOG-DP-PHASE2I-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED

## Objective

Select Phase 2I slice: baseline exit-gate audit in preview manifest (table recompose deferred).

## Decision

**SC-DP-SLICE-14** — `baseline_audit` + `table_recompose: pending` in manifest; MVP gates vs full Phase 2 exit gate separated.

## Rationale

- Honest gate before claiming 65-page FDL reproduction.
- `mvp_gates_pass` documents achievable preview scope.
- `direct.table_recompose` remains Phase 2J+.
