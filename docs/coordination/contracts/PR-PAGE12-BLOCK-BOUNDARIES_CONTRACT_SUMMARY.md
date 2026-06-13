# PR-PAGE12-BLOCK-BOUNDARIES Contract Summary

**Agent:** 2  
**Dependency ID:** PR-PAGE12-BLOCK-BOUNDARIES (block title detection + family reset)  
**Date:** 2026-06-08  
**Status:** `BACKEND_VALIDATED`  
**Builds on:** [PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md](./PR-FDL-FAMILY-BLOCK_CONTRACT_SUMMARY.md), [PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md](./PR-PAGE11-CROSSTRAINING-BUMPER_CONTRACT_SUMMARY.md)

---

## 1. Problem

PDF page 12 (CROSSTRAINING mixed blocks) parsed 39 rows but only 38 imported; all 38 masters were `explicit_one_per_sku`. Root causes:

| Cause | Symptom |
|-------|---------|
| Width gate | Shorter block titles at font 8.28 failed `_is_family_header_line` width ≥ 0.25 |
| Stale `active_family` | Competicion header leaked into DOBF, CRO, SOP025, DOBMINI `raw_name` / `taxonomy_name` |
| Grouping | DOBHT/DOBCC/DOBF prefixes missing from bumper tier |
| CRO grouping | All `CRO*` merged as 1:1; slam/wall blocks not separated |
| DOBMINI | Alpha-only SKU failed `explicit_numeric_sku_regex` → `one_per_sku_fallback` |
| Taxonomy | Contaminated CRO names matched disco/bumper keywords → `discos` |

## 2. Files changed

| File | Change |
|------|--------|
| `apps/api/app/services/import_parsers/fdl_pdf_v1.py` | `_is_block_title_line()` — font band 8.0–8.5, no weight in title, no width gate; noise advisory skip; family reset on every block title |
| `apps/api/app/services/import_audit/page_extraction.py` | Uses `_is_block_title_line` for `family_header` audit kind |
| `apps/api/app/services/import_grouping.py` | Extended bumper prefixes (DOBHT/DOBCC/DOBF); new `cross_training_block_family` tier; alpha-kit `explicit_one_per_sku` path |
| `apps/api/app/services/seed_catalog.py` | Seed defaults for block family + alpha kit regex |
| `apps/api/app/services/seed_taxonomy_mapping_rules.py` | Keyword rules: soporte discos/sopote, slam ball, wall ball |
| Tests + fixtures | `page12_mixed_blocks.json`, parser/grouping/taxonomy/audit tests |

**Not changed:** frontend, migrations, `import_review.py` gates, page-number logic.

## 3. Parser — block title detection

`_is_block_title_line()` (alias `_is_family_header_line`):

- Font **8.0–8.5**
- Not section/subheader/SKU/EAN/price/noise advisory
- Min **15** characters
- **No** `\d+ kgs?` weight pattern in title line
- **No bbox width gate** (short titles like "Slam Ball - Negro" at width ~0.10 are valid)

State machine: on block title → finalize buffer with **previous** family → **replace** `active_family` → do not append title to variant buffer.

Noise lines (`el color del articulo puede variar`) skipped entirely.

## 4. Grouping

### Extended `cross_training_bumper_family`

```python
"cross_training_bumper_family_regex": r"^(?P<prefix>DOBHT|DOBCC|DOBF|DOB3C|DOBC|DOBN|DOB)(?P<size>\d{3})$",
"cross_training_bumper_prefixes": ["DOBHT", "DOBCC", "DOBF", "DOB3C", "DOBC", "DOBN", "DOB"],
```

### New `cross_training_block_family`

- Section root CROSSTRAINING, category `cross-training`
- Requires `family_block_id` + `family_header_raw`
- Name tokens: `slam ball` OR `wall ball`
- SKU: `^CRO\d{2,4}[A-Z]?$`
- `master_key` from block header (e.g. `CRO-SLAM-NEGRO`, `CRO-WALL-COLOR`)
- Variants group only within same block

### Alpha kit explicit 1:1 (DOBMINI)

Guarded path when:

- `family_header_raw` present
- SKU matches `^[A-Z]{3,12}$` (letters only)
- CROSSTRAINING section + full-confidence mapped category
- Not in false-family guards

## 5. Taxonomy

| Priority | Rule | Target |
|----------|------|--------|
| 23 | CROSSTRAINING + `soporte discos` | soportes-y-mancuerneros |
| 23 | CROSSTRAINING + `sopote` | soportes-y-mancuerneros |
| 31 | CROSSTRAINING + `slam ball` | cross-training |
| 32 | CROSSTRAINING + `wall ball` | cross-training |

Soporte rules use specific keywords to avoid false positives (e.g. "Soporte tipo bici" stays cross-training).

## 6. Expected page 12 outcome

| Metric | Before | After |
|--------|--------|-------|
| Imported | 38/39 | **39/39** |
| Block titles detected | 2 | **≥7** |
| Masters | 38 × 1:1 | **~8–12 families** + 1:1 (SOP025, DOBMINI) |
| CRO taxonomy | discos (contaminated) | **cross-training** |
| DOBMINI | blocked | **imported** explicit 1:1 |

## 7. Regression pages

Pages **3, 4, 5, 11** must remain **pass** after changes (no page-number logic).

## 8. Tests

| File | Coverage |
|------|----------|
| `test_import_parser_page12_blocks.py` | Block title detection, clean headers, ≥7 boundaries |
| `test_import_grouping_page12_blocks.py` | DOBHT/DOBCC/DOBF, CRO blocks, DOBMINI |
| `test_taxonomy_page11_mapping.py` | Slam ball clean name, soporte → soportes |
| `test_import_audit_page_import.py` | `test_page_import_page12_fresh` |

## 9. Validation commands

```powershell
npm run docker:up
npm run test:api:full
npm run db:reset:full:wipe
npm run audit:page-import -- 12 both
npm run audit:page-import -- 11 both
npm run audit:page-import -- 3 both
npm run audit:page-import -- 4 both
npm run audit:page-import -- 5 both
```

## 10. Fresh Reset Persistence Checklist

All fixes survive `npm run db:reset:full:wipe`:

- [x] Parser block-title logic in `fdl_pdf_v1.py` (production code, not audit-only)
- [x] Grouping tiers + alpha kit path in `import_grouping.py`
- [x] Profile defaults merged via `ensure_fdl_profile_grouping_config` in `seed_catalog.py`
- [x] Taxonomy rules idempotent in `seed_taxonomy_mapping_rules.py` (via `seed_pim` / `db:seed:pim`)
- [x] No migrations required
- [x] Integration test `test_page_import_page12_fresh` proves end-to-end after fresh seed

## 11. Rollback

Revert parser block-title changes + grouping/taxonomy seed rows; run `npm run db:seed:pim` to re-idempotentize rules.

## 12. Out of scope

Frontend, migrations, page-number checks, global prefix+number grouping, review gate relaxation, PDF-created categories.
