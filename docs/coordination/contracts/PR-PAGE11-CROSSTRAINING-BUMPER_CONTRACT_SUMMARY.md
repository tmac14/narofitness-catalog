# PR-PAGE11-CROSSTRAINING-BUMPER Contract Summary

**Agent:** 2  
**Dependency ID:** PR-PAGE11 (import pipeline — cross-training bumper discs)  
**Date:** 2026-06-07  
**Status:** `CONFIRMED`

---

## Problem

PDF page 11 (CROSSTRAINING bumper discs) had 30 parsed rows but only 10 importable (`DOBNEXO*`):

| Cause | Symptom |
|-------|---------|
| Brand | `section_brand=null`; NEXO only in some product names → default `FDL` |
| Taxonomy | `section_path` rule used `CROSSTRAINING` but PDF path is `CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL`; `DOBN/DOB/DOB3C/DOBC` had no `sku_prefix` rules |
| Grouping | SKUs without letter suffix fell to `one_per_sku_fallback` → `regex_fallback_1_1` + `low_grouping_confidence` |

## Changes (confirmed)

### Brand inference (parser)

- Added `_infer_brand_from_product_text()` in `fdl_pdf_v1.py`.
- Scans concatenated product name lines only (never SKU).
- Uses `KNOWN_BRAND_TOKENS` with word-boundary regex; skips `FDL` and `VARIOS`.
- Priority: section header brand → standalone brand line → embedded name token → `FDL` supplier default.
- **Result:** `DOBNEXO*` rows (10) → `NEXO`; bumper rows without NEXO in name remain `FDL` (expected with current rules).

### Taxonomy

| Rule | Type | Value | Target | Priority |
|------|------|-------|--------|----------|
| Existing | sku_prefix | DOBNEXO | discos | 15 |
| **New** | sku_prefix | DOB3C | discos | 16 |
| **New** | sku_prefix | DOBC | discos | 17 |
| **New** | sku_prefix | DOBN | discos | 18 |
| **New** | sku_prefix | DOB | discos | 19 |
| **Fixed** | section_path | `CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL` | cross-training | 30 |

Non-bumper CROSSTRAINING products map to parent `cross-training`; only explicit `DOB*` prefixes map to `discos`.

### Grouping

New tier **`cross_training_bumper_family`** in `import_grouping.py` (after `numeric_suffix_family`, before `explicit_one_per_sku`):

```python
"cross_training_bumper_family_regex": r"^(?P<prefix>DOB3C|DOBC|DOBN|DOB)(?P<size>\d{3})$",
"cross_training_bumper_prefixes": ["DOB3C", "DOBC", "DOBN", "DOB"],
"cross_training_bumper_section_root": "CROSSTRAINING",
"cross_training_bumper_name_tokens": ["disco", "bumper"],
"cross_training_bumper_category_slug": "discos",
"cross_training_bumper_confidence": 0.90,
```

- `master_key = prefix` (DOB3C ≠ DOBC ≠ DOBN ≠ DOB).
- `peso_kg` from product name (`_extract_peso_kg_from_name`), **not** from SKU size digits.
- Requires mapped category slug `discos` and CROSSTRAINING section root.
- `DOBNEXO*` unchanged (`fdl_sku_family:DOBNEXON/DOBNEXOC`).

Profile defaults merged via `ensure_fdl_profile_grouping_config` and `001_pim_schema.py`.

## Design principles

Page 11 is a **reproducible audit case**, not a condition in any import rule. All fixes are pattern-based business rules with explicit allowlists and guards.

### Allowed (implemented)

- Brand inference from product name text (`KNOWN_BRAND_TOKENS`, word-boundary, never SKU).
- Taxonomy `sku_prefix` allowlist (DOBNEXO, DOB3C, DOBC, DOBN, DOB) → `discos`, ordered by prefix length.
- Taxonomy `section_path` for CROSSTRAINING → parent `cross-training` (not `discos`).
- Grouping tier `cross_training_bumper_family` requiring **all** of: CROSSTRAINING section root, name tokens (`disco` + `bumper`), mapped slug `discos`, and prefix allowlist.

### Prohibited (verified absent in `apps/api/app/`)

- `page_number == 11` (or any page-specific import logic).
- Page-specific category, brand, or grouping overrides.
- Global grouping of arbitrary prefix + number.
- Mapping the entire CROSSTRAINING section to `discos` without product/SKU guards.

### Defense in depth

| Layer | What maps to `discos` | Guard |
|-------|----------------------|-------|
| Taxonomy | Explicit `DOB*` SKU prefixes only | Priority-ordered allowlist; rest of section → `cross-training` |
| Grouping | `cross_training_bumper_family` | Section + name tokens + category slug + prefix regex |

Brand `NEXO` applies only when the token appears in product name lines (e.g. DOBNEXO* headers/names). Bumper rows without NEXO in name keep supplier default `FDL`.

### Production audit

```text
rg "page_number\s*==\s*11|page\s*==\s*11" apps/api/app
# → no matches (import rules never branch on page number)
```

## Gates unchanged

`import_review.py` blocking gates not relaxed. Still blocked: `false_family_pattern`, `duplicate_sku`, `unmapped_category`, etc.

## Guardrails preserved

- BOCNEXO / CRONEXO → `false_family_pattern`
- DOP / MU / MP / MPS numeric families unchanged
- REPUESTO-* → `explicit_one_per_sku` (page 3 regression pass)
- Cardio substring false positives → `cross-training`, not cardio subcategories

## Audit metrics (page 11 — after)

| Metric | Before | After |
|--------|--------|-------|
| status | fail | **pass** |
| parsed | 30 | 30 |
| imported | 10 | **30** |
| blocked | 20 | **0** |
| category (DOB*) | unmapped | **discos** |
| masters | DOBNEXON, DOBNEXOC | **+ DOBN, DOB, DOB3C, DOBC** (6 families) |
| grouping | fallback | `cross_training_bumper_family:*` / `fdl_sku_family:*` |

Page 3 regression: **pass** (8 imported, REPUESTO-805/806 confirmable).

## Tests

Pattern-based unit tests (synthetic fixtures, no page dependency):

- `test_import_grouping_cross_training_bumper.py` — positive grouping + negative section/name guards
- `test_taxonomy_page11_mapping.py` — sku_prefix allowlist + CROSSTRAINING → cross-training
- `test_import_parser_brands.py` — embedded brand from product name

Single PDF integration case (page 11 as reproducible audit only):

- `test_import_audit_page_import.py::test_page_import_page11_fresh`

```bash
pytest tests/test_import_parser_brands.py tests/test_taxonomy_page11_mapping.py tests/test_import_grouping_cross_training_bumper.py tests/test_import_audit_page_import.py::test_page_import_page11_fresh -q
```

## Validation commands

```powershell
npm run db:seed:pim
docker compose exec -e PYTHONPATH=/app api python scripts/audit_page_import.py --page 11 --ensure-pim-seed --format both
docker compose exec -e PYTHONPATH=/app api python scripts/audit_page_import.py --page 3 --ensure-pim-seed --format both
```

## Reseed required

Run `npm run db:seed:pim` to apply new taxonomy rules and FDL grouping profile defaults.

## Risks

- `DOB` sku_prefix is broad; mitigated by priority ordering (DOB3C/DOBC/DOBN/DOBNEXO match first) and regression tests.
- Bumper rows without "NEXO" in name keep supplier default brand `FDL` unless a future rule propagates section brand.
