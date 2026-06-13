# API-1 Contract Summary

**Agent:** 2  
**Dependency ID:** API-1  
**Date:** 2026-06-07  
**Status recommendation:** Phase 1 `PASS_WITH_WARNINGS` (backend `CONFIRMED`; scale QA complete — no Agent 4 step)

---

## Commands

| Command | Purpose |
|---------|---------|
| `npm run db:seed:stress` | Create or update QA Stress Catalog (idempotent) |
| `npm run db:seed:stress:fresh` | Delete `STRESS-*` data and recreate |
| `npm run audit:api1` | Run post-seed validation audit |
| `npm run audit:report -- api1` | Copy post-seed validation report to `temp/` |

Dry-run (inside container):

```bash
docker compose exec -e PYTHONPATH=/app api python scripts/seed_stress_catalog.py --dry-run
```

---

## Output contract

| Field | Value |
|-------|-------|
| **Catalog name** | `QA Stress Catalog` (override with `--name`) |
| **Catalog layout mode** | `manual` (per-product overrides active; others fall back to automatic) |
| **Masters (default)** | 350 |
| **Catalogue lines** | ~946 variant rows |
| **SKU prefix** | `STRESS-` |
| **Master key prefix** | `STRESS-M` |
| **Categories** | 24 distinct on stress masters (≥15 required) |
| **Layout overrides** | 5 incompatible `single_standard` + 67 `variant_row_wide` on `row_2attr` |

### Profile distribution (350 masters)

| Profile | Count | Expected layout |
|---------|-------|-----------------|
| `single` | 73 | `single_standard` (automatic fallback) |
| `grid_1attr` | 73 | `variant_grid_50_50` |
| `row_2attr` | 72 | `variant_row_wide` (manual override) |
| `no_image` | 60 | automatic + `no_image` diagnostic |
| `no_category` | 32 | General section |
| `incomplete_variants` | 40 | warning diagnostic |

### Layout modes in catalog context

All three registry modes present: `single_standard`, `variant_grid_50_50`, `variant_row_wide`.

---

## Validation evidence

| Check | Result |
|-------|--------|
| `test_seed_stress_catalog.py` | 7 passed |
| `test_stress_seed_integration.py` | 3 passed |
| `audit_api1_stress_seeder.py` | **pass** |
| Idempotent re-run | `masters_created=0`, items skipped |
| `--fresh` safety | Deletes `STRESS-*` prefix only |
| `sort_order` | Contiguous 0..945 on catalog items |

Report artifact: `temp/api1_validation_report.json`

---

## Breaking changes

None. Seeder is additive; does not modify FDL import or PIM seed.

---

## Agent 4 integration scope

**None** — CLI/seeder only. User opens catalogue by name in desktop app.

---

## QA unblocked

- `docs/MANUAL_QA_BUILDER_UI.md` sections B, C, G (~350 products)
- `docs/MANUAL_QA_PRESENTATION_BUILDER.md` stress scenarios
- `docs/coordination/tasks/CATALOGUE-BUILDER-OPEN-QA.md` for remaining catalogue-builder QA

---

## Open issues

None blocking confirmation.

---

## Docs updated

- `docs/STRESS_CATALOG_SEED.md` — layout mode, variant counts, row_wide overrides
- `docs/coordination/contracts/API-1_VALIDATION_CHECKLIST.md` — Agent 2 checklist
