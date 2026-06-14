# API-1 Validation Checklist

Agent 2 use-only checklist for signing off the QA/stress catalogue seeder.

**Dependency:** API-1  
**Scope:** `seed_stress_catalog.py`, CLI, tests, `STRESS_CATALOG_SEED.md`

## Commands

```bash
npm run test:api:integration -- tests/test_seed_stress_catalog.py tests/test_stress_seed_integration.py
docker compose exec -e PYTHONPATH=/app api python scripts/seed_stress_catalog.py --dry-run
npm run db:seed:stress:fresh
npm run db:seed:stress   # idempotent re-run
```

## Acceptance criteria

| # | Criterion | Pass | Evidence |
|---|-----------|------|----------|
| 1 | One command → ~300–400 catalogue lines | | `catalog_items` count |
| 2 | ~350 masters (default `--masters`) | | CLI output |
| 3 | All 6 profiles present | | `profile_counts` |
| 4 | 5 incompatible `single_standard` layout overrides | | `layout_overrides >= 5` |
| 5 | 15+ categories used | | distinct `category_id` on stress masters |
| 6 | Catalogue line `sort_order` populated (0..N-1) | | DB query on `catalog_items` |
| 7 | `--fresh` deletes STRESS-* only | | non-stress data intact |
| 8 | Idempotent re-run (no duplicate masters) | | second run `masters_created == 0` |
| 9 | Unit + integration tests pass | | pytest exit 0 |
| 10 | Layout modes covered | | `single_standard`, `variant_grid_50_50`, `variant_row_wide` in layout-status |

## Profile labels (expected in `profile_counts`)

- `single`
- `grid_1attr`
- `row_2attr`
- `no_image`
- `no_category`
- `incomplete_variants`

## Contract Summary template

After all checks pass, publish `API-1_CONTRACT_SUMMARY.md` with:

```
Agent: 2
Dependency ID: API-1
Status recommendation: CONFIRMED / DONE
Commands: npm run db:seed:stress / db:seed:stress:fresh
Catalog name: QA Stress Catalog
Counts: masters, variants, catalog_items, categories, layout_overrides
Profiles confirmed: [list]
Tests run: [commands + pass/fail]
Docs: STRESS_CATALOG_SEED.md
QA unblocked: MANUAL_QA_BUILDER_UI sections B, C, G; MANUAL_QA_PRESENTATION_BUILDER stress scenarios
Agent 4 integration scope: none (seeder-only)
```
