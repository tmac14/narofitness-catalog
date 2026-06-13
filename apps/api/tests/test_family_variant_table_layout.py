"""HTML rendering tests for family_variant_table supplier shell."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.services.app_assets import resolve_placeholder_url
from app.services.catalog_builder import group_products_by_brand
from app.services.pdf_export import render_catalog_html

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "app" / "pdf" / "templates"


def _variant_block(**overrides):
    base = {
        "master_id": "m1",
        "master_name": "Disco Olímpico Bumper",
        "family_title": "Disco Olímpico Bumper Color Fraccional",
        "family_subtitle": None,
        "title_line1": "Disco Olímpico Bumper Color Fraccional",
        "title_line2": None,
        "brand": "NEXO",
        "brand_display": "NEXO",
        "brand_mode": "uniform",
        "show_brand_column": False,
        "show_variant_name_column": False,
        "image_url": None,
        "placeholder_url": resolve_placeholder_url(
            "family_variant_table", for_html=True, api_base="http://127.0.0.1:8000"
        ),
        "has_variants": True,
        "layout_id": "family_variant_table",
        "variant_columns": [
            {"key": "peso_kg", "label": "Peso"},
            {"key": "color", "label": "Color"},
        ],
        "variants": [
            {
                "sku": "DISC-5",
                "ean": "8436578451234",
                "peso_kg": "5 kg",
                "color": "Rojo",
                "price_display": "45,00 €",
                "price_iva_display": "54,45 €",
            },
            {
                "sku": "DISC-10",
                "ean": None,
                "peso_kg": "10 kg",
                "color": "Azul",
                "price_display": "65,00 €",
                "price_iva_display": "78,65 €",
            },
        ],
    }
    base.update(overrides)
    return base


def _single_block(**overrides):
    base = {
        "has_variants": False,
        "variant_columns": [],
        "master_highlights": [{"label": "Material", "value": "PVC"}],
        "description_lines": ["Esterilla antideslizante de alta densidad."],
        "brand": "NaroFit",
        "variants": [
            {
                "sku": "MAT-01",
                "ean": None,
                "price_display": "19,00 €",
                "price_iva_display": "22,99 €",
            }
        ],
    }
    base.update(overrides)
    if "brand_display" not in overrides:
        base["brand_display"] = overrides.get("brand", base.get("brand"))
    return _variant_block(**base)


def _section_with_brand_groups(name: str, products: list[dict], **section_fields) -> dict:
    return {
        "name": name,
        "category_id": None,
        "product_count": len(products),
        "category_cover_image_url": None,
        "category_cover_description": None,
        "products": products,
        "brand_groups": group_products_by_brand(products),
        **section_fields,
    }


def _supplier_context(**overrides):
    products = [_variant_block()]
    base = {
        "catalog_name": "QA Table Catalog",
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "iva_disclaimer": "Precios sin IVA",
        "catalog_shell": "supplier_table",
        "supplier_table_show_ean": True,
        "supplier_price_column_label": "P.V.P.",
        "show_iva_column": False,
        "show_description_column": True,
        "iva_rate_percent": "21",
        "logo_url": None,
        "catalog_cover_image_url": None,
        "catalog_cover_subtitle": None,
        "catalog_render_density": "screen",
        "sections": [
            _section_with_brand_groups(
                "CROSSTRAINING Y ENTRENAMIENTO FUNCIONAL",
                products,
            )
        ],
    }
    base.update(overrides)
    return base


def test_supplier_table_renders_red_section_header():
    html = render_catalog_html(_supplier_context())
    assert 'class="supplier-section-header"' in html
    assert "CROSSTRAINING Y ENTRENAMIENTO FUNCIONAL" in html
    assert 'colspan="99"' not in html


def test_supplier_table_renders_brand_header_and_groups_products():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "BICICLETAS ESTÁTICAS",
                    [
                        _single_block(
                            family_title="Bike A",
                            brand="XEBEX",
                            variants=[{"sku": "X-1", "ean": "111", "price_display": "100 €"}],
                        ),
                        _single_block(
                            family_title="Bike B",
                            brand="XEBEX",
                            variants=[{"sku": "X-2", "ean": "222", "price_display": "200 €"}],
                        ),
                        _single_block(
                            family_title="Generic bike",
                            brand=None,
                            variants=[{"sku": "G-1", "ean": None, "price_display": "50 €"}],
                        ),
                    ],
                )
            ],
        )
    )
    assert 'class="supplier-brand-header"' in html
    assert ">XEBEX<" in html
    assert ">Sin marca<" in html
    assert html.index("XEBEX") < html.index("Bike A")
    assert html.index("Bike A") < html.index("Bike B")
    assert html.index("Sin marca") < html.index("Generic bike")


def test_supplier_table_renders_grey_family_header_and_variant_rows():
    html = render_catalog_html(_supplier_context())
    assert "supplier-family-variant-block" in html
    assert "supplier-catalog-table--family" in html
    assert "supplier-family-header" in html
    assert "Disco Olímpico Bumper Color Fraccional" in html
    assert "DISC-5" in html
    assert "DISC-10" in html
    assert "5 kg" in html
    assert "8436578451234" in html


def test_supplier_table_family_image_rowspan_last_column():
    html = render_catalog_html(_supplier_context())
    assert 'rowspan="2"' in html
    assert "supplier-col-header-image" in html
    assert ">Imagen<" not in html
    assert html.rindex('rowspan="2"') < html.rindex("product_placeholder_aspect_ratio_4_3.png")


def test_supplier_table_simple_product_uses_class_based_colgroup():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups("General", [_single_block()]),
            ],
        )
    )
    assert '<col class="col-image" />' in html
    assert '<col class="col-sku" />' in html
    assert '<col class="col-ean" />' in html
    assert '<col class="col-price" />' in html
    assert '<col class="col-desc" />' in html
    assert "--pdf-font-category: 8.5pt" in html


def test_supplier_table_simple_product_uses_column_layout():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _single_block(
                            family_title="Esterilla yoga",
                            title_line1="Esterilla yoga",
                            master_name="Esterilla yoga",
                        )
                    ],
                )
            ],
        )
    )
    assert "Esterilla yoga" in html
    assert "supplier-simple-block" in html
    assert "supplier-simple-col-header" in html
    assert "supplier-catalog-table--simple" in html
    assert ">SKU<" in html
    assert ">EAN<" in html
    assert ">P.V.P.<" in html
    assert ">Descripción<" in html
    assert "MAT-01" in html
    assert "Material: PVC" in html
    assert "supplier-family-variant-block" not in html


def test_supplier_table_ean_column_always_present_even_without_data():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _variant_block(
                            variants=[
                                {
                                    "sku": "A",
                                    "ean": None,
                                    "peso_kg": "1",
                                    "color": "X",
                                    "price_display": "1 €",
                                }
                            ]
                        )
                    ],
                )
            ],
        )
    )
    assert ">EAN<" in html
    assert html.count(">—<") >= 1


def test_supplier_table_mixed_simple_and_family_in_section():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "Mixed",
                    [
                        _single_block(family_title="Simple SKU", brand="NaroFit"),
                        _variant_block(family_title="Family SKU", brand="NEXO"),
                    ],
                )
            ],
        )
    )
    assert html.count('class="supplier-catalog-table supplier-catalog-table--simple') == 1
    assert html.count('class="supplier-catalog-table supplier-catalog-table--family') == 1
    assert "Simple SKU" in html
    assert "Family SKU" in html


def test_supplier_product_header_omits_redundant_brand_subtitle():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _single_block(
                            family_title="Bicicleta estática",
                            title_line1="Bicicleta estática",
                            title_line2="XEBEX",
                            family_subtitle="XEBEX",
                            brand="XEBEX",
                        )
                    ],
                )
            ],
        )
    )
    assert ">XEBEX<" in html
    assert "Bicicleta estática — XEBEX" not in html
    assert "supplier-family-header" in html


def test_supplier_product_header_keeps_non_brand_subtitle():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _single_block(
                            family_title="Disco bumper",
                            title_line1="Disco bumper",
                            title_line2="Goma maciza",
                            family_subtitle="Goma maciza",
                            brand="NEXO",
                        )
                    ],
                )
            ],
        )
    )
    assert "Disco bumper" in html
    assert "Goma maciza" in html
    assert "supplier-family-subtitle" in html


def test_supplier_table_print_density_scope_on_body():
    html = render_catalog_html(
        _supplier_context(catalog_render_density="print"),
    )
    assert 'class="catalogue-pdf-render"' in html


def test_supplier_table_screen_density_has_no_print_root_class():
    html = render_catalog_html(_supplier_context(catalog_render_density="screen"))
    assert 'class="catalogue-pdf-render"' not in html
    assert "<body>" in html or '<body class="' not in html


def test_supplier_table_print_css_no_sku_ellipsis():
    css = (TEMPLATES_DIR / "_supplier_table_print.css").read_text(encoding="utf-8")
    assert ".catalogue-pdf-render" in css
    assert "overflow: visible" in css
    assert "supplier-simple-ref-cell" in css
    assert "text-overflow: ellipsis" not in css


def test_supplier_table_print_context_renders_long_sku():
    html = render_catalog_html(
        _supplier_context(
            catalog_render_density="print",
            sections=[
                _section_with_brand_groups(
                    "CARDIO",
                    [
                        _single_block(
                            family_title="Repuesto",
                            variants=[
                                {
                                    "sku": "REPUESTO-806",
                                    "ean": None,
                                    "price_display": "12,00 €",
                                }
                            ],
                        )
                    ],
                )
            ],
        )
    )
    assert "REPUESTO-806" in html
    assert 'class="catalogue-pdf-render"' in html


def test_supplier_table_show_description_column_true_renders_description_header_and_cells():
    html = render_catalog_html(
        _supplier_context(
            show_description_column=True,
            sections=[_section_with_brand_groups("General", [_single_block()])],
        )
    )
    assert ">Descripción<" in html
    assert '<col class="col-desc" />' in html
    assert "supplier-simple-info-cell" in html
    assert "Esterilla antideslizante" in html
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" not in html


def test_supplier_table_show_description_column_false_omits_description_column():
    html = render_catalog_html(
        _supplier_context(
            show_description_column=False,
            sections=[_section_with_brand_groups("General", [_single_block()])],
        )
    )
    assert ">Descripción<" not in html
    assert '<col class="col-desc" />' not in html
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" in html
    simple_start = html.index("supplier-simple-block")
    simple_end = (
        html.index("supplier-family-variant-block", simple_start)
        if "supplier-family-variant-block" in html[simple_start:]
        else len(html)
    )
    simple_chunk = html[simple_start:simple_end]
    assert "supplier-simple-info-cell" not in simple_chunk
    assert "supplier-empty-cell" not in simple_chunk
    assert "Esterilla antideslizante" not in simple_chunk
    assert ">SKU<" in html
    assert ">EAN<" in html
    assert ">P.V.P.<" in html


def test_supplier_table_show_description_column_false_print_wider_sku():
    html = render_catalog_html(
        _supplier_context(
            show_description_column=False,
            catalog_render_density="print",
            sections=[
                _section_with_brand_groups(
                    "CARDIO",
                    [
                        _single_block(
                            family_title="Repuesto",
                            description_lines=["Consola Bluetooth"],
                            variants=[
                                {
                                    "sku": "REPUESTO-806",
                                    "ean": "8436578451234",
                                    "price_display": "12,00 €",
                                }
                            ],
                        )
                    ],
                )
            ],
        )
    )
    assert "REPUESTO-806" in html
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" in html
    assert "col.col-sku { width: 26%;" in html


def test_supplier_table_print_sku_ean_font_not_tiny():
    css = (TEMPLATES_DIR / "_supplier_table_print.css").read_text(encoding="utf-8")
    assert "--pdf-font-sku-ean: 7.5pt;" in css
    assert "--pdf-font-body: 6.5pt;" in css


def test_supplier_table_print_wider_price_column():
    css = (TEMPLATES_DIR / "_supplier_table_print.css").read_text(encoding="utf-8")
    assert "col.col-price { width: 13%;" in css
    assert "supplier-catalog-table--no-desc col.col-price { width: 14%;" in css


def test_supplier_table_print_narrower_image_4_3():
    css = (TEMPLATES_DIR / "_supplier_table_print.css").read_text(encoding="utf-8")
    assert "--pdf-image-width-simple: 22mm;" in css
    assert "--pdf-image-height-simple: 16.5mm;" in css
    assert "aspect-ratio: 4 / 3;" in css
    assert "col.col-image { width: 22mm;" in css


def test_supplier_table_print_renders_long_sku_ean_and_price():
    html = render_catalog_html(
        _supplier_context(
            catalog_render_density="print",
            show_description_column=False,
            sections=[
                _section_with_brand_groups(
                    "CARDIO",
                    [
                        _single_block(
                            variants=[
                                {
                                    "sku": "CR0108NEXO",
                                    "ean": "8435657018986",
                                    "price_display": "2048,57 €",
                                }
                            ],
                        )
                    ],
                )
            ],
        )
    )
    assert "CR0108NEXO" in html
    assert "8435657018986" in html
    assert "2048,57 €" in html
    assert "font-variant-numeric: tabular-nums" in html


def test_supplier_table_show_iva_and_description_column_independent():
    html_iva_desc = render_catalog_html(
        _supplier_context(
            show_iva_column=True,
            show_description_column=True,
            sections=[_section_with_brand_groups("General", [_single_block()])],
        )
    )
    assert ">Descripción<" in html_iva_desc
    assert "PVP + IVA" in html_iva_desc
    assert '<col class="col-desc" />' in html_iva_desc
    assert "supplier-catalog-table--with-iva" in html_iva_desc
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" not in html_iva_desc

    html_iva_no_desc = render_catalog_html(
        _supplier_context(
            show_iva_column=True,
            show_description_column=False,
            sections=[_section_with_brand_groups("General", [_single_block()])],
        )
    )
    assert ">Descripción<" not in html_iva_no_desc
    assert "PVP + IVA" in html_iva_no_desc
    assert '<col class="col-desc" />' not in html_iva_no_desc
    assert "supplier-catalog-table--with-iva" in html_iva_no_desc
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" in html_iva_no_desc

    html_no_iva_desc = render_catalog_html(
        _supplier_context(
            show_iva_column=False,
            show_description_column=True,
            sections=[_section_with_brand_groups("General", [_single_block()])],
        )
    )
    assert ">Descripción<" in html_no_iva_desc
    assert "PVP + IVA" not in html_no_iva_desc

    html_no_iva_no_desc = render_catalog_html(
        _supplier_context(
            show_iva_column=False,
            show_description_column=False,
            sections=[_section_with_brand_groups("General", [_single_block()])],
        )
    )
    assert ">Descripción<" not in html_no_iva_no_desc
    assert "PVP + IVA" not in html_no_iva_no_desc
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" in html_no_iva_no_desc


def test_supplier_table_family_variant_unchanged_when_description_column_false():
    html = render_catalog_html(
        _supplier_context(
            show_description_column=False,
            sections=[_section_with_brand_groups("General", [_variant_block()])],
        )
    )
    assert "supplier-family-variant-block" in html
    assert "supplier-catalog-table--family" in html
    assert "supplier-catalog-table--simple supplier-catalog-table--no-desc" not in html
    assert ">Descripción<" not in html
    assert 'rowspan="2"' in html
    assert ">Peso<" in html
    assert "DISC-5" in html


def test_supplier_table_family_header_shows_brand_display():
    html = render_catalog_html(_supplier_context())
    assert "supplier-family-brand-display" in html
    assert "Disco Olímpico Bumper Color Fraccional" in html
    assert " — NEXO" in html


def test_supplier_table_saco_gusano_mixed_brand_columns():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _variant_block(
                            master_name="Saco Gusano",
                            family_title="Saco Gusano",
                            title_line1="Saco Gusano",
                            brand="Varias marcas",
                            brand_display="Varias marcas",
                            brand_mode="mixed",
                            show_brand_column=True,
                            variant_columns=[
                                {"key": "variant_label", "label": "Variante"},
                                {"key": "brand", "label": "Marca"},
                            ],
                            variants=[
                                {
                                    "sku": "CRO107",
                                    "ean": "8435657018986",
                                    "variant_label": "2 personas - 160x30cms (60kgs)",
                                    "brand": "Sin marca",
                                    "price_display": "386,78 €",
                                },
                                {
                                    "sku": "CRO107NEXO",
                                    "ean": None,
                                    "variant_label": "2 personas - 160x30cms (60kgs) - LOGO NEXO",
                                    "brand": "NEXO",
                                    "price_display": "2048,57 €",
                                },
                            ],
                        )
                    ],
                )
            ],
        )
    )
    assert "supplier-family-cols-2" in html
    assert ">Variante<" in html
    assert ">Marca<" in html
    assert " — Varias marcas" in html
    assert "Sin marca" in html
    assert "NEXO" in html
    assert "CRO107NEXO" in html
    assert "2048,57 €" in html
    assert "supplier-family-variant-label-cell" in html
    assert "supplier-family-brand-cell" in html
    assert ">Variante</th>" in html or ">Variante<" in html


def test_supplier_table_barras_crossfit_variant_label_and_specs():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _variant_block(
                            master_name="Barras Crossfit",
                            family_title="Barras Crossfit",
                            title_line1="Barras Crossfit",
                            brand_display="Sin marca",
                            brand_mode="none",
                            variant_columns=[
                                {"key": "peso_kg", "label": "PESO"},
                                {"key": "color", "label": "COLOR"},
                                {"key": "variant_label", "label": "Variante"},
                            ],
                            variants=[
                                {
                                    "sku": "BOC001",
                                    "ean": "8435657018986",
                                    "peso_kg": "20 kg",
                                    "color": "Plata",
                                    "variant_label": "Barra 2,20 Mts - 20 kgs - 6 Rod - Agarre 28 mm PLATA",
                                    "price_display": "386,78 €",
                                },
                                {
                                    "sku": "BOC004",
                                    "ean": None,
                                    "peso_kg": "20 kg",
                                    "color": "Negro",
                                    "variant_label": "Barra 2,20 Mts - 20 kgs - 6 Rod - Agarre 28 mm NEGRA",
                                    "price_display": "175,80 €",
                                },
                            ],
                        )
                    ],
                )
            ],
        )
    )
    assert "supplier-family-cols-3" in html
    assert ">PESO<" in html
    assert ">COLOR<" in html
    assert ">Variante<" in html
    assert "Barra 2,20 Mts" in html
    assert "BOC001" in html
    assert ">Marca<" not in html


def test_supplier_table_no_fallback_variante_when_columns_empty():
    html = render_catalog_html(
        _supplier_context(
            sections=[
                _section_with_brand_groups(
                    "General",
                    [
                        _variant_block(
                            variant_columns=[],
                            variants=[
                                {
                                    "sku": "A-1",
                                    "ean": None,
                                    "price_display": "10,00 €",
                                },
                                {
                                    "sku": "A-2",
                                    "ean": None,
                                    "price_display": "12,00 €",
                                },
                            ],
                        )
                    ],
                )
            ],
        )
    )
    assert "supplier-family-cols-0" in html
    assert ">Variante<" not in html
    assert ">SKU<" in html
    assert "A-1" in html


def test_group_products_by_brand_uses_sin_marca_fallback():
    groups = group_products_by_brand(
        [
            {"brand": "XEBEX", "master_name": "A"},
            {"brand": None, "master_name": "B"},
            {"brand": "  ", "master_name": "C"},
        ]
    )
    assert [g["brand"] for g in groups] == ["XEBEX", "Sin marca"]
    assert len(groups[0]["products"]) == 1
    assert len(groups[1]["products"]) == 2
