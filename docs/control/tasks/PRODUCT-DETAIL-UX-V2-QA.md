# PRODUCT-DETAIL-UX-V2-QA

## Control

- Track: `PRODUCT-DETAIL`
- Status: `PAUSED`
- Resume gate: explicit user authorization plus fresh dataset validation
- Owner on resume: `Agent 1B - App-Wide Accessible UX/UI`
- Contract: `docs/control/contracts/PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md`

## Objective

Complete final ProductDetail v2 QA for variants, local/external media, price
evolution, and supporting backend integration without reimplementing the
already approved base ProductDetail experience.

## Resume Preconditions

- Confirm representative products exist, including mixed-brand and
  multi-variant families.
- Revalidate current ProductDetail implementation against the contract.
- Register exact frontend/backend test and QA scopes before launch.
- Do not resume PDF/export QA through this packet.

## Required Validation

- Variants panel hierarchy, overflow, and expanded detail behavior.
- Local-media picker, keyboard, drag/drop, loading, primary, and delete flows.
- External HTTPS media ingest, validation, origin link, and surfaced errors.
- Price evolution for 0, 1, and 2+ milestones, error state, and per-variant
  caching.
- Product summary no-price, single-price, and min/max range behavior.
- Backend B2 integration: migrations, PostgreSQL, and integration suite.
- Desktop/tablet/mobile accessibility and visual QA.

## Blocked Scope

- Base ProductDetail redesign already closed.
- PDF/preview/export validation.
- Backend contract invention.
- Any paused-track activation without explicit user approval.

## Next Safe Action

Wait for explicit resume; then perform fresh discovery and create an approved
QA task.
