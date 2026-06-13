"""Unit tests for spec_writer validation helpers."""

from decimal import Decimal
from uuid import uuid4

from app.models import SpecAllowedValue, SpecDefinition
from app.services.spec_writer import (
    SOFT_FAIL_ENUM_SPEC_KEYS,
    SpecWriteResult,
    _is_soft_enum_failure,
    _unknown_color_warning,
    _validate_value,
)


def _spec(data_type: str, scope: str = "variant") -> SpecDefinition:
    spec = SpecDefinition(
        id=uuid4(),
        key="test",
        label="Test",
        data_type=data_type,
        scope=scope,
        role="technical_spec",
    )
    if data_type == "enum":
        spec.allowed_values = [
            SpecAllowedValue(
                id=uuid4(),
                spec_definition_id=spec.id,
                value_key="negro",
                label="Negro",
            )
        ]
    return spec


def test_validate_number():
    payload, err = _validate_value(_spec("number"), 25)
    assert err is None
    assert payload is not None
    assert payload["value_number"] == Decimal("25")


def test_validate_text():
    payload, err = _validate_value(_spec("text", "master"), "Acero")
    assert err is None
    assert payload is not None
    assert payload["value_text"] == "Acero"


def test_validate_enum_by_label():
    payload, err = _validate_value(_spec("enum", "both"), "Negro")
    assert err is None
    assert payload is not None
    assert payload["allowed_value_id"] is not None


def test_reject_unknown_enum():
    payload, err = _validate_value(_spec("enum", "both"), "Magenta")
    assert payload is None
    assert err is not None
    assert "unknown enum" in err


def test_soft_enum_failure_only_for_color():
    color_spec = SpecDefinition(
        id=uuid4(),
        key="color",
        label="Color",
        data_type="enum",
        scope="both",
        role="catalog_spec",
    )
    assert _is_soft_enum_failure(color_spec, "unknown enum value 'X' for spec 'color'")
    acabado = SpecDefinition(
        id=uuid4(),
        key="acabado",
        label="Acabado",
        data_type="enum",
        scope="both",
        role="catalog_spec",
    )
    assert not _is_soft_enum_failure(acabado, "unknown enum value 'X' for spec 'acabado'")
    assert "color" in SOFT_FAIL_ENUM_SPEC_KEYS


def test_unknown_color_warning_format():
    assert _unknown_color_warning("Azul Petróleo") == "unknown_color_value:Azul Petróleo"
    assert _unknown_color_warning("") is None
    assert _unknown_color_warning(None) is None


def test_spec_write_result_has_warnings_field():
    result = SpecWriteResult()
    assert result.warnings == []


def test_unknown_color_review_reason_is_not_blocking():
    from app.services.import_review import is_blocking_reason

    assert not is_blocking_reason("unknown_color_value:Azul Petróleo")
    assert is_blocking_reason("spec_validation_failed")
