"""Tests for catalogue layout configuration persistence helpers."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from app.services.catalog_builder import _build_product_block
from app.services.spec_resolver import SpecColumn
from tests.model_test_factories import (
    make_allowed_value,
    make_catalog_item,
    make_product_master,
    make_product_variant,
    make_spec_definition,
    make_unit,
    make_variant_spec,
)


def _master(name: str = "Product"):
    return make_product_master(name, master_id=UUID("00000000-0000-0000-0000-000000000001"))


def _variant_rows(*, multi_attr: bool = True, multi_variant: bool = True):
    if not multi_variant:
        return [
            {
                "sku": "A-1",
                "peso_kg": "10 kg",
                "color": "Rojo" if multi_attr else None,
                "price_display": "10,00 €",
                "sort_order": 0,
                "_variant_images": [],
            }
        ]
    return [
        {
            "sku": "A-1",
            "peso_kg": "8 kg",
            "color": "Rosa" if multi_attr else None,
            "price_display": "10,00 €",
            "sort_order": 0,
            "_variant_images": [],
        },
        {
            "sku": "A-2",
            "peso_kg": "12 kg",
            "color": "Azul" if multi_attr else None,
            "price_display": "12,00 €",
            "sort_order": 1,
            "_variant_images": [],
        },
    ]


def _columns():
    return [
        SpecColumn(
            key="peso_kg",
            label="Peso",
            sort_order=0,
            spec_definition_id=uuid4(),
            data_type="number",
            role="variant_axis",
        ),
        SpecColumn(
            key="color",
            label="Color",
            sort_order=1,
            spec_definition_id=uuid4(),
            data_type="enum",
            role="catalog_spec",
        ),
    ]


def test_build_product_block_automatic_multi_attribute():
    block = _build_product_block(
        _master(), _variant_rows(multi_attr=True), _columns(), [], False, ""
    )
    assert block["layout_id"] == "variant_row_wide"
    assert block["layout_selection"]["selection_mode"] == "automatic"
    assert not block["layout_selection"]["fallback_used"]


def test_build_product_block_uniform_fallback_when_incompatible():
    block = _build_product_block(
        _master(),
        _variant_rows(multi_attr=True),
        _columns(),
        [],
        False,
        "",
        layout_mode="uniform",
        uniform_layout_id="single_standard",
    )
    assert block["layout_id"] == "variant_row_wide"
    assert block["layout_selection"]["fallback_used"]
    assert block["layout_selection"]["requested_layout_id"] == "single_standard"


def test_build_product_block_uniform_applies_to_compatible_single():
    block = _build_product_block(
        _master(),
        _variant_rows(multi_variant=False),
        _columns(),
        [],
        False,
        "",
        layout_mode="uniform",
        uniform_layout_id="single_standard",
    )
    assert block["layout_id"] == "single_standard"
    assert not block["layout_selection"]["fallback_used"]


def test_build_product_block_manual_override():
    block = _build_product_block(
        _master(),
        _variant_rows(multi_attr=False),
        _columns(),
        [],
        False,
        "",
        layout_mode="manual",
        manual_layout_id="variant_row_wide",
    )
    assert block["layout_id"] == "variant_row_wide"
    assert block["layout_selection"]["requested_layout_id"] == "variant_row_wide"


def test_build_product_block_manual_missing_override_falls_back():
    block = _build_product_block(
        _master(),
        _variant_rows(multi_attr=False),
        _columns(),
        [],
        False,
        "",
        layout_mode="manual",
        manual_layout_id=None,
    )
    assert block["layout_id"] == "variant_grid_50_50"
    assert block["layout_selection"]["fallback_used"]


@pytest.mark.asyncio
async def test_master_variant_rows_from_catalog_items():
    from app.services.catalog_layout import master_variant_rows_from_catalog_items

    peso_unit = make_unit(symbol="kg")
    peso_def = make_spec_definition(
        "peso_kg",
        label="Peso",
        data_type="number",
        unit=peso_unit,
        definition_id=uuid4(),
    )
    color_def = make_spec_definition(
        "color",
        label="Color",
        data_type="enum",
        scope="both",
        definition_id=uuid4(),
    )
    rojo = make_allowed_value(color_def, value_key="rojo", label="Rojo")
    azul = make_allowed_value(color_def, value_key="azul", label="Azul")
    master = make_product_master("Layout product")
    variant_one = make_product_variant(
        "A-1",
        master=master,
        specs=[
            make_variant_spec(peso_def, value_number=Decimal("10")),
            make_variant_spec(color_def, allowed_value=rojo),
        ],
    )
    variant_two = make_product_variant(
        "A-2",
        master=master,
        specs=[
            make_variant_spec(peso_def, value_number=Decimal("12")),
            make_variant_spec(color_def, allowed_value=azul),
        ],
    )
    items = [
        make_catalog_item(variant_one, sort_order=0),
        make_catalog_item(variant_two, sort_order=1),
    ]

    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))
    )

    state = await master_variant_rows_from_catalog_items(db, items)
    assert state["has_variants"] is True
    assert state["variant_attribute_count"] == 2
