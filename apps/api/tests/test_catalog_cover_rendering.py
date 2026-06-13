"""HTML rendering tests for catalogue and category cover pages (supplier_table shell)."""

from __future__ import annotations

from app.services.pdf_export import render_catalog_html
from test_family_variant_table_layout import (
    _section_with_brand_groups,
    _single_block,
    _variant_block,
)


def _supplier_context(**overrides):

    products = [_variant_block()]

    base = {
        "catalog_name": "QA Cover Catalog",
        "generated_at": "08/06/2026 12:00",
        "iva_disclaimer": "Precios sin IVA",
        "catalog_shell": "supplier_table",
        "supplier_table_show_ean": True,
        "supplier_price_column_label": "P.V.P.",
        "show_iva_column": False,
        "show_description_column": True,
        "iva_rate_percent": "21",
        "logo_url": "http://127.0.0.1:8000/api/v1/media/logo.png",
        "catalog_cover_image_url": None,
        "catalog_cover_subtitle": None,
        "catalog_render_density": "screen",
        "sections": [
            _section_with_brand_groups(
                "CARDIO",
                products,
                category_id="550e8400-e29b-41d4-a716-446655440000",
                product_count=1,
            )
        ],
    }

    base.update(overrides)

    return base


def _image_cover_html(**overrides):

    return render_catalog_html(
        _supplier_context(
            catalog_cover_image_url="http://127.0.0.1:8000/api/v1/media/images/catalogs/cover.jpg",
            **overrides,
        )
    )


def test_catalog_cover_image_renders_full_bleed_when_url_present():

    html = _image_cover_html()

    assert (
        'class="catalog-page catalog-page--cover catalog-page--cover-has-image catalog-page--cover-full-bleed"'
        in html
    )

    assert 'class="catalog-cover-full-bleed-image"' in html

    assert "images/catalogs/cover.jpg" in html

    assert 'catalog-page--cover-classic"' not in html


def test_catalog_cover_image_has_no_overlay_title_or_date():

    html = _image_cover_html(catalog_cover_subtitle="Edición profesional 2026")

    assert "catalog-cover-hero-overlay" not in html

    assert 'class="catalog-cover-hero"' not in html

    assert '<h1 class="catalog-cover-title"' not in html

    assert '<p class="catalog-cover-date"' not in html

    assert '<p class="catalog-cover-subtitle"' not in html

    assert 'class="catalog-cover-logo"' not in html

    assert ">QA Cover Catalog<" not in html.split("</title>", 1)[-1]

    assert ">08/06/2026 12:00<" not in html

    assert ">Edición profesional 2026<" not in html


def test_catalog_cover_image_includes_cover_full_page_css():

    html = _image_cover_html()

    assert "@page cover-full" in html

    assert "page: cover-full" in html

    assert "margin: 0" in html


def test_catalog_cover_image_print_density_uses_full_bleed():

    html = _image_cover_html(catalog_render_density="print")

    assert "catalog-page--cover-full-bleed" in html

    assert "catalogue-pdf-render" in html


def test_catalog_cover_subtitle_renders_on_classic_layout_only():

    html = render_catalog_html(
        _supplier_context(
            catalog_cover_subtitle="Edición profesional 2026",
        )
    )

    assert "Edición profesional 2026" in html

    assert "catalog-cover-subtitle" in html


def test_catalog_cover_without_image_uses_classic_layout_no_broken_img():

    html = render_catalog_html(_supplier_context())

    assert 'class="catalog-page catalog-page--cover catalog-page--cover-classic"' in html

    assert 'class="catalog-cover-full-bleed-image"' not in html

    assert 'class="catalog-cover-classic"' in html

    assert "QA Cover Catalog" in html

    assert "logo.png" in html

    assert "08/06/2026 12:00" in html


def test_category_cover_page_renders_with_image():

    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "CARDIO",
                    [_single_block()],
                    category_id="550e8400-e29b-41d4-a716-446655440001",
                    product_count=1,
                    category_cover_image_url="http://127.0.0.1:8000/api/v1/media/images/catalogs/section.jpg",
                )
            ],
        )
    )

    assert 'class="catalog-page catalog-page--category-cover"' in html

    assert 'class="category-cover-image"' in html

    assert "images/catalogs/section.jpg" in html

    assert "supplier-section-header--compact" in html


def test_category_cover_description_renders_without_image():

    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "FUERZA",
                    [_single_block()],
                    category_id="550e8400-e29b-41d4-a716-446655440002",
                    product_count=1,
                    category_cover_description="Equipamiento de fuerza y musculación.",
                )
            ],
        )
    )

    assert 'class="catalog-page catalog-page--category-cover"' in html

    assert "Equipamiento de fuerza y musculación." in html

    assert "category-cover-description" in html

    assert "category-cover-image-wrap--fallback" in html

    assert 'class="category-cover-image"' not in html


def test_category_cover_product_count_renders():

    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "CARDIO",
                    [_single_block(), _variant_block()],
                    category_id="550e8400-e29b-41d4-a716-446655440003",
                    product_count=2,
                    category_cover_description="Sección cardio",
                )
            ],
        )
    )

    assert "2 productos" in html

    assert "category-cover-count" in html


def test_no_category_cover_page_without_image_or_description():

    html = render_catalog_html(_supplier_context())

    assert 'class="catalog-page catalog-page--category-cover"' not in html

    assert "supplier-section-header supplier-section-header--compact" not in html

    assert 'class="supplier-section-header">' in html


def test_general_section_without_category_id_renders_normally():

    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [_single_block()],
                    category_id=None,
                    product_count=1,
                )
            ],
        )
    )

    assert 'class="catalog-page catalog-page--category-cover"' not in html

    assert "General" in html

    assert "supplier-simple-block" in html


def test_catalog_and_category_covers_use_page_break_classes():

    html = render_catalog_html(
        _supplier_context(
            catalog_cover_image_url="http://127.0.0.1:8000/api/v1/media/cover.jpg",
            sections=[
                _section_with_brand_groups(
                    "CARDIO",
                    [_single_block()],
                    category_id="550e8400-e29b-41d4-a716-446655440004",
                    product_count=1,
                    category_cover_image_url="http://127.0.0.1:8000/api/v1/media/section.jpg",
                    category_cover_description="Cardio line",
                )
            ],
        )
    )

    assert "catalog-page--cover-full-bleed" in html

    assert 'class="catalog-page catalog-page--category-cover"' in html

    assert 'class="catalog-wrap catalog-page--products"' in html
