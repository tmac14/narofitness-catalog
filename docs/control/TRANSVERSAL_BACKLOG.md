# Transversal Backlog

Cross-cutting workstreams outside catalogue API-X (API-1…API-8) and page-scoped PR-* import audits.

**Last updated:** 2026-06-11 (Codex - dual-path Phase 0 complete)

**Top priority:** [SOURCE_CATALOG_DUAL_PATH_PLAN.md](./SOURCE_CATALOG_DUAL_PATH_PLAN.md)

**Snapshot:** [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md)

---

## Summary table

| ID | Title | Owner | Status |
|----|-------|-------|--------|
| **PROD-DETAIL-UX-1** | Product detail base | Agent 1B | **APPROVED / CLOSED** |
| **PROD-DETAIL-UX-V2** | Product detail v2 (A/B/C/D/B2) | Agent 1B + 4 + 2 | **IMPLEMENTED / QA_PENDING** (parts COMPLETE) |
| **DASHBOARD-UX-1B** | Dashboard redesign | Agent 1B | **APPROVED / CLOSED** |
| **SCROLL-LAYOUT-1** | Single scroll owner | Agent 1B | **APPROVED_WITH_NOTES / CLOSED** |
| **VARIANT-REPRESENTATION-1** | Mixed-brand families | Agent 2 + 1B + 6 | Backend **COMPLETE**; frontend QA **PAUSED / DEFERRED** |
| **VARIANT-REPRESENTATION-1B/1C** | Label cleanup | Agent 2 | **COMPLETE** |
| **COLOR-1** | Color normalization | Agent 2 | **COMPLETE / CLOSED** |
| **PDF-TABLE-FIX-1** | Supplier table PDF fixes | Agent 6 | **PAUSED / DEFERRED** |
| **DASHBOARD-API-2** | Dashboard real data | Agent 2 + 4 | **NOT_STARTED** |
| **MEDIA-ENHANCE-1** | Cloud product-image enhancement pipeline | Agent 2 + 6 | **FUTURE / DEFERRED** |
| **SOURCE-CATALOG-DUAL-PATH-1** | Direct catalogue adaptation + structured PIM import | Agent 2 + 6 + 1B + 4 | **ACTIVE / PHASE 0 COMPLETE / PHASE 1A GATE** |

---

## PROD-DETAIL-UX-V2 — Product detail v2

**Contract:** [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./contracts/PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md)

| Phase | Status | Tests |
|-------|--------|-------|
| A — Variants panel | **IMPLEMENTED / QA_PENDING** | 227 |
| B — Local media | **IMPLEMENTED / QA_PENDING** | 239 |
| C0 — Price history types | **COMPLETE** (Agent 4) | 248 |
| C/D — Price evolution UI | **IMPLEMENTED / QA_PENDING** | 259 |
| B2 backend | **IMPLEMENTED / INTEGRATION_TESTS_PENDING** | 19 unit |
| B2 api.ts | **COMPLETE** (Agent 4) | 264 |
| B2 UI | **IMPLEMENTED / QA_PENDING** | **268** |

**Base PROD-DETAIL-UX-1 remains APPROVED / CLOSED** — v2 is additive block pending final QA.

---

## VARIANT-REPRESENTATION-1

**Contract:** [VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md](./contracts/VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md)

| Layer | Status |
|-------|--------|
| Backend | **COMPLETE** |
| 1B/1C cleanup | **COMPLETE** |
| Frontend | **IMPLEMENTED / QA_PENDING** |
| PDF | Integrated — visual QA pending |

---

## SCROLL-LAYOUT-1 — CLOSED

| Field | Value |
|-------|-------|
| **Status** | **APPROVED_WITH_NOTES / CLOSED** |
| **QA** | **PASS_WITH_NOTES** — no blockers/majors |

**Minor notes (non-blocking):**

| ID | Note |
|----|------|
| B1 | Residual minor scroll — Catálogo General |
| B2 | Regional scroll on some wide tables |
| B3 | Cosmetic header+toolbar in preview |

**SCROLL-LAYOUT-1C:** Do not open unless user reports real annoyance.

---

## PROD-DETAIL-UX-1 / DASHBOARD-UX-1B

Remain **APPROVED / CLOSED** — see prior entries. ProductDetail UX v2 builds on closed base.

---

## PDF-TABLE-FIX-1 — PAUSED

Agent 6 — **PAUSED / DEFERRED**. PDF/Preview visual QA resumes Wave 3 after import complete.

---

## DASHBOARD-API-2 — NOT_STARTED

Future real data feed after closed Dashboard shell.

---

## MEDIA-ENHANCE-1 - FUTURE / DEFERRED

Future cloud pipeline for improving low-resolution product images extracted from
supplier catalogues without requiring a permanently provisioned GPU.

**Decision:** prefer deterministic super-resolution with an ephemeral/serverless
GPU worker. Generative GPT image editing is an optional premium/experimental
path only because it can alter product geometry, logos, colours, or accessories
and has a materially higher per-catalogue cost.

**Proposed flow:**

1. Python extracts source images and records provenance.
2. Images are deduplicated by content hash.
3. A queued serverless GPU job runs Real-ESRGAN or an equivalent deterministic model.
4. Original and enhanced derivatives are stored separately in object storage.
5. Enhanced assets require visual approval before becoming the preferred product media.
6. Existing derivatives are reused by hash across imports and catalogue regenerations.

**Activation conditions:**

- `IMPORT-FDL-FULL-QUALITY` is complete or the user explicitly reprioritizes this feature.
- Product-media provenance and derivative storage contracts are defined.
- Background jobs/process registry is available or a limited worker contract is approved.
- A representative benchmark proves acceptable fidelity, runtime, and cost.

**Expected infrastructure envelope:** approximately USD 25-50/month for an
initial robust cloud deployment shared with the application, with image
enhancement compute typically USD 0-3/month at low volume when using serverless
GPU and caching. Revalidate provider pricing before implementation.

**Detailed scope:** [MEDIA_ENHANCEMENT_FUTURE_FEATURE.md](./contracts/MEDIA_ENHANCEMENT_FUTURE_FEATURE.md)

---

## SOURCE-CATALOG-DUAL-PATH-1 - ACTIVE / PHASE 0 COMPLETE

Introduce a shared immutable supplier-PDF intake with two deliberately isolated
workflows:

- Directly adapt and brand the source catalogue into a derived PDF without
  creating PIM products.
- Import the original source into normalized PIM entities and build a DB-backed
  catalogue through the existing catalog builder.

The paths share source storage, semantic analysis, provenance, jobs, and artifact
infrastructure, but keep recipes, approvals, PIM state, pricing side effects, and
exports separate.

**Critical decisions:** `Catalog` remains PIM-backed only; adapted PDFs are never
automatic import sources; unknown layouts require an explicit supported profile;
no productive page/SKU hardcodes.

**Detailed plan:** [SOURCE_CATALOG_DUAL_PATH_PLAN.md](./SOURCE_CATALOG_DUAL_PATH_PLAN.md)

**Phase 0 decisions:** [SOURCE_CATALOG_PHASE0_DECISIONS.md](./SOURCE_CATALOG_PHASE0_DECISIONS.md)

**Next gated batch:** [SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md](./SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md)

---

## Related documents

- [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md)
- [TASK_HISTORY.md](./TASK_HISTORY.md)
- [IMPORT_PARSER_BACKLOG.md](./IMPORT_PARSER_BACKLOG.md)
- [MEDIA_ENHANCEMENT_FUTURE_FEATURE.md](./contracts/MEDIA_ENHANCEMENT_FUTURE_FEATURE.md)
- [SOURCE_CATALOG_DUAL_PATH_PLAN.md](./SOURCE_CATALOG_DUAL_PATH_PLAN.md)
- [SOURCE_CATALOG_PHASE0_DECISIONS.md](./SOURCE_CATALOG_PHASE0_DECISIONS.md)
- [SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md](./SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md)
