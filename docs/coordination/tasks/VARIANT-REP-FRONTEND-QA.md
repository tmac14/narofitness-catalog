# VARIANT-REP-FRONTEND-QA

## Control

- Track: `VARIANT-REPRESENTATION`
- Status: `PAUSED`
- Resume gate: explicit user authorization and representative dataset
- Owner on resume: `Agent 1B - App-Wide Accessible UX/UI`
- Contract: `docs/coordination/contracts/VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md`

## Objective

Validate mixed-brand and variant-representation behavior in Products and
ProductDetail without changing the already completed backend contract.

## Required Dataset

- `CRO-SACO-GUSANO`
- `BOC-BARRAS-CROSSFIT`
- `BOC-BARRAS-CROSSFIT-NEXO`
- `DOBHT`

## Required Validation

- Mixed-brand master displays `Varias marcas`, never a false brand.
- Variant rows show Brand only when the contract requires it.
- Family grouping remains correct.
- No redundant Variant column for single-label cases.
- Variant-label cleanup removes weight/logo noise.
- Products and ProductDetail column order matches the contract.
- Narrow widths have no Variant/Reference overlap.

## Next Safe Action

Wait for explicit resume and dataset proof, then create a QA-mode task.
