"""PDF export HTML rendering and engine integration."""

from datetime import datetime
from pathlib import Path

import pytest
from app.services.app_assets import resolve_placeholder_url
from app.services.pdf_export import (
    PdfEngineError,
    _preview_url,
    export_catalog_pdf,
    pdf_engine_status,
    render_catalog_html,
    require_pdf_engine,
)

_engine, _engine_error = pdf_engine_status()
_requires_pdf_engine = pytest.mark.skipif(
    not _engine,
    reason=_engine_error or "Ningún motor PDF disponible en este entorno",
)


def _with_placeholder(block: dict) -> dict:
    if block.get("image_url") is None and block.get("placeholder_url") is None:
        layout_id = block.get("layout_id", "single_standard")
        block = {
            **block,
            "placeholder_url": resolve_placeholder_url(
                layout_id,
                for_html=True,
                api_base="http://127.0.0.1:8000",
            ),
        }
    return block


def _single_product_block(**overrides):
    base = {
        "master_name": "Esterilla yoga",
        "subtitle": None,
        "brand": None,
        "image_url": None,
        "has_variants": False,
        "variant_attribute_count": 0,
        "variant_columns": [],
        "layout_id": "single_standard",
        "variants": [
            {
                "sku": "MAT-01",
                "price_display": "19,00 €",
                "price_iva_display": "22,99 €",
            }
        ],
        "sku": "MAT-01",
        "price_display": "19,00 €",
        "price_iva_display": "22,99 €",
    }
    base.update(overrides)
    return _with_placeholder(base)


def _variant_product_block(**overrides):
    base = {
        "master_name": "Kettlebell",
        "title_line1": "Kettlebell",
        "title_line2": "Competition",
        "subtitle": "Competition",
        "brand": None,
        "image_url": None,
        "has_variants": True,
        "variant_attribute_count": 2,
        "variant_columns": [
            {"key": "peso_kg", "label": "Peso"},
            {"key": "color", "label": "Color"},
        ],
        "layout_id": "variant_row_wide",
        "variants": [
            {
                "sku": "NRO-K08",
                "peso_kg": "8 kg",
                "color": "Rosa",
                "price_display": "25,00 €",
                "price_iva_display": "30,25 €",
            },
            {
                "sku": "NRO-K12",
                "peso_kg": "12 kg",
                "color": "Azul",
                "price_display": "35,00 €",
                "price_iva_display": "42,35 €",
            },
        ],
        "sku": "NRO-K08",
        "price_display": "25,00 €",
        "price_iva_display": "30,25 €",
    }
    base.update(overrides)
    return _with_placeholder(base)


@_requires_pdf_engine
def test_pdf_engine_ready():
    engine, error = pdf_engine_status()
    assert engine in ("playwright", "weasyprint"), error
    require_pdf_engine()


def test_render_catalog_html_minimal():
    html = render_catalog_html(
        {
            "catalog_name": "Test",
            "generated_at": datetime.now().strftime("%d/%m/%Y"),
            "iva_disclaimer": "Sin IVA",
            "sections": [],
            "categories": [],
        }
    )
    assert "Test" in html
    assert "<html" in html.lower()


def test_render_catalog_html_with_variant_table():
    html = render_catalog_html(
        {
            "catalog_name": "Test",
            "generated_at": "01/01/2026",
            "iva_disclaimer": "Sin IVA",
            "catalog_template": "branded",
            "show_iva_column": True,
            "iva_rate_percent": "21",
            "sections": [
                {
                    "name": "Pesas",
                    "products": [_variant_product_block()],
                }
            ],
            "categories": [
                {
                    "name": "Pesas",
                    "products": [_variant_product_block()],
                }
            ],
        }
    )
    assert "variant-table" in html
    assert "Peso" in html
    assert "Precio" in html
    assert "NRO-K08" in html
    assert "8 kg" in html
    assert "Competition" in html
    assert "product-block__layout" in html
    assert "product-block__title-line1" in html
    assert "product-block__title-line2" in html
    assert "product-block__image--placeholder" in html
    assert "product_placeholder_aspect_ratio_16_9.png" in html
    assert 'class="product-block product-block--variants product-block--row-wide"' in html
    assert 'data-layout="variant_row_wide"' in html
    assert "product-block__layout--row-wide" in html
    assert "product-block__left" in html
    assert "product-block__right" in html


def test_render_catalog_html_single_attribute_variant_grid():
    html = render_catalog_html(
        {
            "catalog_name": "Test",
            "generated_at": "01/01/2026",
            "iva_disclaimer": "Sin IVA",
            "catalog_template": "branded",
            "show_iva_column": False,
            "iva_rate_percent": "21",
            "sections": [
                {
                    "name": "Discos",
                    "products": [
                        _variant_product_block(
                            master_name="Disco bumper",
                            title_line1="Disco bumper",
                            title_line2="Competition",
                            variant_attribute_count=1,
                            layout_id="variant_grid_50_50",
                            variant_columns=[{"key": "peso_kg", "label": "Peso"}],
                            variants=[
                                {
                                    "sku": "BP-10",
                                    "peso_kg": "10 kg",
                                    "price_display": "45,00 €",
                                    "price_iva_display": None,
                                },
                                {
                                    "sku": "BP-15",
                                    "peso_kg": "15 kg",
                                    "price_display": "55,00 €",
                                    "price_iva_display": None,
                                },
                            ],
                        )
                    ],
                }
            ],
            "categories": [],
        }
    )
    assert 'data-layout="variant_grid_50_50"' in html
    assert "product-block--grid-50-50" in html
    assert "product-block__col-media" in html
    assert "product-block__col-info" in html
    assert "10 kg" in html
    assert "product_placeholder_aspect_ratio_1_1.png" in html


def test_render_catalog_html_single_variant():
    html = render_catalog_html(
        {
            "catalog_name": "Test",
            "generated_at": "01/01/2026",
            "iva_disclaimer": "Sin IVA",
            "catalog_template": "default",
            "show_iva_column": False,
            "iva_rate_percent": "21",
            "sections": [],
            "categories": [
                {
                    "name": "Accesorios",
                    "products": [_single_product_block()],
                }
            ],
        }
    )
    assert "product-block--single" in html
    assert "MAT-01" in html
    assert "19,00 €" in html
    assert "variant-table--single" in html
    assert "product-block__image--placeholder" in html
    assert "product_placeholder_aspect_ratio_4_3.png" in html


@_requires_pdf_engine
def test_export_catalog_pdf_writes_file(tmp_path: Path):
    out = tmp_path / "out.pdf"
    engine, data = export_catalog_pdf(
        {
            "catalog_name": "Export test",
            "generated_at": "01/01/2026",
            "iva_disclaimer": "Leyenda IVA",
            "catalog_template": "branded",
            "show_iva_column": False,
            "iva_rate_percent": "21",
            "categories": [
                {
                    "name": "Demo",
                    "products": [_single_product_block()],
                }
            ],
        },
        out,
    )
    assert engine in ("playwright", "weasyprint")
    assert len(data) > 500
    assert out.is_file()
    assert out.read_bytes()[:4] == b"%PDF"


def test_preview_url_includes_render_density_print():
    url = _preview_url(
        {
            "catalog_id": "65096ef9-cb58-4026-b998-c557bf3bd007",
            "api_base": "http://127.0.0.1:8000",
        }
    )
    assert url is not None
    assert "render_density=print" in url


def test_require_pdf_engine_raises_when_unavailable(monkeypatch):
    def _fail():
        raise PdfEngineError("simulated failure")

    monkeypatch.setattr("app.services.pdf_export.resolve_pdf_export_engine", _fail)
    with pytest.raises(PdfEngineError, match="simulated"):
        require_pdf_engine()
