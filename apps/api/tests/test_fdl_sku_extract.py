"""Unit tests for FDL embedded/trailing SKU extraction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.services.fdl_sku_extract import (
    extract_sku_from_buffer_lines,
    extract_trailing_sku,
    is_bom_component_line,
    is_fdl_sku_token,
    strip_composite_bom_description,
)

FIXTURES = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "fdl_embedded_sku_samples.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("token", FIXTURES["positive_tokens"])
def test_is_fdl_sku_token_positive(token: str):
    assert is_fdl_sku_token(token)


@pytest.mark.parametrize("token", FIXTURES["negative_tokens"])
def test_is_fdl_sku_token_negative(token: str):
    assert not is_fdl_sku_token(token)


@pytest.mark.parametrize("sample", FIXTURES["trailing_samples"])
def test_extract_trailing_sku_samples(sample: dict):
    remainder, sku = extract_trailing_sku(sample["raw_line"])
    assert sku == sample["expected_sku"]
    assert remainder.startswith(sample["expected_remainder_prefix"])


def test_extract_trailing_sku_bom_line_unchanged():
    line = "- PK001 X 6Uds (Columna 2,70)"
    remainder, sku = extract_trailing_sku(line)
    assert sku is None
    assert remainder == line


def test_is_bom_component_line():
    assert is_bom_component_line("- PK003 X 2Uds (Union doble 1,10)")
    assert not is_bom_component_line("JAULA CENTRAL FDRig-3")


def test_strip_composite_bom_description():
    raw = "JAULA CENTRAL - 3 Mts Compuesto de las referencias : - PK001 X 6Uds FDRig-3"
    assert strip_composite_bom_description(raw) == "JAULA CENTRAL - 3 Mts"


def test_extract_sku_from_buffer_lines_bottom_up():
    lines = [
        "JAULA CENTRAL - 3 Mts",
        "Compuesto de las referencias:",
        "- PK001 X 6Uds (Columna 2,70)",
        "- PK022 x 2Ud (J-cups) FDRig-3",
    ]
    sku, cleaned = extract_sku_from_buffer_lines(lines)
    assert sku == "FDRIG-3"
    assert cleaned[-1] == "- PK022 x 2Ud (J-cups)"
    assert "FDRig-3" not in cleaned[-1]
