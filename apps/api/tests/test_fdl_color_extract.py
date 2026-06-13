"""Tests for FDL color extraction from variant names (COLOR-1c)."""

from __future__ import annotations

import pytest
from app.services.fdl_color_extract import (
    ColorExtractContext,
    extract_color_from_name,
    extract_color_from_name_with_meta,
    is_excluded_suffix,
    normalize_color_candidate,
)


def _color_family_context() -> ColorExtractContext:
    return ColorExtractContext(
        family_header_raw="Power Bags Color",
        master_name="Power Bags Color",
        mapped_category_slug="cross-training",
        attr_from_name_has_color=True,
    )


def test_extracts_trailing_color_word_boundary():
    color, unknown = extract_color_from_name("Power Bag Color 10 kgs ROJO")
    assert color == "Rojo"
    assert unknown is None


def test_extracts_naranja_azul_verde():
    assert extract_color_from_name("Power Bag Color 5 kgs NARANJA")[0] == "Naranja"
    assert extract_color_from_name("Power Bag Color 15 kgs AZUL")[0] == "Azul"
    assert extract_color_from_name("Power Bag Color 20 kgs VERDE")[0] == "Verde"


def test_no_color_when_absent():
    color, unknown = extract_color_from_name("Power Bag Color 30 kgs")
    assert color is None
    assert unknown is None


def test_purpura_synonym_maps_to_morado():
    color, unknown = extract_color_from_name("Power Bag Color 10 kgs PURPURA")
    assert color == "Morado"
    assert unknown is None


def test_violeta_explicit_stays_violeta():
    color, unknown = extract_color_from_name("Power Bag Color 10 kgs VIOLETA")
    assert color == "Violeta"
    assert unknown is None


def test_unknown_color_generates_token_for_review():
    color, unknown = extract_color_from_name("Power Bag Color 10 kgs PETROLEO")
    assert color is None
    assert unknown == "PETROLEO"


@pytest.mark.parametrize(
    "token",
    ["NEGRA", "Negra", "negra", "negros", "negras"],
)
def test_negra_synonyms_map_to_negro(token: str):
    color, unknown = extract_color_from_name(f"Barra 2,20 Mts Agarre 28 mm {token}")
    assert color == "Negro"
    assert unknown is None


def test_dash_suffix_gris_with_color_context():
    ctx = _color_family_context()
    color, unknown, meta = extract_color_from_name_with_meta(
        "Power Bag - Gris",
        context=ctx,
    )
    assert color == "Gris"
    assert unknown is None
    assert meta is not None
    assert meta.source == "dash_suffix"
    assert meta.raw_candidate == "Gris"


def test_dash_suffix_amarillo_case_insensitive():
    ctx = ColorExtractContext(
        family_header_raw="Mancuernas",
        mapped_category_slug="mancuernas",
        attr_from_name_has_color=True,
    )
    color, unknown, meta = extract_color_from_name_with_meta(
        "Mancuerna - amarillo",
        context=ctx,
    )
    assert color == "Amarillo"
    assert unknown is None
    assert meta and meta.source == "dash_suffix"


def test_dash_suffix_azul_petroleo_unknown():
    ctx = _color_family_context()
    color, unknown, meta = extract_color_from_name_with_meta(
        "Producto X - Azul Petróleo",
        context=ctx,
    )
    assert color is None
    assert unknown == "Azul Petróleo"
    assert meta and meta.source == "dash_suffix"


def test_dash_suffix_weight_excluded():
    ctx = _color_family_context()
    color, unknown, _meta = extract_color_from_name_with_meta(
        "Producto - 10 kg",
        context=ctx,
    )
    assert color is None
    assert unknown is None
    assert is_excluded_suffix("10 kg")


def test_dash_suffix_sku_excluded():
    ctx = _color_family_context()
    color, unknown, _meta = extract_color_from_name_with_meta(
        "Producto - CRO143",
        context=ctx,
    )
    assert color is None
    assert unknown is None


def test_synonyms_marron_cafe_plateado_oro_multicolor():
    assert extract_color_from_name("Item - marron", context=_color_family_context())[0] == "Marrón"
    assert extract_color_from_name("Item - café", context=_color_family_context())[0] == "Marrón"
    assert extract_color_from_name("Item - plateado", context=_color_family_context())[0] == "Plata"
    assert extract_color_from_name("Item - oro", context=_color_family_context())[0] == "Dorado"
    assert (
        extract_color_from_name("Item - multi color", context=_color_family_context())[0]
        == "Multicolor"
    )


def test_normalize_color_candidate_collapses_and_casefolds():
    assert normalize_color_candidate("  Amarillo  ") == "amarillo"


def test_dash_negro_wall_ball():
    ctx = ColorExtractContext(
        family_header_raw="Wall Balls",
        mapped_category_slug="cross-training",
        attr_from_name_has_color=True,
    )
    color, unknown = extract_color_from_name("Wall Ball - Negro", context=ctx)
    assert color == "Negro"
    assert unknown is None
