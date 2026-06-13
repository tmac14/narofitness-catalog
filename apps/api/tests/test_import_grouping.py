from decimal import Decimal

from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus

FDL_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
        "false_family_suffixes": ["NEXO"],
        "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
        "cross_training_block_family_regex": r"^(?:CRO\d{2,4}(?:NEXO)?|BOC\d{3}(?:NEXO)?)$",
        "cross_training_block_section_root": "CROSSTRAINING",
        "cross_training_block_category_slug": "cross-training",
        "cross_training_block_name_tokens": ["barras crossfit", "saco gusano"],
    },
}


def _assert_false_family(row: ImportRow) -> None:
    assert "false_family_pattern" in row.review_reasons
    assert "peso_kg" not in row.parsed_variant_specs_raw
    assert row.grouping_confidence is not None
    assert row.grouping_confidence <= 0.4
    assert row.review_status == "needs_review" or row.status.value == "revisar"


def _row(sku: str, name: str) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        brand="NEXO",
        ean=None,
        category_path="DISCOS",
        price_amount=Decimal("19.55"),
    )


def test_fdl_groups_bumper_discs_same_master():
    r1 = _row("DOBNEXO05N", "Disco Bumper NEXO Negro - 5 kgs")
    r2 = _row("DOBNEXO10N", "Disco Bumper NEXO Negro - 10 kgs")
    apply_grouping([r1, r2], FDL_CONFIG)
    assert r1.master_key == r2.master_key == "DOBNEXON"
    assert r1.parsed_variant_specs_raw.get("peso_kg") == 5
    assert r2.parsed_variant_specs_raw.get("peso_kg") == 10
    assert r1.grouping_confidence is not None
    assert r1.grouping_confidence >= 0.7


def test_fdl_fallback_one_per_sku():
    r = _row("FDRig-3", "JAULA CENTRAL - 3 Mts")
    apply_grouping([r], FDL_CONFIG)
    assert r.master_key == "FDRig-3"
    assert "regex_fallback_1_1" in r.review_reasons
    assert "low_grouping_confidence" in r.review_reasons


def test_fdl_false_family_needs_review():
    r = _row("CRONEXO05N", "Cronometro NEXO - 5 kgs")
    apply_grouping([r], FDL_CONFIG)
    assert "false_family_pattern" in r.review_reasons
    assert "peso_kg" not in r.parsed_variant_specs_raw
    assert r.review_status == "needs_review" or r.status.value == "revisar"


def test_varjh_false_family_needs_review():
    r = _row("VARJH10N", "Variante VARJH - 10 kgs")
    apply_grouping([r], FDL_CONFIG)
    assert "false_family_pattern" in r.review_reasons
    assert "peso_kg" not in r.parsed_variant_specs_raw


def test_cro107nexo_explicit_logo_not_false_family():
    r = _row(
        "CRO107NEXO",
        "Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
    )
    r.raw_name = "Saco Gusano Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO"
    apply_grouping([r], FDL_CONFIG)
    assert "false_family_pattern" not in r.review_reasons
    assert r.grouping_confidence is not None
    assert r.grouping_confidence >= 0.7


def test_cro108nexo_without_explicit_signal_stays_false_family():
    r = _row(
        "CRO108NEXO",
        "Saco Gusano 4 personas - 336x30,5cms (163kgs)",
    )
    apply_grouping([r], FDL_CONFIG)
    _assert_false_family(r)
    assert r.grouping_reason == "false_family:CRONEXO"


def test_boc001nexo_without_explicit_signal_stays_false_family():
    r = _row("BOC001NEXO", "Boca de Lobo - 1 kg")
    apply_grouping([r], FDL_CONFIG)
    _assert_false_family(r)
    assert r.grouping_reason == "false_family:BOCNEXO"
    assert r.grouping_confidence <= 0.4


def test_boc001nexo_explicit_header_not_false_family():
    from uuid import uuid4

    r = _row(
        "BOC001NEXO",
        "Barra 2,20 Mts - 20 kgs - 6 Rod - 1500 lbs Agarre 28 mm PLATA - LOGO NEXO",
    )
    r.raw_name = (
        "Barras Crossfit - NEXO Barra 2,20 Mts - 20 kgs - 6 Rod - "
        "1500 lbs Agarre 28 mm PLATA - LOGO NEXO"
    )
    r.family_header_raw = "Barras Crossfit - NEXO"
    r.family_block_id = "p14:block"
    r.category_path = "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL"
    r.mapped_category_id = uuid4()
    r.mapped_category_slug = "cross-training"
    r.mapped_category_confidence = 1.0
    apply_grouping([r], FDL_CONFIG)
    assert "false_family_pattern" not in r.review_reasons
    assert r.master_key == "BOC-BARRAS-CROSSFIT-NEXO"
    assert r.grouping_reason == "cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO"


def test_grouping_locked_preserved_in_schema():
    from app.schemas import ParsedRowSchema

    schema = ParsedRowSchema(
        row_index=0,
        status="ok",
        sku="TESTSKU01",
        name="Test",
        brand=None,
        ean=None,
        category_path="X",
        price_amount="10.00",
        master_key="CUSTOM",
        grouping_locked=True,
    )
    assert schema.grouping_locked is True
