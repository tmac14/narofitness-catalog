"""Tests for parsed spec validation at staging."""

from decimal import Decimal

import pytest
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import resolve_review_status
from app.services.import_spec_validate import validate_parsed_specs_batch
from app.services.seed_spec_definitions import seed_spec_definitions

FDL_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
        "attr_from_name": {
            "color": ["Negro"],
            "material": ["Goma maciza"],
            "casquillo": ["Acero"],
        },
    },
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_spec_key_flags_needs_review(integration_db):
    from app.database import async_session

    row = ImportRow(
        row_index=1,
        status=RowStatus.OK,
        sku="TESTSKU01",
        name="Test",
        brand=None,
        ean=None,
        category_path="X",
        price_amount=Decimal("10"),
        parsed_common_specs_raw={"not_a_real_spec": "value"},
    )
    async with async_session() as session:
        await seed_spec_definitions(session)
        errors = await validate_parsed_specs_batch(session, [row])
        row.review_status = resolve_review_status(row)
    assert errors[1]
    assert "unknown_spec_key" in row.review_reasons
    assert row.review_status == "needs_review"


def test_dobnexo_extracts_common_specs_from_name():
    row = ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku="DOBNEXO05N",
        name="Disco Bumper NEXO Negro - 5 kgs (Goma maciza, casquillo de acero)",
        brand="NEXO",
        ean=None,
        category_path="CROSSTRAINING",
        price_amount=Decimal("19.55"),
    )
    apply_grouping([row], FDL_CONFIG)
    assert row.parsed_variant_specs_raw.get("peso_kg") == 5
    assert row.parsed_common_specs_raw.get("color") == "Negro"
    assert row.parsed_common_specs_raw.get("material") == "Goma maciza"
    assert row.parsed_common_specs_raw.get("casquillo") == "Acero"
