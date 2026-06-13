# IMPORT-FDL-FULL-QUALITY — Full Catalog Import Plan

**Track ID:** IMPORT-FDL-FULL-QUALITY  
**Status:** **`PAUSED / DEFERRED`** — superseded by active `SOURCE-CATALOG-DUAL-PATH-1`  
**Date:** 2026-06-07  
**Owner coordination:** Agent 3  
**Implementation:** Agent 2  
**Audit:** Agent 5  

**Supersedes (temporarily):** page-by-page expansion as primary strategy. **65-page manual loop is last resort.**

**Registry:** [IMPORT_PARSER_BACKLOG.md](./IMPORT_PARSER_BACKLOG.md) · [CODEX_ORCHESTRATION_STATE.md](./CODEX_ORCHESTRATION_STATE.md)

---

## Objective

Achieve **complete and correct** import of the **FDL Tarifa 2026** catalog (65 PDF pages) via **full seed**, not incremental page fixes.

| Goal | Detail |
|------|--------|
| Unblock real product rows | Minimize unjustified `rows_blocked` |
| Reduce false singleton masters | High-confidence false singletons → **0** |
| Preserve correct families | No false mega-families; no over-grouping |
| Maintain regressions | Pages **11 / 12 / 13 / 14** remain **PASS** |
| Deterministic full seed | Repeatable counts and grouping |

---

## Current seed snapshot (baseline)

| Field | Value |
|-------|-------|
| `price_list_id` | `2eb77933-c07b-4421-bb1d-36322809c9ec` |
| `masters_created` | **358** |
| `variants_created` | **544** |
| `variants_updated` | **0** |
| `price_entries` | **544** |
| `rows_blocked` | **292** ← **too high** |
| `catalog_name` | FDL Tarifa 2026 |
| `catalog_id` | `a0e513fc-a0e9-46cf-ba8b-0215a0109210` |
| `catalog_items_created` | **544** |
| PDF pages | **65** |

### Observed problems

- Too many **rows_blocked** — likely systemic gates, not only headers.
- Too many **standalone masters** — possible false singletons / family fragmentation.
- Possible **family fragmentation** — variants split across masters incorrectly.
- Page-by-page (65 pages) must be **last option** after systemic pattern analysis.

---

## Agent strategy (waves)

### Wave 1 — Parallel diagnosis (NOW)

| Agent | Role | Deliverable |
|-------|------|-------------|
| **Agent 5** | Full-catalog **non-invasive** audit | Reports under `temp/audit/full_catalog/` |
| **Agent 2** | Backend/importer **root-cause** diagnostic | Blocked-row taxonomy; singleton/family fragmentation analysis |
| **Agent 3** | Coordination, backlog, acceptance criteria | This plan + checkpoint updates |

**Wave 1 rules:**

- Agent 5: **read-only** audit path — same production parser modules; no parser edits.
- Agent 2: diagnostic + classification; **no** page-specific SKU hardcodes in Wave 1.
- **Do not** start Page 15 or new page-by-page work during Wave 1.

### Wave 2 — Systemic fixes

| Agent | Role |
|-------|------|
| **Agent 2** | Implement **systemic batches** (grouping, gates, taxonomy, brand, family rules) |
| **Agent 5** | Re-audit **full catalog** + deep-dive **red pages** from Wave 1 |
| **Agent 1A** | **Idle** until backend stabilized — then Products UI visual smoke only |

### Wave 3 — Validation

| Step | Owner |
|------|-------|
| Full seed validation (deterministic counts) | Agent 2 + Agent 5 |
| Catalog builder visual smoke | Agent 1A |
| PDF/export smoke | Agent 6 — **only if** import complete |

---

## Acceptance criteria (objective)

| # | Criterion | Target |
|---|-----------|--------|
| AC-1 | All **real product rows** importable | 100% of identifiable product SKUs/variants in seed output |
| AC-2 | Remaining `rows_blocked` | Each **justified** as non-product / header / ambiguous — documented taxonomy |
| AC-3 | False singleton masters (high-confidence) | **0** |
| AC-4 | False mega-families | **0** |
| AC-5 | Unexpected category creation | **0** — only expected taxonomy |
| AC-6 | Regression pages | **11 / 12 / 13 / 14** — **PASS** |
| AC-7 | Full seed deterministic | Same command → same master/variant/block counts (±0) |
| AC-8 | Catalog lines parity | `catalog_items_created` == variants expected/imported |
| AC-9 | Products UI smoke | Pass with representative families (mixed-brand, multi-variant, simple) |
| AC-10 | Audit artifacts | Reports under `temp/audit/full_catalog/` |

---

## Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-1 | Over-grouping → **false families** | Wave 1 audit before batch fixes; regression pages 11–14 |
| R-2 | Lowering gates too much → junk rows import | Justified-block taxonomy; AC-2 sign-off |
| R-3 | **Page-specific / SKU hardcodes** | Forbidden as primary strategy; systemic rules only |
| R-4 | Breaking **approved pages** 11–14 | Mandatory regression PASS after each batch |
| R-5 | Mixing page-by-page DB with full seed | **Isolate DB** per workflow; document proof path |
| R-6 | **65 manual page loops** before systemic analysis | Page-by-page = **last resort**; full-catalog audit first |
| R-7 | Context switch from paused UI/PDF QA | Explicit **PAUSED** status — resume after IMPORT-FDL gate |

---

## Paused workstreams (deferred)

Not closed — **QA not signed off**:

| ID | Status |
|----|--------|
| PROD-DETAIL-UX-V2 QA (A/B/C/D/B2 UI) | **PAUSED / DEFERRED** |
| ProductMedia QA | **PAUSED / DEFERRED** |
| PriceEvolution QA | **PAUSED / DEFERRED** |
| VARIANT-REP frontend QA | **PAUSED / DEFERRED** |
| PDF / Preview visual QA | **PAUSED / DEFERRED** |
| PDF-TABLE-FIX-1 visual QA | **PAUSED / DEFERRED** |
| PR-PAGE15 | **PAUSED / DEFERRED** |
| PROD-DETAIL-V2-B2 integration tests | **PAUSED / DEFERRED** |
| Non-critical UI follow-up (SHARED-4 visual, PRES-1, etc.) | **PAUSED / DEFERRED** |

**Resume trigger:** IMPORT-FDL-FULL-QUALITY acceptance criteria **met** or user explicitly reprioritizes.

---

## Proof commands (reference)

```text
# Full seed proof path (isolate from page-by-page DB)
npm run db:reset:full:wipe
  → migrate
  → seed_pim
  → seed_catalog --fresh
  → fdl_pdf_v1 (full 65 pages)
  → run_preview_pipeline
  → confirm_import

# Full catalog audit (Agent 5)
npm run audit:full-catalog -- --format=both
# Output: temp/audit/full_catalog/
```

---

## Agent next steps

| Agent | Wave 1 action |
|-------|---------------|
| **Agent 5** | Run full-catalog non-invasive audit → `temp/audit/full_catalog/` |
| **Agent 2** | Blocked-row + singleton + fragmentation diagnostic report |
| **Agent 3** | Track metrics vs baseline; gate Wave 2 |
| **Agent 1A** | **Idle** (Wave 2 smoke only when stable) |
| **Agent 4** | **Idle** |
| **Agent 6** | **Idle** (Wave 3 PDF smoke) |
| **User** | Approve Wave 2 batches; confirm resume of paused tracks later |

---

## Related documents

- [IMPORT_PARSER_BACKLOG.md](./IMPORT_PARSER_BACKLOG.md)
- [CODEX_ORCHESTRATION_STATE.md](./CODEX_ORCHESTRATION_STATE.md)
- [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml)
- [PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md](./contracts/PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md)
- [PR-PAGE14-FDL_CONTRACT_SUMMARY.md](./contracts/PR-PAGE14-FDL_CONTRACT_SUMMARY.md)
