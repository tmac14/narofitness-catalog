"""Unit tests for explicit_one_per_sku master name resolution."""

from __future__ import annotations

from decimal import Decimal

from app.services.import_master_naming import (
    is_valid_commercial_master_name,
    resolve_explicit_one_per_sku_master_name,
    row_canonical_display_name,
)
from app.services.import_parsers.base import ImportRow, RowStatus


def _row(
    *,
    sku: str,
    name: str,
    normalized_name: str | None = None,
    variant_primary_name_raw: str | None = None,
    family_header_raw: str | None = None,
) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        normalized_name=normalized_name or name,
        brand="XEBEX",
        ean=None,
        category_path="CARDIO > CINTA",
        price_amount=Decimal("100.00"),
        variant_primary_name_raw=variant_primary_name_raw,
        variant_name_raw=variant_primary_name_raw,
        raw_name=variant_primary_name_raw or name,
        taxonomy_name=variant_primary_name_raw or name,
        family_header_raw=family_header_raw,
    )


def test_prefers_normalized_over_variant_primary_raw():
    row = _row(
        sku="CIN003",
        name="ST-6000",
        normalized_name="ST-6000",
        variant_primary_name_raw="Cinta Xebex ST-6000",
    )
    master_name, audit_reason = resolve_explicit_one_per_sku_master_name(row)
    assert master_name == "ST-6000"
    assert audit_reason is None
    assert "Xebex" not in master_name


def test_remo_prefix_removed_via_normalized_display():
    row = _row(
        sku="REM002",
        name="Air Rower 2,0 (NO smart conect)",
        normalized_name="Air Rower 2,0 (NO smart conect)",
        variant_primary_name_raw="Remo Air Rower 2,0 (NO smart conect)",
    )
    master_name, _ = resolve_explicit_one_per_sku_master_name(row)
    assert master_name == "Air Rower 2,0 (NO smart conect)"
    assert not master_name.lower().startswith("remo ")


def test_repuesto_leading_brand_stripped_in_normalized():
    row = _row(
        sku="REPUESTO-805",
        name="Consola Bluetooth AB-1 SMART CONECT",
        normalized_name="Consola Bluetooth AB-1 SMART CONECT",
        variant_primary_name_raw="XEBEX Consola Bluetooth AB-1 SMART CONECT",
    )
    master_name, _ = resolve_explicit_one_per_sku_master_name(row)
    assert master_name == "Consola Bluetooth AB-1 SMART CONECT"
    assert "XEBEX" not in master_name.upper()


def test_fallback_header_when_display_invalid():
    row = _row(
        sku="DOBMINI",
        name="Ab",
        normalized_name="Ab",
        family_header_raw="Disco Olimpico Bumper Mini",
    )
    master_name, audit_reason = resolve_explicit_one_per_sku_master_name(row)
    assert master_name == "Disco Olimpico Bumper Mini"
    assert audit_reason == "master_name_from_header"


def test_fallback_sku_when_display_and_header_invalid():
    row = _row(
        sku="FOO123",
        name="Ab",
        normalized_name="Ab",
        family_header_raw=None,
    )
    master_name, audit_reason = resolve_explicit_one_per_sku_master_name(row)
    assert master_name == "FOO123"
    assert audit_reason == "master_name_from_sku"


def test_empty_when_no_display_header_or_sku():
    row = ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=None,
        name="",
        normalized_name="",
        brand=None,
        ean=None,
        category_path="CARDIO > BICI",
        price_amount=Decimal("1.00"),
        variant_primary_name_raw="Bicicleta Air Bike Xebex (NO smart conect)",
    )
    master_name, audit_reason = resolve_explicit_one_per_sku_master_name(row)
    assert master_name == ""
    assert audit_reason is None


def test_is_valid_commercial_master_name_rejects_sku_echo():
    assert not is_valid_commercial_master_name("CIN003", sku="CIN003")
    assert is_valid_commercial_master_name("ST-6000", sku="CIN003")


def test_row_canonical_display_name_prefers_normalized():
    row = _row(
        sku="BIC002",
        name="Bicicleta Air Bike (NO smart conect)",
        normalized_name="Bicicleta Air Bike (NO smart conect)",
        variant_primary_name_raw="Bicicleta Air Bike Xebex (NO smart conect)",
    )
    assert row_canonical_display_name(row) == "Bicicleta Air Bike (NO smart conect)"
