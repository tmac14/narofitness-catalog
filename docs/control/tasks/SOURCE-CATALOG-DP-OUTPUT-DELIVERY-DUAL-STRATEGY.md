# SOURCE-CATALOG-DP-OUTPUT-DELIVERY-DUAL-STRATEGY

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-docs + agent-backend + agent-frontend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: **VALIDATED** (2026-06-15)

## Objective

Record product decision: dual output profiles + persist/ephemeral delivery, integrated across parity and Phase 3 tracks.

## Decision

**SC-DP-SLICE-31..37** — see [ADAPTATION_OUTPUT_DELIVERY_PLAN.md](../../product/planning/ADAPTATION_OUTPUT_DELIVERY_PLAN.md)

User requirements (2026-06-14):

- Maintain **both** PDF strategies: `email_optimized` (≤15 MB) and `archive_quality`.
- UI must let user choose profile before generation.
- UI must let user choose **persist** vs **ephemeral download-only**.
- Final export and approval require persist; ephemeral is preview-only.

## Evidence

- EVID-SC-DP-OUTPUT-DELIVERY-001 (plan doc + decision log)
