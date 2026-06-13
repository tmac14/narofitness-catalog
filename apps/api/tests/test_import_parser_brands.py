"""Parser tests for section brand detection."""

import pytest
from app.services.import_brand_resolution import (
    FALLBACK_COMMERCIAL_BRAND,
    infer_brand_from_product_text,
)
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf


def test_infer_brand_from_product_text_detects_embedded_fdl_and_nexo():
    assert infer_brand_from_product_text("Wall Ball Doble costura 3 kgs Negro FDL") == "FDL"
    assert infer_brand_from_product_text("Disco Bumper NEXO Negro - 5 kgs") == "NEXO"
    assert infer_brand_from_product_text("Disco Bumper Negro NEXO - Goma Maciza") == "NEXO"


def test_infer_brand_from_product_text_skips_sku_tokens():
    assert infer_brand_from_product_text("DOBNEXO05N") is None
    assert infer_brand_from_product_text("Disco Olimpico Premium 5 kgs") is None


def test_parser_assigns_section_brand_from_headers(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    xebex_rows = [r for r in rows if r.brand == "XEBEX"]
    reebok_rows = [r for r in rows if r.brand == "REEBOK"]
    assert len(xebex_rows) > 0
    assert len(reebok_rows) > 0

    cardio_xebex = [r for r in xebex_rows if r.category_path.startswith("CARDIO")]
    assert len(cardio_xebex) > 0


def test_parser_defaults_to_fdl_without_section_brand(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    discos = [r for r in rows if r.category_path.startswith("DISCOS Y BARRAS")]
    assert len(discos) > 0
    assert all(r.brand == FALLBACK_COMMERCIAL_BRAND for r in discos)

    assert all(r.brand for r in rows)
    assert FALLBACK_COMMERCIAL_BRAND in {r.brand for r in rows}
    assert sum(1 for r in rows if r.brand == FALLBACK_COMMERCIAL_BRAND) > 100
    fdl_branded = [r for r in rows if r.brand == "FDL"]
    for row in fdl_branded:
        context = " ".join(
            filter(None, [row.family_header_raw, row.variant_name_raw, row.raw_name, row.name])
        ).upper()
        assert "FDL" in context


def test_parser_dobnexo_rows_use_embedded_nexo_brand_from_product_name(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    dobnexo_rows = [
        r
        for r in rows
        if r.sku and r.sku.startswith("DOBNEXO") and "NEXO" in (r.raw_name or "").upper()
    ]
    if not dobnexo_rows:
        pytest.skip("DOBNEXO rows with NEXO in product name not in reference PDF")
    assert all(r.brand == "NEXO" for r in dobnexo_rows)
