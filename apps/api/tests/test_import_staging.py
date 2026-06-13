"""Tests for import batch staging."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.models import ImportBatch, ImportProfile, Supplier
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_staging import bulk_insert_rows, create_batch, get_batch_rows


def _parsed_row(index: int = 0) -> ImportRow:
    return ImportRow(
        row_index=index,
        status=RowStatus.OK,
        sku="DOBNEXO05N",
        name="Disco Bumper NEXO Negro - 5 kgs",
        raw_name="Disco Bumper NEXO Negro - 5 kgs",
        normalized_name="Disco Bumper NEXO Negro - 5 kgs",
        brand="NEXO",
        ean="1234567890123",
        category_path="DISCOS Y BARRAS",
        price_amount=Decimal("19.55"),
        raw_lines=["line one", "19,55 €"],
        page_number=3,
        master_key="DOBNEXON",
        master_name="Disco Bumper NEXO Negro",
        parsed_variant_specs_raw={"peso_kg": 5},
        grouping_confidence=0.95,
        grouping_reason="fdl_sku_family:DOBNEXON",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_batch_and_bulk_insert_rows(integration_db):
    from app.database import async_session

    async with async_session() as session:
        supplier = Supplier(code=f"T{uuid4().hex[:6].upper()}", name="Test Supplier")
        session.add(supplier)
        await session.flush()

        profile = ImportProfile(
            supplier_id=supplier.id,
            slug="test",
            name="Test",
            parser_key="fdl_pdf_v1",
        )
        session.add(profile)
        await session.flush()

        batch = await create_batch(
            session,
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="test.pdf",
            parser_key="fdl_pdf_v1",
        )
        await bulk_insert_rows(session, batch.id, [_parsed_row()])
        await session.commit()

        stored = await get_batch_rows(session, batch.id)
        assert len(stored) == 1
        row = stored[0]
        assert isinstance(batch, ImportBatch)
        assert row.raw_lines == ["line one", "19,55 €"]
        assert row.parsed_variant_specs_raw == {"peso_kg": 5}
        assert row.grouping_reason == "fdl_sku_family:DOBNEXON"
