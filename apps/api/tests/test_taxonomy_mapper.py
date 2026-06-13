"""Unit tests for taxonomy mapping rule matching."""

from dataclasses import dataclass

from app.models import TaxonomyMappingRule
from app.services.taxonomy_mapper import _rule_matches


@dataclass
class _Row:
    detected_category_path_raw: str = ""
    sku: str | None = None
    normalized_name: str = ""


def test_sku_prefix_match():
    rule = TaxonomyMappingRule(match_type="sku_prefix", match_value="REPUESTO", priority=10)
    assert _rule_matches(rule, _Row(sku="REPUESTO-123"))
    assert not _rule_matches(rule, _Row(sku="DOBNEXO05N"))


def test_section_keyword_requires_section_when_configured():
    rule = TaxonomyMappingRule(
        match_type="section_keyword",
        match_value="DISCOS Y BARRAS|disco",
        priority=50,
    )
    row = _Row(
        detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO FUNCIONAL",
        sku="DOBNEXO05N",
        normalized_name="Disco Bumper NEXO Negro - 5 kgs",
    )
    assert not _rule_matches(rule, row)


def test_section_keyword_matches_in_section():
    rule = TaxonomyMappingRule(
        match_type="section_keyword",
        match_value="DISCOS Y BARRAS|disco",
        priority=50,
    )
    row = _Row(
        detected_category_path_raw="DISCOS Y BARRAS > BUMPER",
        normalized_name="Disco Olimpico Premium - 5 kgs",
    )
    assert _rule_matches(rule, row)


def test_section_keyword_does_not_match_section_title_substring():
    rule = TaxonomyMappingRule(
        match_type="section_keyword",
        match_value="DISCOS Y BARRAS|disco",
        priority=50,
    )
    row = _Row(
        detected_category_path_raw="DISCOS Y BARRAS > BUMPER",
        normalized_name="Producto genérico",
    )
    assert not _rule_matches(rule, row)


def test_section_keyword_mancuerna_in_discos_section():
    rule = TaxonomyMappingRule(
        match_type="section_keyword",
        match_value="DISCOS Y BARRAS|mancuerna",
        priority=35,
    )
    row = _Row(
        detected_category_path_raw="DISCOS Y BARRAS",
        normalized_name="Mancuerna Hexagonal 10 kgs",
    )
    assert _rule_matches(rule, row)


def test_section_keyword_barra_in_discos_section():
    rule = TaxonomyMappingRule(
        match_type="section_keyword",
        match_value="DISCOS Y BARRAS|barra",
        priority=45,
    )
    row = _Row(
        detected_category_path_raw="DISCOS Y BARRAS",
        normalized_name="Barra Olímpica 28 MM - 120 cm",
    )
    assert _rule_matches(rule, row)


def test_dobnexo_sku_prefix_maps_discos():
    rule = TaxonomyMappingRule(match_type="sku_prefix", match_value="DOBNEXO", priority=15)
    row = _Row(
        detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO FUNCIONAL",
        sku="DOBNEXO05N",
        normalized_name="Disco Bumper NEXO Negro - 5 kgs",
    )
    assert _rule_matches(rule, row)


def test_section_keyword_matches_row_text_without_section():
    rule = TaxonomyMappingRule(match_type="section_keyword", match_value="disco", priority=50)
    row = _Row(
        detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO FUNCIONAL",
        sku="DOBNEXO05N",
        normalized_name="Disco Bumper NEXO Negro - 5 kgs",
    )
    assert _rule_matches(rule, row)


def test_section_path_exact():
    rule = TaxonomyMappingRule(match_type="section_path", match_value="CARDIO > BICI", priority=10)
    assert _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > BICI"))
    assert not _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > BICI EXTRA"))


def test_cardio_remo_section_path():
    rule = TaxonomyMappingRule(match_type="section_path", match_value="CARDIO > REMO", priority=21)
    assert _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > REMO", sku="REM002"))
    assert not _rule_matches(
        rule,
        _Row(
            detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            normalized_name="Saco con remo integrado",
            sku="VAR120NEXO",
        ),
    )


def test_cardio_cinta_section_path():
    rule = TaxonomyMappingRule(match_type="section_path", match_value="CARDIO > CINTA", priority=22)
    assert _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > CINTA", sku="CIN001"))
    assert not _rule_matches(
        rule,
        _Row(
            detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            normalized_name="Wall Ball con cinta de resistencia",
            sku="CRO100",
        ),
    )


def test_cardio_eliptica_section_path():
    rule = TaxonomyMappingRule(
        match_type="section_path", match_value="CARDIO > ELIPTICA", priority=23
    )
    assert _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > ELIPTICA"))
    assert not _rule_matches(
        rule,
        _Row(
            detected_category_path_raw="MATERIAL DE ESTUDIO",
            normalized_name="Producto eliptica portatil",
        ),
    )


def test_cardio_bicis_section_path():
    rule = TaxonomyMappingRule(match_type="section_path", match_value="CARDIO > BICIS", priority=24)
    assert _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > BICIS"))
    assert not _rule_matches(
        rule,
        _Row(
            detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            normalized_name="Soporte tipo bici para rack",
        ),
    )


def test_cardio_ski_section_path_parent_only():
    rule = TaxonomyMappingRule(match_type="section_path", match_value="CARDIO > SKI", priority=26)
    assert _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > SKI"))
    assert not _rule_matches(rule, _Row(detected_category_path_raw="CARDIO > SKI EXTRA"))


def test_material_estudio_section_path():
    rule = TaxonomyMappingRule(
        match_type="section_path",
        match_value="MATERIAL DE ESTUDIO",
        priority=29,
    )
    assert _rule_matches(rule, _Row(detected_category_path_raw="MATERIAL DE ESTUDIO", sku="ELA001"))
    assert not _rule_matches(
        rule,
        _Row(
            detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            normalized_name="Material de estudio portatil",
        ),
    )
