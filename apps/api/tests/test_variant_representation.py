"""Unit tests for variant_representation: mixed brands, variant labels, columns."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.services.spec_resolver import SYNTHETIC_PESO_KEY, SpecColumn, consolidate_weight_columns
from app.services.variant_representation import (
    BRAND_COLUMN_KEY,
    SIN_MARCA,
    VARIANT_LABEL_KEY,
    VARIAS_MARCAS,
    build_variant_table_presentation,
    compute_variant_label,
    summarize_master_brand,
    variant_brand_display,
)
from tests.model_test_factories import (
    make_brand,
    make_product_master,
    make_product_variant,
    make_spec_definition,
    make_unit,
    make_variant_spec,
)


def _column(key: str, label: str, sort_order: int = 0, *, role: str = "variant_axis") -> SpecColumn:
    return SpecColumn(
        key=key,
        label=label,
        sort_order=sort_order,
        spec_definition_id=uuid4(),
        data_type="text" if key == "color" else "number",
        role=role,
    )


def _spec_row(
    key: str,
    *,
    value_number: Decimal | None = None,
    value_text: str | None = None,
    unit_symbol: str | None = None,
    role: str = "variant_axis",
):
    unit = make_unit(symbol=unit_symbol) if unit_symbol else None
    definition = make_spec_definition(
        key,
        label=key,
        data_type="number" if value_number is not None else "text",
        role=role,
        unit=unit,
    )
    return make_variant_spec(
        definition,
        value_number=value_number,
        value_text=value_text,
    )


def _variant(
    sku: str,
    *,
    display_name: str | None = None,
    reference_label: str | None = None,
    brand_name: str | None = None,
    specs: list | None = None,
    master=None,
):
    brand = make_brand(brand_name) if brand_name else None
    return make_product_variant(
        sku,
        master=master,
        display_name=display_name,
        reference_label=reference_label,
        raw_name=display_name,
        brand=brand,
        specs=specs or [],
    )


def _master(name: str):
    return make_product_master(name)


def test_summarize_master_brand_uniform_nexo():
    variants = [_variant("A", brand_name="NEXO"), _variant("B", brand_name="NEXO")]
    summary = summarize_master_brand(variants)
    assert summary.brand_mode == "uniform"
    assert summary.brand_display == "NEXO"
    assert summary.brand_id is not None


def test_summarize_master_brand_none():
    variants = [_variant("A"), _variant("B")]
    summary = summarize_master_brand(variants)
    assert summary.brand_mode == "none"
    assert summary.brand_display == SIN_MARCA
    assert summary.brand_id is None


def test_summarize_master_brand_mixed_null_and_nexo():
    variants = [_variant("CRO107"), _variant("CRO107NEXO", brand_name="NEXO")]
    summary = summarize_master_brand(variants)
    assert summary.brand_mode == "mixed"
    assert summary.brand_display == VARIAS_MARCAS
    assert summary.brand_id is None


def test_variant_brand_display_sin_marca():
    assert variant_brand_display(_variant("X")) == SIN_MARCA
    assert variant_brand_display(_variant("Y", brand_name="NEXO")) == "NEXO"


def test_compute_variant_label_barras_commercial_detail():
    master = _master("Barras Crossfit")
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    variant = _variant(
        "BOC001",
        display_name="Barra 2,20 Mts - 20 kgs - 6 Rod - 1500 lbs Agarre 28 mm PLATA",
        specs=[
            _spec_row("peso_kg", value_number=Decimal("20"), unit_symbol="kg"),
            _spec_row("color", value_text="Plata", role="catalog_spec"),
        ],
    )
    spec_values: dict[str, str | None] = {"peso_kg": "20 kg", "color": "Plata"}
    label = compute_variant_label(
        variant,
        master_name=master.name,
        visible_spec_columns=columns,
        spec_values=spec_values,
    )
    assert label is not None
    assert "agarre" in label.lower() or "rod" in label.lower() or "2,20" in label.lower()


def test_compute_variant_label_redundant_weight_only():
    master = _master("Disco Bumper")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variant = _variant(
        "DOB05",
        display_name="5 kgs",
        specs=[_spec_row("peso_kg", value_number=Decimal("5"), unit_symbol="kg")],
    )
    label = compute_variant_label(
        variant,
        master_name=master.name,
        visible_spec_columns=columns,
        spec_values={SYNTHETIC_PESO_KEY: "5 kg"},
    )
    assert label is None


def test_compute_variant_label_saco_gusano_persons():
    master = _master("Saco Gusano")
    variant = _variant(
        "CRO107",
        display_name="Saco Gusano 2 personas - 160x30cms (60kgs)",
    )
    label = compute_variant_label(
        variant,
        master_name=master.name,
        visible_spec_columns=[],
        spec_values={},
    )
    assert label is not None
    assert "personas" in label.lower() or "160" in label


def test_build_presentation_mixed_brand_shows_marca_column():
    master = _master("Saco Gusano")
    variants = [
        _variant("CRO107", display_name="Saco Gusano 2 personas - 160x30cms (60kgs)"),
        _variant(
            "CRO107NEXO",
            display_name="Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
            brand_name="NEXO",
        ),
    ]
    presentation = build_variant_table_presentation(master, variants, [])
    assert presentation.brand_summary.brand_mode == "mixed"
    assert presentation.show_brand_column is True
    assert any(col.key == BRAND_COLUMN_KEY for col in presentation.columns)
    nexo_row = presentation.rows_by_variant_id[variants[1].id]
    plain_row = presentation.rows_by_variant_id[variants[0].id]
    assert nexo_row.brand_display == "NEXO"
    assert plain_row.brand_display == SIN_MARCA


def test_build_presentation_reference_label_fallback():
    master = _master("Family")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variants = [
        _variant("A", reference_label="5 kgs"),
        _variant("B", reference_label="10 kgs"),
    ]
    presentation = build_variant_table_presentation(master, variants, columns)
    assert presentation.show_variant_name_column is True


def test_dobht_redundant_variant_label_hidden():
    master = _master("Disco Olimpico Bumper Hi-Temp (Casquillo de Acero)")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variants = [
        _variant(
            "DOBHT005",
            display_name="Disco Bumper Hi Temp 5 kgs (Numero Color)",
            reference_label="5 kg",
            specs=[_spec_row("peso_kg", value_number=Decimal("5"), unit_symbol="kg")],
        ),
        _variant(
            "DOBHT010",
            display_name="Disco Bumper Hi Temp 10 kgs (Numero Color)",
            reference_label="10 kg",
            specs=[_spec_row("peso_kg", value_number=Decimal("10"), unit_symbol="kg")],
        ),
    ]
    label = compute_variant_label(
        variants[0],
        master_name=master.name,
        visible_spec_columns=columns,
        spec_values={SYNTHETIC_PESO_KEY: "5 kg"},
    )
    assert label is None

    presentation = build_variant_table_presentation(master, variants, columns)
    assert presentation.show_variant_name_column is False
    assert VARIANT_LABEL_KEY not in [col.key for col in presentation.columns]
    assert SYNTHETIC_PESO_KEY in [col.key for col in presentation.columns]
    row = presentation.rows_by_variant_id[variants[0].id]
    assert row.variant_label is None
    assert VARIANT_LABEL_KEY not in row.attributes


def test_column_order_variant_label_specs_brand():
    master = _master("Saco Gusano")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variants = [
        _variant(
            "CRO107",
            display_name="Saco Gusano 2 personas - 160x30cms (60kgs)",
            specs=[_spec_row("peso_kg", value_number=Decimal("60"), unit_symbol="kg")],
        ),
        _variant(
            "CRO108",
            display_name="Saco Gusano 4 personas - 336x30,5cms (163kgs)",
            specs=[_spec_row("peso_kg", value_number=Decimal("163"), unit_symbol="kg")],
        ),
        _variant(
            "CRO107NEXO",
            display_name="Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
            brand_name="NEXO",
            specs=[_spec_row("peso_kg", value_number=Decimal("60"), unit_symbol="kg")],
        ),
    ]
    presentation = build_variant_table_presentation(master, variants, columns)
    keys = [col.key for col in presentation.columns]
    assert keys.index(VARIANT_LABEL_KEY) < keys.index(SYNTHETIC_PESO_KEY)
    assert keys.index(SYNTHETIC_PESO_KEY) < keys.index(BRAND_COLUMN_KEY)


def test_build_presentation_barras_column_order_and_label():
    master = _master("Barras Crossfit")
    columns = consolidate_weight_columns(
        [_column("peso_kg", "Peso", 10), _column("color", "Color", 20, role="catalog_spec")]
    )
    variants = [
        _variant(
            "BOC001",
            display_name="Barra 2,20 Mts - 20 kgs - 6 Rod - Agarre 28 mm PLATA",
            specs=[
                _spec_row("peso_kg", value_number=Decimal("20"), unit_symbol="kg"),
                _spec_row("color", value_text="Plata", role="catalog_spec"),
            ],
        ),
        _variant(
            "BOC004",
            display_name="Barra 2,20 Mts - 20 kgs - 6 Rod - Agarre 28 mm NEGRA",
            specs=[
                _spec_row("peso_kg", value_number=Decimal("20"), unit_symbol="kg"),
                _spec_row("color", value_text="Negro", role="catalog_spec"),
            ],
        ),
    ]
    presentation = build_variant_table_presentation(master, variants, columns)
    assert presentation.show_variant_name_column is True
    keys = [col.key for col in presentation.columns]
    assert keys[0] == VARIANT_LABEL_KEY
    label = presentation.rows_by_variant_id[variants[0].id].variant_label
    assert label is not None
    assert "agarre" in label.lower() or "rod" in label.lower() or "2,20" in label.lower()


def test_weight_glued_plural_stripped_when_covered_by_spec():
    master = _master("Saco Gusano")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variant = _variant(
        "CRO107",
        display_name="Saco Gusano 2 personas - 160x30cms (60kgs)",
        specs=[_spec_row("peso_kg", value_number=Decimal("60"), unit_symbol="kg")],
    )
    label = compute_variant_label(
        variant,
        master_name=master.name,
        visible_spec_columns=columns,
        spec_values={SYNTHETIC_PESO_KEY: "60 kg"},
    )
    assert label is not None
    assert "60kgs" not in (label or "").lower()
    assert "60 kgs" not in (label or "").lower()
    assert "personas" in label.lower()


def test_logo_nexo_fully_stripped_when_brand_nexo():
    master = _master("Saco Gusano")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variant = _variant(
        "CRO107NEXO",
        display_name="Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
        brand_name="NEXO",
        specs=[_spec_row("peso_kg", value_number=Decimal("60"), unit_symbol="kg")],
    )
    label = compute_variant_label(
        variant,
        master_name=master.name,
        visible_spec_columns=columns,
        spec_values={SYNTHETIC_PESO_KEY: "60 kg"},
        brand_display="NEXO",
    )
    assert label is not None
    assert "logo" not in label.lower()
    assert "nexo" not in label.lower()
    assert "60kgs" not in label.lower()
    assert "personas" in label.lower()
    assert "160" in label


def test_saco_gusano_nexo_presentation_clean_label():
    master = _master("Saco Gusano")
    columns = consolidate_weight_columns([_column("peso_kg", "Peso", 10)])
    variants = [
        _variant(
            "CRO107",
            display_name="Saco Gusano 2 personas - 160x30cms (60kgs)",
            specs=[_spec_row("peso_kg", value_number=Decimal("60"), unit_symbol="kg")],
        ),
        _variant(
            "CRO108",
            display_name="Saco Gusano 4 personas - 336x30,5cms (163kgs)",
            specs=[_spec_row("peso_kg", value_number=Decimal("163"), unit_symbol="kg")],
        ),
        _variant(
            "CRO107NEXO",
            display_name="Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
            brand_name="NEXO",
            specs=[_spec_row("peso_kg", value_number=Decimal("60"), unit_symbol="kg")],
        ),
    ]
    presentation = build_variant_table_presentation(master, variants, columns)
    nexo_row = presentation.rows_by_variant_id[variants[2].id]
    assert nexo_row.brand_display == "NEXO"
    if SYNTHETIC_PESO_KEY in nexo_row.attributes:
        assert nexo_row.attributes[SYNTHETIC_PESO_KEY] == "60 kg"
    label = nexo_row.variant_label
    assert label is not None
    assert label.lower() == "2 personas - 160x30cms"
    assert "logo" not in label.lower()
    assert "nexo" not in label.lower()
    assert "60kgs" not in label.lower()
    assert "(60" not in label
