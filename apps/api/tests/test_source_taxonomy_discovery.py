"""Unit tests for source category key normalization and discovery helpers."""

import json
from pathlib import Path

from app.services.taxonomy_mapper import normalize_source_category_key

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_normalize_source_category_key():
    assert normalize_source_category_key("cardio > remo") == "CARDIO > REMO"
    assert normalize_source_category_key("CARDIO>REMO") == "CARDIO > REMO"
    assert normalize_source_category_key("  CARDIO  >  CINTA  ") == "CARDIO > CINTA"


def test_fdl_source_categories_fixture_paths():
    data = json.loads((FIXTURES / "fdl_source_categories_sample.json").read_text(encoding="utf-8"))
    paths = {normalize_source_category_key(p) for p in data["source_paths"]}
    assert "CARDIO > REMO" in paths
    assert "CARDIO > CINTA" in paths
    assert "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL" in paths
    assert "MATERIAL DE ESTUDIO" in paths
