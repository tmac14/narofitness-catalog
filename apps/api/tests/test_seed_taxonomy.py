"""Tests for taxonomy seed helpers."""

from pathlib import Path

import pytest
from app.services.seed_brands import extract_brands_from_pdf
from app.services.seed_category_defaults import DEFAULT_CATEGORY_ROWS
from app.services.text_utils import brand_slug, normalize_brand_name, slugify


def test_slugify_preserves_csv_slugs():
    assert slugify("Bancos, jaulas y soportes") == "bancos-jaulas-y-soportes"
    assert slugify("Linea convergente a disco") == "linea-convergente-a-disco"
    assert slugify("Cross Training") == "cross-training"


def test_brand_normalization():
    assert normalize_brand_name("  xebex ") == "XEBEX"
    assert brand_slug("Reebok") == "reebok"


def test_default_category_rows_parent_and_sub_slugs():
    parent_slugs = {row.parent_slug for row in DEFAULT_CATEGORY_ROWS}
    assert parent_slugs == {
        "agarres",
        "barras",
        "boxeo",
        "cardio",
        "cross-training",
        "discos",
        "home",
        "mancuernas",
        "material-de-estudio",
        "musculacion",
        "racks-y-estructuras",
        "repuestos",
        "soportes-y-mancuerneros",
        "suelos",
    }
    sub_slugs = {row.subcategory_slug for row in DEFAULT_CATEGORY_ROWS if row.subcategory_slug}
    assert len(sub_slugs) == 10


def test_extract_brands_from_reference_pdf(reference_pdf: Path | None):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    brands = extract_brands_from_pdf(reference_pdf)
    assert brands == ["ADIDAS", "FDL", "HORIZON", "NEXO", "REEBOK", "XEBEX"]
