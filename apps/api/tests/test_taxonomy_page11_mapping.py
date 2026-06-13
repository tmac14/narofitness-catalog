"""Tests for cross-training bumper taxonomy mapping (PR-PAGE11)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.database import async_session
from app.models import Category, ImportProfile, Supplier
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

CROSSTRAINING_PATH = "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL"


def _parser_row(*, sku: str, name: str, category_path: str = CROSSTRAINING_PATH) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        raw_name=name,
        normalized_name=name,
        brand="FDL",
        ean=None,
        category_path=category_path,
        price_amount=Decimal("18.80"),
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sku",
    ["DOBN005", "DOB005", "DOB3C005", "DOBC005", "DOBNEXO05N"],
)
async def test_bumper_sku_prefix_maps_to_discos(integration_db, sku: str):
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
            sku=sku,
            name="Disco Bumper Negro 3.0 - 5 kgs",
        )
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "discos"
    assert row.mapped_category_id is not None
    assert row.mapped_category_confidence >= 0.9


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crosstraining_generic_sku_maps_to_cross_training_not_discos(integration_db):
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
        cross_training = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        row = _parser_row(
            sku="CRO110",
            name="Slam Ball - Negro",
        )
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "cross-training"
    assert row.mapped_category_slug != "discos"
    assert row.mapped_category_id == cross_training.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crosstraining_section_path_maps_non_dob_to_cross_training(integration_db):
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
        cross_training = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        row = _parser_row(
            sku="CRO107NEXO",
            name="Cronometro NEXO",
        )
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "cross-training"
    assert row.mapped_category_id == cross_training.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crosstraining_slam_ball_clean_name_maps_cross_training(integration_db):
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
        cross_training = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        row = _parser_row(
            sku="CRO110",
            name="Slam Ball 6 kgs Negro",
        )
        row.taxonomy_name = "Slam Ball -  Negro Slam Ball 6 kgs Negro"
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "cross-training"
    assert row.mapped_category_slug != "discos"
    assert row.mapped_category_id == cross_training.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soporte_maps_to_soportes_not_discos(integration_db):
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
        soportes = (
            await session.execute(
                select(Category).where(Category.slug == "soportes-y-mancuerneros")
            )
        ).scalar_one()
        row = _parser_row(
            sku="SOP025",
            name="Soporte Discos Bumper",
        )
        row.taxonomy_name = "Soporte Discos Bumper Sopote para juego de Discos Bumper"
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "soportes-y-mancuerneros"
    assert row.mapped_category_slug != "discos"
    assert row.mapped_category_id == soportes.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dobn_not_matched_by_dob_prefix(integration_db):
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
            sku="DOBN005",
            name="Disco Bumper Negro 3.0 - 5 kgs",
        )
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "discos"
    discos = (await session.execute(select(Category).where(Category.slug == "discos"))).scalar_one()
    assert row.mapped_category_id == discos.id
