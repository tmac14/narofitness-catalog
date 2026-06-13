"""Tests for human-readable numeric spec display."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.services.number_display import format_number_for_display
from app.services.spec_resolver import (
    SpecColumn,
    build_variant_row_spec_values,
    format_spec_display,
)


def _spec_row(*, value_number: Decimal | None = None, value_text: str | None = None):
    return SimpleNamespace(
        allowed_value_id=None,
        allowed_value=None,
        value_text=value_text,
        value_number=value_number,
        value_boolean=None,
    )


def _definition(*, unit_symbol: str | None = "kg"):
    unit = SimpleNamespace(symbol=unit_symbol) if unit_symbol else None
    return SimpleNamespace(
        key="peso_kg",
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
    unit = SimpleNamespace(symbol="kg")
    assert format_spec_display(row, _definition(), unit) == "0.5 kg"
    assert (
        format_spec_display(_spec_row(value_number=Decimal("5.0000")), _definition(), unit)
        == "5 kg"
    )
    assert (
        format_spec_display(_spec_row(value_number=Decimal("1.5000")), _definition(), unit)
        == "1.5 kg"
    )


def test_format_spec_display_without_unit():
    row = _spec_row(value_number=Decimal("0.5000"))
    assert format_spec_display(row, _definition(unit_symbol=None), None) == "0.5"


def test_format_spec_display_other_unit():
    row = _spec_row(value_number=Decimal("12.5000"))
    unit = SimpleNamespace(symbol="mm")
    assert format_spec_display(row, _definition(unit_symbol="mm"), unit) == "12.5 mm"


def test_build_variant_row_spec_values_formats_fractional_peso():
    definition_id = uuid4()
    spec_row = SimpleNamespace(
        spec_definition_id=definition_id,
        spec_definition=SimpleNamespace(
            id=definition_id,
            key="peso_kg",
            label="Peso",
            data_type="number",
            unit=SimpleNamespace(symbol="kg"),
        ),
        value_number=Decimal("0.5000"),
        allowed_value_id=None,
        allowed_value=None,
        value_text=None,
        value_boolean=None,
    )
    variant = SimpleNamespace(specs=[spec_row])
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
