# PR-FDL-FAMILY-BLOCK Contract Summary

**Agent:** 2  
**Dependency ID:** PR-FDL-FAMILY-BLOCK (family_header + variant_rows parser model)  
**Date:** 2026-06-08  
**Status recommendation:** **`BACKEND_VALIDATED` / `QA_VISUAL_READY`**  
**Validated:** 2026-06-08 (Agent 2 + Agent 5 fresh-reset proof)  
**Builds on:** [PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md](./PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md)

**Registry:** [IMPORT_PARSER_BACKLOG.md](../IMPORT_PARSER_BACKLOG.md)

---

## 1. Problem

The FDL PDF parser treated page 11 (and similar layouts) as a flat product list: grey **family header** rows were concatenated into `raw_name` with variant weight lines. Grouping then derived `master_name` from variant text (e.g. `"25 kgs"`) instead of the family header. Commercial brand defaulted to supplier **FDL** when no section brand was present.

## 2. Files changed

| File | Change |
|------|--------|
| `apps/api/app/services/import_parsers/fdl_pdf_v1.py` | Layout extraction (union span bbox); family_header state machine; variant/family split; commercial brand resolution |
| `apps/api/app/services/import_parsers/base.py` | `family_header_raw`, `family_block_id`, `variant_name_raw`, `taxonomy_name`, brand metadata fields |
| `apps/api/app/services/import_brand_resolution.py` | **New** — priority chain section → family header → variant → `Sin marca` |
| `apps/api/app/services/import_master_naming.py` | **New** — `build_master_name_from_family_header()` |
| `apps/api/app/services/seed_brands.py` | `Sin marca` / `sin-marca` seed; preserve display casing |
| `apps/api/app/services/seed_pim.py` | Calls `ensure_fallback_commercial_brand()` |
| `apps/api/app/services/import_grouping.py` | `master_name` from family header; `family_block_id` guard; peso from variant name |
| `apps/api/app/services/seed_taxonomy_mapping_rules.py` | `section_keyword` rules for CROSSTRAINING + disco/bumper |
| `apps/api/app/services/taxonomy_mapper.py` | `_row_name()` uses `taxonomy_name` / family header concat |
| `apps/api/app/services/import_staging.py` | Family/brand fields in `parsed_payload` JSONB |
| `apps/api/app/services/import_audit/page_extraction.py` | `line_kind: family_header` in raw extraction audit |
| Tests + fixtures | See section 8 |

**Not changed:** frontend, `import_review.py` gates, DB migrations.

## 3. Migrations

None. Family block context is stored in existing `parsed_payload` JSONB on import rows.

## 4. Parser changes

### Layout extraction

- `_extract_lines_with_layout()` returns `ParsedLine` with union bbox across all spans (not first span only).
- Font size bands: section ≥ 20.0, family header 8.0–8.5, variants ≤ 7.5.

### Family header detection

`_is_family_header_line()` requires:

- Font size in `[8.0, 8.5]`
- No SKU / EAN / price pattern
- Not a section or subheader line
- Minimum 15 characters
- Bbox width ratio ≥ 0.25 (family headers ~0.28–0.39 on page 11; variants ~0.13–0.18)

### State machine

- On family header: set `active_family` (`FamilyBlockContext` with stable `family_block_id`)
- Variant buffer excludes header text; `variant_name_raw` = product lines before SKU only
- `raw_name` / `taxonomy_name` = header + variant for taxonomy keyword matching
- `row.name` = variant-specific display name

## 5. Brand resolution

New module `import_brand_resolution.py`:

| Priority | Source | Confidence |
|----------|--------|------------|
| 1 | Section header brand | 1.0 |
| 2 | `family_header_raw` token scan | 0.95 |
| 3 | `variant_name_raw` consensus | 0.8 |
| 4 | Fallback **`Sin marca`** | 0.0 |

- **Supplier** remains `FDL` (unchanged entity).
- **Commercial brand** never defaults to FDL; `DEFAULT_BRAND` in parser aliases `FALLBACK_COMMERCIAL_BRAND`.
- Seed: idempotent `Brand` with `name="Sin marca"`, `slug="sin-marca"`.

## 6. Taxonomy changes

Layered rules (priority ascending):

| Prio | Type | Match | Target |
|------|------|-------|--------|
| 15–19 | sku_prefix | DOBNEXO / DOB3C / DOBC / DOBN / DOB | discos |
| 24 | section_keyword | `CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL\|bumper` | discos |
| 25 | section_keyword | `CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL\|disco` | discos |
| 30 | section_path | CROSSTRAINING (full path) | cross-training |

`_row_name()` in taxonomy mapper concatenates `family_header_raw` + variant name so keyword rules match product evidence in headers.

## 7. Grouping changes

- **`master_name`:** from `family_header_raw` via `build_master_name_from_family_header()` when present; never from variant weight line alone.
- **`family_block_id`:** variants group only within the same active family block (prevents mixing distinct grey headers sharing a SKU prefix).
- **`peso_kg`:** extracted from `variant_name_raw`, not SKU suffix digits.
- Existing tiers preserved: `cross_training_bumper_family`, `fdl_sku_family`, numeric suffix families, REPUESTO explicit one-per-SKU.

## 8. Tests

| Test file | Coverage |
|-----------|----------|
| `test_import_parser_family_blocks.py` | Heuristic detection; PDF integration (DOBNEXO05N, DOBN005) |
| `test_import_brand_resolution.py` | NEXO from header; Sin marca fallback; FDL never commercial; seed idempotency |
| `test_import_parser_brands.py` | No FDL commercial brand; embedded NEXO |
| `test_import_grouping_cross_training_bumper.py` | Master name from header; DOB3C≠DOBC; peso axis |
| `test_taxonomy_page11_mapping.py` | sku_prefix + section_keyword + CROSSTRAINING guard |
| `test_import_audit_page_import.py` | Page 11 fresh (30/30, 6 masters); pages 3/4/5 regression |
| `test_seed_catalog.py::test_full_seed_includes_page11_bumper_families` | Full `seed_pim` + `run_seed(fresh=True)` production path; page-11 DB invariants |

Fixtures: `page11_bumper_rows.json`, `dobnexo_family.json`.

## 9. Agent 5 audit results

Post-implementation after **`npm run db:reset:full:wipe`**:

### Full-catalog spot check (production seed path)

After wipe + PIM seed + `seed_catalog --fresh`:

| Check | Result |
|-------|--------|
| Page-11 variants in DB | **30 / 30** |
| Page-11 master keys | **DOB, DOB3C, DOBC, DOBN, DOBNEXON, DOBNEXOC** (6 families) |
| Category | **discos** (all page-11 variants) |
| Commercial brands | **nexo**, **sin-marca** — never **fdl** |
| Master names | No `"25 kgs"` in master titles |
| `Sin marca` brand seeded | **Yes** (`slug=sin-marca`) |

Full import stats: 530 variants created, 420 masters, 527 price entries (306 rows blocked by review gates — unchanged guardrails).

### Page sandbox audits (`audit:page-import`)

| Page | Status | Parsed | Imported | Blocked |
|------|--------|--------|----------|---------|
| 11 | **pass** | 30 | 30 | 0 |
| 3 | **pass** | 8 | 8 | 0 |
| 4 | **pass** | 9 | 9 | 0 |
| 5 | **pass** | 8 | 8 | 0 |

Page 11 criteria met: 30 variants, 6 masters, `master_name` without variant weight, commercial brand NEXO or Sin marca (never FDL), category discos with keyword/SKU evidence.

Raw extraction audit exposes `line_kind: family_header` for grey header rows (6 on page 11).

## 10. Guardrails preserved

- No `page_number == 11` (or any page) in production import rules
- `false_family_pattern` (BOCNEXO, CRONEXO) unchanged
- DOP / MU / MP / MPS numeric families unchanged
- REPUESTO-* → explicit one-per-SKU (page 3 pass)
- Cardio substring false positives → cross-training, not cardio subcategories
- `import_review.py` blocking gates not relaxed

## 11. Limitations (deferred)

- **Product images:** associating right-column images to family blocks deferred; `family_block_id` reserved for future linking.
- **Background grey detection:** not reliable in v1; font size + width ratio used instead.
- **Profile thresholds:** `FAMILY_HEADER_*` constants in parser; future merge into import profile config optional.

## 12. Rollback

1. Revert parser version / family block state machine in `fdl_pdf_v1.py`.
2. Re-seed taxonomy: `npm run db:seed:pim` (rules idempotent).
3. Optional profile flag `family_block_detection: false` (future) to restore flat parsing without code revert.

## 13. Frontend impact

None. Changes are backend parser, staging payload, grouping, taxonomy, and brand seed only.

## 14. Reseed required

```powershell
npm run db:seed:pim
```

Applies `Sin marca` brand, new `section_keyword` taxonomy rules, and existing bumper grouping profile defaults.

## 15. Agent 3 handoff

**Coordination status (2026-06-08):** `BACKEND_VALIDATED` / `QA_VISUAL_READY` — see [IMPORT_PARSER_BACKLOG.md](../IMPORT_PARSER_BACKLOG.md).

- **Review UI:** `parsed_payload` now includes `family_header_raw`, `variant_name_raw`, `family_block_id`, `brand_source`, `brand_confidence` — available for display in import review without schema migration.
- **Master names in app:** grouped bumper products show header-derived names (no `"25 kgs"` master titles).
- **Brand column:** expect NEXO, XEBEX, etc. or **Sin marca**; FDL appears only as supplier, not commercial brand.
- **Validation:** re-run page audits after any parser threshold tuning; page 11 is the canonical family-block fixture.

### Validation commands

```powershell
npm run test:api:full
docker compose exec -e PYTHONPATH=/app api python scripts/audit_page_import.py --page 11 --ensure-pim-seed --format both
docker compose exec -e PYTHONPATH=/app api python scripts/audit_page_import.py --page 3 --ensure-pim-seed --format both
docker compose exec -e PYTHONPATH=/app api python scripts/audit_page_import.py --page 4 --ensure-pim-seed --format both
docker compose exec -e PYTHONPATH=/app api python scripts/audit_page_import.py --page 5 --ensure-pim-seed --format both
```

---

## 16. Fresh reset/import lifecycle (documented)

Primary fresh command: **`npm run db:reset:full:wipe`**

Canonical sequence ([`scripts/db-reset-full.ps1`](../../../scripts/db-reset-full.ps1)):

1. **Wipe PostgreSQL volume**
2. **`alembic upgrade head`** (migrate)
3. **`npm run db:seed:pim`** → [`seed_pim.py`](../../../apps/api/app/services/seed_pim.py): categories, brands, **`Sin marca`**, specs, profiles, taxonomy mapping rules
4. **`npm run db:seed:fresh`** → [`seed_catalog.py --fresh`](../../../apps/api/app/services/seed_catalog.py):
   - `reset_catalog_data`
   - **`run_preview_pipeline`** — real FDL PDF → **`fdl_pdf_v1`** parser/importer path
   - **`confirm_import`** (full PDF)
   - presentation catalog

There is **no static product catalogue**. FDL import is live PDF → production parser → taxonomy → grouping → review → confirm.

### Agent 5 vs fresh seed

| Step | Fresh seed | Agent 5 audit |
|------|------------|---------------|
| Parser | `get_parser` → `parse_pdf` | Same `parse_pdf` |
| Taxonomy / grouping / review | `run_preview_pipeline` | Same modules, manual planning |
| Confirm | All PDF rows | Page-filtered rows only |
| PIM seed | Full `seed_pim` | `--ensure-pim-seed` re-runs mapping rules only |

Family-block fixes live in **shared production modules** (`fdl_pdf_v1`, `import_grouping`, `import_brand_resolution`, seed files)—not audit-only scripts.

### Fresh reset validation commands

```powershell
npm run db:reset:full:wipe
npm run test:api:full
npm run audit:page-import -- --page=11 --ensure-pim-seed --format=both
npm run audit:page-import -- --page=3 --ensure-pim-seed --format=both
npm run audit:page-import -- --page=4 --ensure-pim-seed --format=both
npm run audit:page-import -- --page=5 --ensure-pim-seed --format=both
npm run audit:report -- page-import
```

---

## 17. Fresh Reset Persistence Checklist

| # | Question | Answer |
|---|----------|--------|
| 1 | Affects production fresh seed/import path? | **Yes** — parser, pipeline, confirm |
| 2 | Which fresh command executes it? | `db:reset:full:wipe` → `seed_pim` + `seed_catalog --fresh` |
| 3 | Production code vs audit-only? | **Production code** (`fdl_pdf_v1`, grouping, brand, taxonomy seeds) |
| 4 | Seed data update required? | **Yes** — taxonomy rules + `Sin marca` in `seed_pim` |
| 5 | Taxonomy mapping seed update? | **Yes** — `section_keyword` rules in `seed_taxonomy_mapping_rules.py` |
| 6 | Grouping config seed update? | **Yes** — `cross_training_bumper_family` in `seed_catalog.ensure_fdl_profile_grouping_config` |
| 7 | Brand seed/fallback update? | **Yes** — `ensure_fallback_commercial_brand` in `seed_pim` and `run_seed` |
| 8 | Migration required? | **No** — `parsed_payload` JSONB only |
| 9 | Correct after `db:reset:full:wipe`? | **Verified** — full wipe + page-11 spot checks + audits 11/3/4/5 |
| 10 | Proof test/audit? | `test:api:full`, `test_seed_catalog` page-11 assertions, page audits 11/3/4/5 |

---

## 18. Backend validation closure (2026-06-08)

**Status:** **`BACKEND_VALIDATED` / `QA_VISUAL_READY`**

### Validation summary (post `db:reset:full:wipe`)

| Check | Result |
|-------|--------|
| Page 11 import | **30 / 30** variants |
| Page 11 master keys | **DOB, DOB3C, DOBC, DOBN, DOBNEXON, DOBNEXOC** |
| Category | **discos** |
| Commercial brands | **nexo**, **sin-marca** — never **fdl** |
| Master names | No variant-weight titles (e.g. no `"25 kgs"` masters) |
| Full import | **530** variants, **420** masters |
| Agent 5 audits | **PASS** — pages **11, 3, 4, 5** |

### Test suite (`npm run test:api:full`)

| Result | Count |
|--------|-------|
| Passed | **286** |
| Skipped | **1** |
| Failed | **1** |

**Failed test (pre-existing, unrelated to import fixes):**

- `test_get_master_with_variants_returns_detail` — SQLAlchemy lazy-load flake
- **Follow-up:** separate task [TEST-FLAKE-MASTER-DETAIL](../IMPORT_PARSER_BACKLOG.md#test-flake-master-detail) — triage/fix; does not block `BACKEND_VALIDATED`

### Coordination decisions

| Agent | Action |
|-------|--------|
| **Agent 2** | **Complete** for PR-FDL-FAMILY-BLOCK — no further backend work unless visual QA finds import bugs |
| **Agent 5** | Audits complete — production modules only; scoped page import/reporting |
| **User / App UX agent** | Optional visual QA on import review UI (`family_header_raw`, brand fields in `parsed_payload`) |
| **Agent 4** | Not involved — no frontend contract |

### QA visual ready (optional)

- Import review may surface new `parsed_payload` fields (`family_header_raw`, `variant_name_raw`, `brand_source`, etc.)
- Master names and brand column in desktop app should reflect header-derived names and commercial brands (NEXO / Sin marca, not FDL)
