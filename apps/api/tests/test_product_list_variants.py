"""Tests for product list variant columns, weight dimension, visibility and sorting."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.services.spec_resolver import (
    SYNTHETIC_PESO_KEY,
    SYNTHETIC_PESO_LABEL,
    SpecColumn,
    build_variant_row_spec_values,
    consolidate_weight_columns,
    format_spec_display,
    list_column_label,
    sort_product_variants,
    visible_variant_columns,
)
from app.services.variant_representation import build_variant_table_presentation


def _column(
    key: str,
    label: str,
    sort_order: int = 0,
    *,
    role: str = "variant_axis",
) -> SpecColumn:
    return SpecColumn(
        key=key,
        label=label,
        sort_order=sort_order,
        spec_definition_id=uuid4(),
        data_type="text" if key == "color" else "number",
        role=role,
    )


def _spec_row(
    key: str,
    *,
    value_number: Decimal | None = None,
    value_text: str | None = None,
    unit_symbol: str | None = None,
    role: str = "variant_axis",
):
    unit = SimpleNamespace(symbol=unit_symbol) if unit_symbol else None
    definition = SimpleNamespace(
        id=uuid4(),
        key=key,
        label=key,
        data_type="number" if value_number is not None else "text",
        role=role,
        unit=unit,
        is_active=True,
        is_printable=True,
        sort_order=0,
        scope="variant",
    )
    allowed_value = None
    return SimpleNamespace(
        spec_definition=definition,
        spec_definition_id=uuid4(),
        value_number=value_number,
        value_text=value_text,
        value_boolean=None,
        allowed_value_id=None,
        allowed_value=allowed_value,
    )


def _variant(sku: str, specs: list, *, reference_label: str | None = None):
    return SimpleNamespace(
        id=uuid4(),
        sku=sku,
        specs=specs,
        reference_label=reference_label,
        display_name=sku,
        raw_name=sku,
        brand=None,
        brand_id=None,
        product_master_id=uuid4(),
    )


def test_consolidate_weight_columns_emits_unified_peso():
    columns = [
        _column("peso_kg", "Peso", 10),
        _column("peso_lb", "Peso (lbs)", 11),
        _column("color", "Color", 20, role="catalog_spec"),
    ]
    merged = consolidate_weight_columns(columns)
    assert [column.key for column in merged] == [SYNTHETIC_PESO_KEY, "color"]
    assert merged[0].label == SYNTHETIC_PESO_LABEL


def test_build_variant_row_spec_values_peso_lb_display():
    columns = consolidate_weight_columns([_column("peso_lb", "Peso (lbs)", 11)])
    variant = _variant(
        "CRO083",
        [_spec_row("peso_lb", value_number=Decimal("12"), unit_symbol="lbs")],
        reference_label="12 lb",
    )
    values = build_variant_row_spec_values(variant, columns)
    assert values[SYNTHETIC_PESO_KEY] == "12 lb"
    assert values["_spec_sort"][SYNTHETIC_PESO_KEY] == 12


def test_build_variant_row_spec_values_peso_kg_display():
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variant = _variant(
        "CRO095", [_spec_row("peso_kg", value_number=Decimal("5"), unit_symbol="kg")]
    )
    values = build_variant_row_spec_values(variant, columns)
    assert values[SYNTHETIC_PESO_KEY] == "5 kg"


def test_format_spec_display_peso_lb_uses_lb_not_lbs():
    row = _spec_row("peso_lb", value_number=Decimal("14"), unit_symbol="lbs")
    definition = row.spec_definition
    assert format_spec_display(row, definition, definition.unit) == "14 lb"


def test_visible_variant_columns_hides_uniform_color():
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    rows = [
        {"peso": "5 kg", "color": "Negro"},
        {"peso": "10 kg", "color": "Negro"},
        {"peso": "15 kg", "color": "Negro"},
    ]
    visible = visible_variant_columns(columns, rows)
    assert [column.key for column in visible] == [SYNTHETIC_PESO_KEY]


def test_visible_variant_columns_shows_color_when_values_differ():
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    rows = [
        {"peso": "5 kg", "color": "Naranja"},
        {"peso": "10 kg", "color": "Rojo"},
    ]
    visible = visible_variant_columns(columns, rows)
    assert [column.key for column in visible] == [SYNTHETIC_PESO_KEY, "color"]


def test_visible_variant_columns_shows_color_on_empty_mix():
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    rows = [
        {"peso": "5 kg", "color": "Naranja"},
        {"peso": "10 kg", "color": "Rojo"},
        {"peso": "30 kg", "color": None},
    ]
    visible = visible_variant_columns(columns, rows)
    assert "color" in [column.key for column in visible]


def test_visible_variant_columns_peso_first():
    columns = consolidate_weight_columns(
        [_column("color", "Color", 20, role="catalog_spec"), _column("peso_kg", "Peso", 10)]
    )
    rows = [
        {"peso": "5 kg", "color": "Naranja"},
        {"peso": "10 kg", "color": "Rojo"},
    ]
    visible = visible_variant_columns(columns, rows)
    assert [column.key for column in visible] == [SYNTHETIC_PESO_KEY, "color"]


def test_list_column_label_uppercases_peso_and_color():
    assert list_column_label(_column(SYNTHETIC_PESO_KEY, SYNTHETIC_PESO_LABEL)) == "PESO"
    assert list_column_label(_column("color", "Color", role="catalog_spec")) == "COLOR"


def test_build_variant_table_presentation_wall_ball_lbs_uses_peso_not_variante():
    columns = consolidate_weight_columns(
        [_column("peso_lb", "Peso (lbs)", 11), _column("color", "Color", 20, role="catalog_spec")]
    )
    master = SimpleNamespace(id=uuid4(), name="Wall Ball")
    variants = [
        _variant(
            "CRO083",
            [_spec_row("peso_lb", value_number=Decimal("12"), unit_symbol="lbs")],
            reference_label="12 lb",
        ),
        _variant(
            "CRO084",
            [_spec_row("peso_lb", value_number=Decimal("14"), unit_symbol="lbs")],
            reference_label="14 lb",
        ),
    ]

    presentation = build_variant_table_presentation(master, variants, columns)

    assert len(presentation.columns) == 1
    assert presentation.columns[0].key == SYNTHETIC_PESO_KEY
    assert presentation.columns[0].label == "PESO"


def test_build_variant_table_presentation_power_bags_peso_and_color():
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    master = SimpleNamespace(id=uuid4(), name="Power Bag")
    variants = [
        _variant(
            "CRO069",
            [
                _spec_row("peso_kg", value_number=Decimal("5"), unit_symbol="kg"),
                _spec_row("color", value_text="Naranja", role="catalog_spec"),
            ],
        ),
        _variant(
            "CRO070",
            [
                _spec_row("peso_kg", value_number=Decimal("10"), unit_symbol="kg"),
                _spec_row("color", value_text="Rojo", role="catalog_spec"),
            ],
        ),
        _variant("CRO143", [_spec_row("peso_kg", value_number=Decimal("30"), unit_symbol="kg")]),
    ]
    presentation = build_variant_table_presentation(master, variants, columns)
    assert [column.key for column in presentation.columns] == [SYNTHETIC_PESO_KEY, "color"]
    assert presentation.columns[0].label == "PESO"
    assert presentation.columns[1].label == "COLOR"


def test_build_variant_table_presentation_reference_label_fallback():
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    master = SimpleNamespace(id=uuid4(), name="Family")
    variants = [
        SimpleNamespace(
            id=uuid4(),
            sku="A",
            display_name="A",
            reference_label="5 kgs",
            raw_name=None,
            brand=None,
            brand_id=None,
            specs=[],
            product_master_id=master.id,
        ),
        SimpleNamespace(
            id=uuid4(),
            sku="B",
            display_name="B",
            reference_label="10 kgs",
            raw_name=None,
            brand=None,
            brand_id=None,
            specs=[],
            product_master_id=master.id,
        ),
    ]
    presentation = build_variant_table_presentation(master, variants, columns)
    assert presentation.show_variant_name_column is True
    assert any(col.key == "variant_label" for col in presentation.columns)


def test_sort_product_variants_by_weight_then_sku():
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variants = [
        _variant("CRO100", [_spec_row("peso_kg", value_number=Decimal("12"), unit_symbol="kg")]),
        _variant("CRO095", [_spec_row("peso_kg", value_number=Decimal("3"), unit_symbol="kg")]),
        _variant("CRO096", [_spec_row("peso_kg", value_number=Decimal("5"), unit_symbol="kg")]),
    ]
    sorted_variants = sort_product_variants(variants, columns)
    assert [variant.sku for variant in sorted_variants] == ["CRO095", "CRO096", "CRO100"]


def test_sort_product_variants_lbs_family():
    columns = consolidate_weight_columns([_column("peso_lb", "Peso (lbs)", 11)])
    variants = [
        _variant("CRO086", [_spec_row("peso_lb", value_number=Decimal("20"), unit_symbol="lbs")]),
        _variant("CRO083", [_spec_row("peso_lb", value_number=Decimal("12"), unit_symbol="lbs")]),
        _variant("CRO085", [_spec_row("peso_lb", value_number=Decimal("16"), unit_symbol="lbs")]),
    ]
    sorted_variants = sort_product_variants(variants, columns)
    assert [variant.sku for variant in sorted_variants] == ["CRO083", "CRO085", "CRO086"]


def test_discover_columns_from_variants_adds_missing_peso_lb():
    from app.services.spec_resolver import _discover_columns_from_variants

    columns = [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    existing_keys = {column.key for column in columns}
    variants = [
        _variant("CRO083", [_spec_row("peso_lb", value_number=Decimal("12"), unit_symbol="lbs")]),
    ]
    discovered = _discover_columns_from_variants(variants, existing_keys=existing_keys)
    assert [column.key for column in discovered] == ["peso_lb"]
    merged = consolidate_weight_columns(columns + discovered)
    assert merged[0].key == SYNTHETIC_PESO_KEY
