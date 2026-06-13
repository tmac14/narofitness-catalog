"""End-to-end confirm import with normalized specs (DOBNEXO family)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import (
    Category,
    ImportBatch,
    ImportProfile,
    ImportRow,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    Supplier,
    SupplierPriceEntry,
    SupplierProductFamilyKey,
    TaxonomyMappingRule,
)
from app.services.import_confirm import confirm_import
from app.services.seed_categories import seed_default_categories
from app.services.seed_spec_definitions import seed_spec_definitions
from sqlalchemy import select
from sqlalchemy.orm import selectinload

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "dobnexo_family.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


async def _seed_taxonomy_rules(session, discos_id) -> None:
    existing = (
        await session.execute(
            select(TaxonomyMappingRule).where(
                TaxonomyMappingRule.match_type == "section_keyword",
                TaxonomyMappingRule.match_value == "disco",
            )
        )
    ).scalar_one_or_none()
    if existing:
        return
    session.add(
        TaxonomyMappingRule(
            match_type="section_keyword",
            match_value="disco",
            priority=50,
            target_category_id=discos_id,
            confidence=Decimal("0.95"),
            requires_review=False,
            is_active=True,
        )
    )
    await session.commit()


async def _create_batch_from_fixture(
    session, fixture: dict, supplier_id, profile_id
) -> tuple[ImportBatch, list[ImportRow]]:
    batch = ImportBatch(
        supplier_id=supplier_id,
        import_profile_id=profile_id,
        source_filename=fixture["source_filename"],
        parser_key=fixture["parser_key"],
        parser_version=fixture["parser_version"],
        effective_date=date.fromisoformat(fixture["effective_date"]),
        status="completed",
    )
    session.add(batch)
    await session.flush()

    rows: list[ImportRow] = []
    for item in fixture["rows"]:
        row = ImportRow(
            batch_id=batch.id,
            source_row_index=item["source_row_index"],
            raw_lines=[item["raw_name"]],
            raw_name=item["raw_name"],
            normalized_name=item["normalized_name"],
            detected_category_path_raw=fixture["detected_category_path_raw"],
            brand_raw=item["brand_raw"],
            sku=item["sku"],
            ean=item["ean"],
            price_amount=Decimal(item["price_amount"]),
            currency=item.get("currency", "EUR"),
            master_key=item["master_key"],
            master_name=item["master_name"],
            reference_label=item["reference_label"],
            grouping_confidence=Decimal(str(item["grouping_confidence"])),
            grouping_reason=item["grouping_reason"],
            parsed_variant_specs_raw=item["parsed_variant_specs_raw"],
            parsed_common_specs_raw=item["parsed_common_specs_raw"],
            review_status=item.get("review_status", "confirmed"),
        )
        session.add(row)
        rows.append(row)
    await session.commit()
    for row in rows:
        await session.refresh(row)
    await session.refresh(batch)
    return batch, rows


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_dobnexo_family_specs(integration_db):
    fixture = _load_fixture()

    async with async_session() as session:
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one_or_none()
        if not supplier:
            pytest.skip("FDL supplier not seeded")
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not profile:
            pytest.skip("FDL import profile not seeded")

        await seed_default_categories(session)
        await seed_spec_definitions(session)

        discos = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one_or_none()
        assert discos is not None
        await _seed_taxonomy_rules(session, discos.id)

        batch, rows = await _create_batch_from_fixture(session, fixture, supplier.id, profile.id)

        result = await confirm_import(
            session,
            batch_id=batch.id,
            row_ids=[row.id for row in rows],
            profile=profile,
        )

        assert result.rows_imported == 5
        assert result.entries_created == 5
        assert not result.spec_errors
        assert result.variants_created + result.variants_updated == 5

        master = (
            await session.execute(
                select(ProductMaster).where(ProductMaster.master_key == "DOBNEXON")
            )
        ).scalar_one()
        assert master.name == "Disco Bumper NEXO"
        assert master.category_id == discos.id

        family_key = (
            await session.execute(
                select(SupplierProductFamilyKey).where(
                    SupplierProductFamilyKey.supplier_id == supplier.id,
                    SupplierProductFamilyKey.source_master_key == "DOBNEXON",
                )
            )
        ).scalar_one()
        assert family_key.product_master_id == master.id

        variants = (
            (
                await session.execute(
                    select(ProductVariant)
                    .where(ProductVariant.product_master_id == master.id)
                    .order_by(ProductVariant.sku)
                )
            )
            .scalars()
            .all()
        )
        assert len(variants) == 5
        assert {v.sku for v in variants} == {
            "DOBNEXO05N",
            "DOBNEXO10N",
            "DOBNEXO15N",
            "DOBNEXO20N",
            "DOBNEXO25N",
        }

        spec_defs = {
            s.id: s for s in (await session.execute(select(SpecDefinition))).scalars().all()
        }

        master_specs = (
            (
                await session.execute(
                    select(ProductMasterSpec)
                    .where(ProductMasterSpec.master_id == master.id)
                    .options(selectinload(ProductMasterSpec.allowed_value))
                )
            )
            .scalars()
            .all()
        )
        master_by_key = {spec_defs[row.spec_definition_id].key: row for row in master_specs}
        assert master_by_key["color"].allowed_value.label == "Negro"
        assert master_by_key["material"].value_text == "Goma maciza"
        assert master_by_key["casquillo"].value_text == "Acero"

        variant_specs = (
            (
                await session.execute(
                    select(ProductVariantSpec)
                    .join(ProductVariant)
                    .where(ProductVariant.product_master_id == master.id)
                    .options(selectinload(ProductVariantSpec.spec_definition))
                )
            )
            .scalars()
            .all()
        )
        peso_by_sku: dict[str, Decimal] = {}
        variant_by_id = {v.id: v for v in variants}
        peso_def_id = next(s.id for s in spec_defs.values() if s.key == "peso_kg")
        for row in variant_specs:
            if row.spec_definition_id != peso_def_id:
                continue
            peso_by_sku[variant_by_id[row.variant_id].sku] = row.value_number
        assert peso_by_sku == {
            "DOBNEXO05N": Decimal("5"),
            "DOBNEXO10N": Decimal("10"),
            "DOBNEXO15N": Decimal("15"),
            "DOBNEXO20N": Decimal("20"),
            "DOBNEXO25N": Decimal("25"),
        }

        imported_rows = (
            (await session.execute(select(ImportRow).where(ImportRow.batch_id == batch.id)))
            .scalars()
            .all()
        )
        assert all(r.review_status == "imported" for r in imported_rows)
        assert all(r.confirmed_product_master_id == master.id for r in imported_rows)
        assert all(r.confirmed_product_variant_id is not None for r in imported_rows)

        price_entries = (
            (
                await session.execute(
                    select(SupplierPriceEntry).where(
                        SupplierPriceEntry.list_id == result.price_list.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(price_entries) == 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_dobnexo_reimport_price_update_only(integration_db):
    fixture = _load_fixture()

    async with async_session() as session:
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one_or_none()
        if not supplier:
            pytest.skip("FDL supplier not seeded")
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not profile:
            pytest.skip("FDL import profile not seeded")

        await seed_default_categories(session)
        await seed_spec_definitions(session)
        discos = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one()
        await _seed_taxonomy_rules(session, discos.id)

        batch1, rows1 = await _create_batch_from_fixture(session, fixture, supplier.id, profile.id)
        first = await confirm_import(
            session,
            batch_id=batch1.id,
            row_ids=[r.id for r in rows1],
            profile=profile,
        )
        assert first.variants_created + first.variants_updated == 5

    fixture2 = _load_fixture()
    fixture2["source_filename"] = f"reimport-{uuid4()}.pdf"

    async with async_session() as session:
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

        batch2, rows2 = await _create_batch_from_fixture(session, fixture2, supplier.id, profile.id)
        second = await confirm_import(
            session,
            batch_id=batch2.id,
            row_ids=[r.id for r in rows2],
            profile=profile,
        )

        assert second.masters_created == 0
        assert second.variants_created == 0
        assert second.variants_updated == 5
        assert second.entries_created == 5
