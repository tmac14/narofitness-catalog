# PDF-EXPORT-PREVIEW-MANUAL-QA

## Control

- Track: `PDF-EXPORT`
- Status: `PAUSED`
- Resume gate: explicit user authorization
- Owner on resume: `Agent 6 - PDF Export and Print Renderer`
- Supporting UI QA: `Agent 1A - Catalogue Builder UI/UX`
- Contract: `docs/control/contracts/PDF_EXPORT_CONTRACT_SUMMARY.md`

## Objective

Complete pending PDF export and PDF-table manual sign-off while preserving the
already validated paginated preview (`PREV-3`).

## Current Proven State

- PDF layout visually accepted.
- Export pipeline integrated.
- PREV-3 preview implemented and QA PASS.
- Automated export/layout tests previously green.
- Manual PDF-1 and PDF-table sign-off remains pending.

## Required Validation

- Real `%PDF` download without preview reload.
- Selected content, category/brand grouping, EAN, SKU, P.V.P., images, and
  placeholders.
- Simple-product and variant-family layouts.
- Preview/export parity and page-break behavior.
- Legacy layout rendering only until PR-08 removes approved obsolete behavior.
- Windows system-viewer smoke and active engine health.
- Export blocked clearly while order or preview is pending.

## Escalation

- Renderer/layout/parity defect: Agent 6.
- Export-modal-only UX: Agent 1A.
- Missing API/context data: Agent 2A or Agent 6 after contract diagnosis.
- Import-data defect: Agent 2B, not Agent 6.

## Next Safe Action

Wait for explicit resume, then create a QA task with current catalogs and
canonical commands.
