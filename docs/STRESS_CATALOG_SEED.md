# Stress catalogue seed

Generates a large test catalogue for manual QA of the Presentation builder, preview, and PDF export.

## What it creates

| Item | Details |
|------|---------|
| **Catalogue name** | `QA Stress Catalog` (configurable with `--name`) |
| **Product masters** | ~350 by default (`--masters N`) |
| **Variants** | ~946 catalogue lines (~400+ variant rows across 350 masters) |
| **SKU prefix** | `STRESS-` (e.g. `STRESS-0042-01`) |
| **Master key prefix** | `STRESS-M` (e.g. `STRESS-M0042`) |
| **Categories** | Ensures default taxonomy exists; distributes products across 15+ categories |
| **Layout overrides** | 5 incompatible `single_standard` overrides on multi-attribute products; `row_2attr` masters get `variant_row_wide` override |
| **Catalog layout mode** | `manual` (per-product overrides active; others fall back to automatic heuristic) |

### Product profiles (deterministic)

- **single** — one variant, no attributes → `single_standard`
- **grid_1attr** — 2–4 variants, weight only → `variant_grid_50_50`
- **row_2attr** — 2–4 variants, weight + color → `variant_row_wide`
- **no_image** — no `ProductImage` row → diagnostic `no_image`
- **no_category** — `category_id = null` → section General
- **incomplete_variants** — multiple variants without weight/color → warning diagnostic

## Commands

From the repository root (requires Docker API running):

```bash
# Create or update the stress catalogue
npm run db:seed:stress

# Delete and recreate from scratch
npm run db:seed:stress:fresh

# Preview counts without writing
docker compose exec -e PYTHONPATH=/app api python scripts/seed_stress_catalog.py --dry-run
```

Direct CLI (inside API container):

```bash
python scripts/seed_stress_catalog.py
python scripts/seed_stress_catalog.py --fresh
python scripts/seed_stress_catalog.py --masters 400 --name "My QA Catalog"
```

## How to identify the catalogue

1. CLI prints **Catalog name** and **Catalog ID** (UUID) when finished.
2. In the desktop app: **Catálogos** → look for **QA Stress Catalog**.
3. Product SKUs all start with `STRESS-`.

## How to delete or regenerate

```bash
# Recommended: fresh recreate
npm run db:seed:stress:fresh
```

This removes only the stress catalogue and products with SKU prefix `STRESS-*`. It does **not** wipe the full database.

## Prerequisites

Single squashed migration: `001_pim_schema` (head).

Specs are stored in `product_variant_specs` / `product_master_specs` — not JSONB `variant_attrs`.

```bash
# Con código montado (desarrollo)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
npm run db:migrate
```

- FDL supplier exists (created by migration `001`)

## Testing layout fallbacks manually

The catalogue is created in **automatic** layout mode. To force fallbacks:

1. Open the catalogue → **Presentación** tab.
2. Switch to **Uniforme** → select `single_standard` → save.
3. Filter by **Con fallback** or open **Diagnóstico**.

Pre-seeded layout overrides (5 products) will show incompatible manual assignments when you switch to manual mode.
