"""Integration tests for CARDIO subsection taxonomy mapping (PR-H)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select
from tests.taxonomy_test_utils import reset_taxonomy_rules_to_seed

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

POSITIVE_FIXTURES = (
    "cardio_remo_rows.json",
    "cardio_cinta_rows.json",
    "cardio_eliptica_rows.json",
    "cardio_bici_rows.json",
)

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
}


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _parser_row(item: dict) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=item["sku"],
        name=item["name"],
        brand="NEXO",
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("100.00"),
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
async def test_cardio_subsection_maps_to_subcategory(integration_db, fixture_name: str):
    fixture = _load_fixture(fixture_name)
    expected_slug = fixture["expected_subcategory_slug"]

    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        rows = [_parser_row(item) for item in fixture["rows"]]
        rows = await map_row_categories(session, rows, supplier.id, profile.id)

    for row in rows:
        assert row.mapped_category_slug == expected_slug
        assert row.mapped_category_confidence == 1.0
        assert "unmapped_category" not in row.review_reasons


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cardio_substring_false_positive_does_not_map(integration_db):
    fixture = _load_fixture("cardio_substring_false_positive.json")
    forbidden = set(fixture["forbidden_subcategory_slugs"])

    async with async_session() as session:
        await seed_default_categories(session)
        await reset_taxonomy_rules_to_seed(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        rows = [_parser_row(item) for item in fixture["rows"]]
        rows = await map_row_categories(session, rows, supplier.id, profile.id)

    for row in rows:
        assert row.mapped_category_slug not in forbidden
        assert row.mapped_category_slug == "cross-training"
        assert "unmapped_category" not in row.review_reasons


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cardio_ski_maps_to_parent_cardio(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        row = _parser_row(
            {"sku": "SKI002", "name": "Soporte pared Ski", "category_path": "CARDIO > SKI"}
        )
        rows = await map_row_categories(session, [row], supplier.id, profile.id)

    assert rows[0].mapped_category_slug == "cardio"
    assert rows[0].mapped_category_confidence == 1.0
    assert "unmapped_category" not in rows[0].review_reasons


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sku", "name", "category_path", "expected_slug"),
    [
        (
            "BIC010",
            "Bicileta Air Bike 1000 Eco (NO smart conect)",
            "CARDIO > BICI",
            "bicicletas-estaticas",
        ),
        ("REM002", "Remo Air Rower 2,0 (NO smart conect)", "CARDIO > REMO", "remos"),
        ("CIN001", "Cinta Curva sin Motor", "CARDIO > CINTA", "cintas-de-correr"),
    ],
)
async def test_explicit_one_per_sku_unlocks_mapped_cardio_rows(
    integration_db, sku: str, name: str, category_path: str, expected_slug: str
):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        row = _parser_row({"sku": sku, "name": name, "category_path": category_path})
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]
        apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
        row.review_status = resolve_review_status(row)

    assert row.mapped_category_slug == expected_slug
    assert "unmapped_category" not in row.review_reasons
    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.grouping_confidence is not None
    assert row.grouping_confidence >= 0.85
    assert "regex_fallback_1_1" not in row.review_reasons
    assert "low_grouping_confidence" not in row.review_reasons
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate


@pytest.mark.integration
@pytest.mark.asyncio
async def test_taxonomy_alone_does_not_unlock_false_family_rows(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        row = _parser_row(
            {
                "sku": "CRO107NEXO",
                "name": "Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
                "category_path": "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            }
        )
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]
        apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
        row.review_status = resolve_review_status(row)

    assert "false_family_pattern" not in row.review_reasons
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate
