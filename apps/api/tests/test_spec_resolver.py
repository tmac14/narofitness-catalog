"""Tests for human-readable numeric spec display."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.services.number_display import format_number_for_display
from app.services.spec_resolver import (
    SpecColumn,
    build_variant_row_spec_values,
    format_spec_display,
)
from tests.model_test_factories import (
    make_product_variant,
    make_spec_definition,
    make_unit,
    make_variant_spec,
)


def _spec_row(*, value_number: Decimal | None = None, value_text: str | None = None):
    definition = make_spec_definition("peso_kg", label="Peso", data_type="number")
    return make_variant_spec(
        definition,
        value_number=value_number,
        value_text=value_text,
    )


def _definition(*, unit_symbol: str | None = "kg"):
    unit = make_unit(symbol=unit_symbol) if unit_symbol else None
    return make_spec_definition(
        "peso_kg",
        label="Peso",
        data_type="number",
        unit=unit,
    )


def test_format_number_for_display_integers():
    assert format_number_for_display(Decimal("5.0000")) == "5"
    assert format_number_for_display(Decimal("25.0000")) == "25"


def test_format_number_for_display_fractions():
    assert format_number_for_display(Decimal("0.5000")) == "0.5"
    assert format_number_for_display(Decimal("1.5000")) == "1.5"
    assert format_number_for_display(Decimal("0.2500")) == "0.25"
    assert format_number_for_display(0.5) == "0.5"


def test_format_spec_display_with_kg_unit():
    row = _spec_row(value_number=Decimal("0.5000"))
    unit = make_unit(symbol="kg")
    definition = _definition()
    assert format_spec_display(row, definition, unit) == "0.5 kg"
    assert (
        format_spec_display(_spec_row(value_number=Decimal("5.0000")), _definition(), unit)
        == "5 kg"
    )
    assert (
        format_spec_display(_spec_row(value_number=Decimal("1.5000")), _definition(), unit)
        == "1.5 kg"
    )


def test_format_spec_display_without_unit():
    row = make_variant_spec(
        make_spec_definition("capacidad_balones", label="Capacidad", data_type="number"),
        value_number=Decimal("0.5000"),
    )
    definition = make_spec_definition(
        "capacidad_balones",
        label="Capacidad",
        data_type="number",
        unit=None,
    )
    assert format_spec_display(row, definition, None) == "0.5"


def test_format_spec_display_other_unit():
    row = make_variant_spec(
        make_spec_definition("longitud_mm", label="Longitud", data_type="number"),
        value_number=Decimal("12.5000"),
    )
    unit = make_unit(symbol="mm")
    definition = make_spec_definition(
        "longitud_mm",
        label="Longitud",
        data_type="number",
        unit=unit,
    )
    assert format_spec_display(row, definition, unit) == "12.5 mm"


def test_build_variant_row_spec_values_formats_fractional_peso():
    definition_id = uuid4()
    peso_unit = make_unit(symbol="kg")
    definition = make_spec_definition(
        "peso_kg",
        label="Peso",
        data_type="number",
        unit=peso_unit,
        definition_id=definition_id,
    )
    spec_row = make_variant_spec(definition, value_number=Decimal("0.5000"))
    variant = make_product_variant("TEST-SKU", specs=[spec_row])
    columns = [
        SpecColumn(
            key="peso_kg",
            label="Peso",
            sort_order=0,
            spec_definition_id=definition_id,
            data_type="number",
            role="variant_axis",
        )
    ]
    values = build_variant_row_spec_values(variant, columns)
    assert values["peso_kg"] == "0.5 kg"
