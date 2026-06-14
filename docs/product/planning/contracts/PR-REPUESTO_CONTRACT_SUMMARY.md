# PR-REPUESTO Contract Summary

**Agent:** 2  
**Dependency ID:** PR-REPUESTO (import pipeline)  
**Date:** 2026-06-07  
**Status:** `CONFIRMED`

---

## Problem

SKUs `REPUESTO-*` (e.g. REPUESTO-805, REPUESTO-806 from PDF page 3, section CARDIO > BICI) were parsed correctly but blocked at confirm:

- Taxonomy rule `MATCH_SKU_PREFIX` `REPUESTO-` → slug `repuestos` (priority 10) overrode section mapping.
- Grouping excluded REPUESTO from `explicit_one_per_sku` and fell back to `one_per_sku_fallback` with `regex_fallback_1_1` + `low_grouping_confidence`.

## Changes (confirmed)

### Taxonomy

- Removed `REPUESTO-` from `DEFAULT_TAXONOMY_MAPPING_RULE_ROWS`.
- Added `RETIRED_TAXONOMY_MAPPING_RULE_KEYS`; seed sets `is_active=False` on existing `REPUESTO-` rules.
- REPUESTO-* inherit category from `section_path` (e.g. `CARDIO > BICI` → `bicicletas-estaticas`).

### Grouping

- Extended `explicit_numeric_sku_regex`:

```
^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$
```

- Removed REPUESTO exclusion from `_eligible_for_explicit_one_per_sku` (still excluded from `numeric_suffix_family`).
- Result: `grouping_reason=explicit_one_per_sku`, `master_key=<SKU>`, confidence 0.85, confirmable when section-mapped.

### Audit (Agent 5)

- `SamePageSkuFamily` skips groups where all SKUs match `^REPUESTO-\d+$`.

## Gates unchanged

`BLOCKING_REASONS` not relaxed. Still blocked: `unmapped_category`, `false_family_pattern`, `duplicate_sku`, `spec_validation_failed`, etc.

## Example: REPUESTO-806 (CARDIO > BICI)

| Field | After fix |
|-------|-----------|
| `mapped_category_slug` | `bicicletas-estaticas` |
| `master_key` | `REPUESTO-806` |
| `grouping_reason` | `explicit_one_per_sku` |
| `can_confirm` | `true` |

## Tests

```bash
pytest tests/test_taxonomy_repuesto_mapping.py tests/test_import_grouping_repuesto_explicit.py tests/test_import_grouping_explicit_one_per_sku.py tests/test_import_audit_variant_detection.py -q
```

## Validation commands

```powershell
npm run db:seed:pim
npm run test:api -- tests/test_taxonomy_repuesto_mapping.py tests/test_import_grouping_repuesto_explicit.py
npm run audit:variants -- --page 3
npm run audit:report -- variants
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_j.py
```

## Reseed required

Run `npm run db:seed:pim` to deactivate retired `REPUESTO-` taxonomy rule in existing databases.

## Risks

- REPUESTO-* without `category_path` remains `unmapped_category` (by design).
- Orphan `repuestos` category slug may remain in DB unused.
