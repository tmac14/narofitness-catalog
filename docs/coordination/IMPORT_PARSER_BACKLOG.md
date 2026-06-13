# Import / Parser Backlog

Registry for FDL PDF import and parser workstreams (PR-* IDs). Separate from catalogue builder API dependencies ([API_DEPENDENCY_BACKLOG.md](./API_DEPENDENCY_BACKLOG.md)).

- **Agent 2** owns parser, grouping, taxonomy, brand resolution, seed paths.
- **Agent 5** runs scoped page import audits (`audit:page-import`) using **same production modules** as fresh seed — differs only in page-scoped import and reporting.
- **Agent 3** maintains this registry.

**Last updated:** 2026-06-11 (Codex — import work paused by explicit reprioritization)

**Top priority:** [SOURCE_CATALOG_DUAL_PATH_PLAN.md](./SOURCE_CATALOG_DUAL_PATH_PLAN.md)

**Status legend:** `ACTIVE` | `PAUSED` | `OPEN` | `CONFIRMED` | `BACKEND_VALIDATED` | `QA_VISUAL_READY` | `DONE`

---

## Summary table

| ID | Title | Owner | Status | Blocks fresh seed? |
|----|-------|-------|--------|-------------------|
| **IMPORT-FDL-FULL-QUALITY** | Full FDL 2026 catalog import | Agent 2 + 5 | **`PAUSED / DEFERRED`** | Yes — when resumed |
| PR-PAGE11 | Cross-training bumper discs (page 11) | Agent 2 | **DONE** (superseded by family block) | No |
| PR-REPUESTO | REPUESTO explicit one-per-SKU | Agent 2 | **DONE** | No |
| **PR-FDL-FAMILY-BLOCK** | Family header + variant_rows parser model | Agent 2 | **`BACKEND_VALIDATED` / `QA_VISUAL_READY`** | No |
| **COLOR-1** | Color normalization (1a–1d) | Agent 2 | **COMPLETE / CLOSED** | No |
| **VARIANT-REP-1B/1C** | Variant label cleanup | Agent 2 | **COMPLETE** | No |
| **PR-PAGE14** | FDL page 14 scoped audit | Agent 5 | **`APPROVE_WITH_NOTES`** | No — **QA dataset source** |
| **PR-PAGE15** | FDL page 15 scoped audit | Agent 5 | **PAUSED / DEFERRED** | No — superseded by full-quality track |
| TEST-FLAKE-MASTER-DETAIL | Lazy-load flake in master detail test | Agent 2 | **OPEN** | No |

---

## IMPORT-FDL-FULL-QUALITY — Full catalog (PAUSED)

**Plan:** [IMPORT_FDL_FULL_QUALITY_PLAN.md](./IMPORT_FDL_FULL_QUALITY_PLAN.md)

| Field | Value |
|-------|-------|
| **Status** | **`PAUSED / DEFERRED`** |
| **Wave** | Paused during `SOURCE-CATALOG-DUAL-PATH-1` |
| **Pages** | 65 — **full seed**, not page-by-page primary |
| **Regression guard** | Pages **11 / 12 / 13 / 14** must stay **PASS** |

### Baseline (current seed)

| Metric | Value |
|--------|-------|
| `price_list_id` | `2eb77933-c07b-4421-bb1d-36322809c9ec` |
| `masters_created` | 358 |
| `variants_created` | 544 |
| `rows_blocked` | **292** |
| `catalog_id` | `a0e513fc-a0e9-46cf-ba8b-0215a0109210` |
| `catalog_items_created` | 544 |

### Acceptance (summary)

All real product rows importable; justified blocks only; false singletons (high-confidence) = 0; no false mega-families; deterministic seed; `catalog_items_created` parity; audit reports in `temp/audit/full_catalog/`.

**Page-by-page (65 loops):** **last resort** after systemic fixes.

---

## PR-FDL-FAMILY-BLOCK — Family header + variant_rows

| Field | Value |
|-------|-------|
| **Status** | **`BACKEND_VALIDATED` / `QA_VISUAL_READY`** |
| **Validated** | 2026-06-08 |
| **Contract** | [PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md](./contracts/PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md) |
| **Builds on** | [PR-PAGE11-CROSSTRAINING-BUMPER](./contracts/PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md) |

### Fresh reset lifecycle

```text
npm run db:reset:full:wipe
  → wipe PostgreSQL volume
  → migrate (alembic upgrade head)
  → seed_pim
  → seed_catalog --fresh
  → real FDL PDF parser/importer (fdl_pdf_v1)
  → run_preview_pipeline
  → confirm_import
```

Agent 5 page audits use the **same production modules**; they differ only in **scoped page import** and **reporting**.

### Validation (post-wipe)

| Check | Result |
|-------|--------|
| Page 11 variants | **30 / 30** |
| Master keys | DOB, DOB3C, DOBC, DOBN, DOBNEXON, DOBNEXOC |
| Category | discos |
| Brands | nexo, sin-marca — **never fdl** |
| Master names | Not derived from variant names like `"25 kgs"` |
| Full import | 530 variants, 420 masters |
| Agent 5 audits | **PASS** — pages 11, 3, 4, 5 |
| `test:api:full` | 286 passed, 1 skipped, **1 failed** (pre-existing flake — see below) |

### Agent roles

| Agent | Status |
|-------|--------|
| **Agent 2** | **Complete** — no further backend action unless visual QA finds import bugs |
| **Agent 5** | **Complete** — audit path validated |
| **Agent 1B** | Optional — import review UI visual check for new payload fields |
| **Agent 4** | Not involved |

### Proof commands

```powershell
npm run db:reset:full:wipe
npm run test:api:full
npm run audit:page-import -- --page=11 --ensure-pim-seed --format=both
npm run audit:page-import -- --page=3 --ensure-pim-seed --format=both
npm run audit:page-import -- --page=4 --ensure-pim-seed --format=both
npm run audit:page-import -- --page=5 --ensure-pim-seed --format=both
```

---

## COLOR-1 — Color normalization

| Field | Value |
|-------|-------|
| **Status** | **COMPLETE / CLOSED** |
| **Owner** | Agent 2 |
| **Phases** | 1a, 1b, 1c, 1d |

**Delivered:** `unknown_color_value` non-blocking for price; expanded allowed values; hyphen extraction; synonyms; raw metadata; UI `Color no reconocido: {valor}`.

**Audits:** Pages **11 / 12 / 13** — **PASS**.

**Post–page-14:** NEGRA / negra / negros / negras → Negro.

**Open (non-blocking):** P14-n1 — `NEGRA - LOGO` on NEXO SKUs — see [PR-PAGE14](./contracts/PR-PAGE14-FDL_CONTRACT_SUMMARY.md).

---

## PR-PAGE14 — FDL page 14 audit

| Field | Value |
|-------|-------|
| **Status** | **`APPROVE_WITH_NOTES`** |
| **Owner** | Agent 5 (audit) |
| **Contract** | [PR-PAGE14-FDL_CONTRACT_SUMMARY.md](./contracts/PR-PAGE14-FDL_CONTRACT_SUMMARY.md) |

| Metric | Value |
|--------|-------|
| Imported | 22/22 |
| Blocked | 0 |
| Masters | SOP028, SOP029, CRO-SACO-GUSANO, CRO133, BOC-BARRAS-CROSSFIT, BOC-BARRAS-CROSSFIT-NEXO |

**Notes (non-blocking):** P14-n1 NEXO color null; P14-n2 mixed NEXO master; P14-c1 cross-training taxonomy; P14-c2 Saco Gusano specs in name only.

**Unblocks:** PR-PAGE15.

**QA dataset:** Masters listed above required for VARIANT-REP + ProductDetail v2 manual QA.

---

## VARIANT-REPRESENTATION-1B/1C — Label cleanup

| Field | Value |
|-------|-------|
| **Status** | **COMPLETE** |
| **Owner** | Agent 2 |

DOBHT redundant Variante removed; PESO covers weight tokens; LOGO/NEXO noise stripped from labels when brand covered. Audits 11/12/13/14 **PASS**. No frontend/PDF/schema.

---

## PR-PAGE15 — FDL page 15 audit

| Field | Value |
|-------|-------|
| **Status** | **PAUSED / DEFERRED** |
| **Owner** | Agent 5 |
| **Reason** | Superseded by **IMPORT-FDL-FULL-QUALITY** — resume only if full-quality track fails and user reprioritizes page-by-page |

**Workflow (when approved):** isolated import → DB page 15 only → audit markdown/json → API/UI visual → no code changes in audit phase → no advance without approval.

---

## TEST-FLAKE-MASTER-DETAIL {#test-flake-master-detail}

| Field | Value |
|-------|-------|
| **ID** | TEST-FLAKE-MASTER-DETAIL |
| **Status** | **OPEN** |
| **Owner** | Agent 2 |
| **Priority** | P3 — non-blocking |
| **Test** | `test_get_master_with_variants_returns_detail` |
| **Symptom** | Intermittent SQLAlchemy lazy-load flake |
| **Relation to PR-FDL-FAMILY-BLOCK** | **Unrelated** — documented pre-existing; does not affect import/parser validation |
| **Blocks** | Nothing — PR-FDL-FAMILY-BLOCK remains `BACKEND_VALIDATED` |

**Action:** Triage and fix in a **separate task** (eager load, session scope, or test isolation).

---

## Related documents

- [PR-PAGE14-FDL_CONTRACT_SUMMARY.md](./contracts/PR-PAGE14-FDL_CONTRACT_SUMMARY.md)
- [PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md](./contracts/PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md)
- [IMPORT_FDL_FULL_QUALITY_PLAN.md](./IMPORT_FDL_FULL_QUALITY_PLAN.md)
- [VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md](./contracts/VARIANT_REPRESENTATION_CONTRACT_SUMMARY.md)
- [TRANSVERSAL_BACKLOG.md](./TRANSVERSAL_BACKLOG.md)
- [CODEX_ORCHESTRATION_STATE.md](./CODEX_ORCHESTRATION_STATE.md)
- [PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md](./contracts/PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md)
- [PR-REPUESTO_CONTRACT_SUMMARY.md](./contracts/PR-REPUESTO_CONTRACT_SUMMARY.md)
- [PR-K-family-regex-design.md](./PR-K-family-regex-design.md)
- [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml)
- [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)
