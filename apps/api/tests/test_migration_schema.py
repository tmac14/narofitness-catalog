"""Smoke test that PIM schema tables exist after migrate."""

import os

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

PIM_TABLES = {
    "units",
    "spec_definitions",
    "spec_allowed_values",
    "product_master_specs",
    "product_variant_specs",
    "category_spec_profiles",
    "import_batches",
    "import_rows",
    "taxonomy_mapping_rules",
    "supplier_product_family_keys",
}

REMOVED_TABLES = {"product_attributes", "product_master_attributes"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pim_tables_exist(integration_db):
    engine = create_async_engine(integration_db)
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    await engine.dispose()

    missing = PIM_TABLES - tables
    assert not missing, f"Missing PIM tables: {missing}"

    for removed in REMOVED_TABLES:
        assert removed not in tables, f"Legacy table still present: {removed}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_product_variants_no_variant_attrs(integration_db):
    engine = create_async_engine(integration_db)
    async with engine.connect() as conn:
        cols = await conn.run_sync(
            lambda c: {col["name"] for col in inspect(c).get_columns("product_variants")}
        )
    await engine.dispose()
    assert "variant_attrs" not in cols, "variant_attrs column must not exist in PIM schema"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fdl_supplier_seeded(integration_db):
    engine = create_async_engine(integration_db)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT code FROM suppliers WHERE code = 'FDL'"))
        row = result.first()
    await engine.dispose()
    if os.getenv("SKIP_SEED_CHECK") == "1":
        pytest.skip("Seed check skipped")
    assert row is not None, "FDL supplier should be seeded by migration"
