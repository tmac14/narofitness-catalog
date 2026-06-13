"""Unit tests for spec_resolver and catalog_builder helpers."""

from uuid import UUID, uuid4

from app.services.catalog_builder import _build_product_block, _title_lines
from app.services.spec_resolver import (
    ResolvedSpecValue,
    SpecColumn,
    count_variant_attributes,
    master_highlights_from_specs,
    master_subtitle_from_specs,
)
from tests.model_test_factories import make_brand, make_product_master


def _master(name: str, brand: str | None = None):
    brand_obj = make_brand(brand) if brand else None
    return make_product_master(
        name,
        master_id=UUID("00000000-0000-0000-0000-000000000001"),
        brand=brand_obj,
    )


def _spec(key: str, value: str | None, role: str = "catalog_spec") -> ResolvedSpecValue:
    return ResolvedSpecValue(
        id=None,
        spec_definition_id=uuid4(),
        key=key,
        label=key,
        data_type="text",
        role=role,
        value=value,
    )


def test_master_subtitle_uses_highlight_keys():
    specs = [
        _spec("color", "Negro", role="catalog_spec"),
        _spec("material", "Goma maciza", role="technical_spec"),
    ]
    assert (
        master_subtitle_from_specs(specs, highlight_keys=("color", "material"))
        == "Negro · Goma maciza"
    )


def test_master_highlights_from_profile_keys():
    specs = [
        _spec("color", "Negro", role="catalog_spec"),
        _spec("material", "Goma maciza", role="technical_spec"),
    ]
    highlights = master_highlights_from_specs(specs, ("color", "material"))
    assert highlights == [
        {"label": "color", "value": "Negro"},
        {"label": "material", "value": "Goma maciza"},
    ]


def test_master_subtitle_falls_back_to_catalog_spec():
    specs = [_spec("tipo", "Pro"), _spec("material", "Acero", role="technical_spec")]
    assert master_subtitle_from_specs(specs) == "Pro"


def test_master_subtitle_falls_back_to_first_catalog_spec():
    specs = [_spec("material", "Goma", role="technical_spec")]
    assert master_subtitle_from_specs(specs) == "Goma"


def test_master_subtitle_empty():
    assert master_subtitle_from_specs([]) is None


def test_title_lines_from_highlight_specs():
    master = _master("Kettlebell")
    specs = [_spec("color", "Negro", role="catalog_spec")]
    assert _title_lines(master, specs, ("color",)) == ("Kettlebell", "Negro")


def test_title_lines_split_brand_suffix():
    master = _master("BICI C-21X ADIDAS", brand="ADIDAS")
    assert _title_lines(master, []) == ("BICI C-21X", "ADIDAS")


def test_title_lines_brand_when_not_in_name():
    master = _master("Kettlebell", brand="NEXO")
    assert _title_lines(master, []) == ("Kettlebell", "NEXO")


def test_title_lines_single_when_no_split():
    master = _master("Esterilla yoga")
    assert _title_lines(master, []) == ("Esterilla yoga", None)


def _variant_rows(*, multi_attr: bool = True, multi_variant: bool = True):
    columns = [
        SpecColumn(
            key="peso_kg",
            label="Peso",
            sort_order=0,
            spec_definition_id=uuid4(),
            data_type="number",
            role="variant_axis",
        ),
        SpecColumn(
            key="color",
            label="Color",
            sort_order=1,
            spec_definition_id=uuid4(),
            data_type="text",
            role="catalog_spec",
        ),
    ]
    if not multi_variant:
        return [
            {
                "sku": "A-1",
                "peso_kg": "10 kg",
                "color": "Rojo" if multi_attr else None,
                "price_display": "10,00 €",
                "sort_order": 0,
                "_variant_images": [],
            }
        ], columns
    return [
        {
            "sku": "A-1",
            "peso_kg": "8 kg",
            "color": "Rosa" if multi_attr else None,
            "price_display": "10,00 €",
            "sort_order": 0,
            "_variant_images": [],
        },
        {
            "sku": "A-2",
            "peso_kg": "12 kg",
            "color": "Azul" if multi_attr else None,
            "price_display": "12,00 €",
            "sort_order": 1,
            "_variant_images": [],
        },
    ], columns


def test_build_product_block_includes_highlights():
    rows, columns = _variant_rows(multi_attr=True)
    specs = [_spec("material", "Goma maciza", role="technical_spec")]
    block = _build_product_block(
        _master("Product"),
        rows,
        columns,
        specs,
        False,
        "",
        highlight_keys=("material",),
    )
    assert block["master_highlights"] == [{"label": "material", "value": "Goma maciza"}]
    assert block["layout_id"] == "variant_row_wide"
    assert block["variant_columns"] == [
        {"key": "peso_kg", "label": "Peso"},
        {"key": "color", "label": "Color"},
    ]
    assert not block["layout_selection"]["fallback_used"]


def test_count_variant_attributes():
    rows = [{"peso_kg": "10 kg", "color": "Rojo"}, {"peso_kg": "12 kg", "color": "Azul"}]
    assert count_variant_attributes(rows, ["peso_kg", "color"]) == 2
    assert count_variant_attributes(rows, ["peso_kg"]) == 1
    assert count_variant_attributes([{"peso_kg": None, "color": None}], ["peso_kg", "color"]) == 0


def test_subtitle_keys_deprecated():
    from app.services.spec_resolver import SUBTITLE_SPEC_KEYS

    assert SUBTITLE_SPEC_KEYS == ()
