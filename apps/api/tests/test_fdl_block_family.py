"""Unit tests for reusable FDL block-family header rules."""

from __future__ import annotations

import pytest
from app.services.fdl_block_family import (
    is_short_semantic_block_title,
    master_key_from_block_header,
    master_key_stem_from_header,
    normalize_fdl_variant_text,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12& Negro", "12 lbs Negro"),
        ("14& Negro", "14 lbs Negro"),
        ("Wall Ball 5 kgs Negro", "Wall Ball 5 kgs Negro"),
    ],
)
def test_normalize_fdl_variant_text_ocr_lbs(raw: str, expected: str):
    assert normalize_fdl_variant_text(raw) == expected


def test_short_semantic_block_title_saco_bulgaro():
    assert is_short_semantic_block_title("Saco Bulgaro") is True
    assert is_short_semantic_block_title("Wall Ball") is False


def test_short_semantic_block_title_saco_gusano():
    assert is_short_semantic_block_title("Saco Gusano") is True


@pytest.mark.parametrize(
    ("header", "stem"),
    [
        ("Wall Balls Doble Costura Negro FDL", "WALL-FDL"),
        ("Wall Balls Doble Costura Negro NEXO", "WALL-NEXO"),
        ("Wall Balls Doble Costura Libras", "WALL-LBS"),
        ("Wall Balls Doble Costura Color kgs", "WALL-COLOR"),
        ("Power Bags Color", "POWER-BAGS-COLOR"),
        ("Saco Bulgaro", "SACO-BULGARO"),
        ("Saco Gusano", "SACO-GUSANO"),
        ("Barras Crossfit", "BARRAS-CROSSFIT"),
        ("Barras Crossfit - NEXO", "BARRAS-CROSSFIT-NEXO"),
    ],
)
def test_master_key_stem_from_header(header: str, stem: str):
    assert master_key_stem_from_header(header) == stem


def test_short_semantic_block_title_barras_crossfit():
    assert is_short_semantic_block_title("Barras Crossfit") is True


def test_block_name_token_matches_barras_requires_header():
    from app.services.fdl_block_family import block_name_token_matches

    assert (
        block_name_token_matches("Barras Crossfit", "Barra 2 Mts PLATA", "barras crossfit") is True
    )
    assert block_name_token_matches(None, "Barra 2 Mts PLATA", "barras crossfit") is False


def test_master_key_from_block_header_uses_sku_prefix():
    assert (
        master_key_from_block_header("Wall Balls Doble Costura Negro FDL", "CRO095")
        == "CRO-WALL-FDL"
    )
    assert (
        master_key_from_block_header("Wall Balls Doble Costura Color kgs", "CRO002")
        == "CRO-WALL-COLOR"
    )
    assert master_key_from_block_header("Barras Crossfit", "BOC001") == "BOC-BARRAS-CROSSFIT"
    assert (
        master_key_from_block_header("Barras Crossfit - NEXO", "BOC001NEXO")
        == "BOC-BARRAS-CROSSFIT-NEXO"
    )
