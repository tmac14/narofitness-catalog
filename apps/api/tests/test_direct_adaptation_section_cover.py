"""Tests for Phase 2F section cover replacement."""

from __future__ import annotations

import hashlib
from pathlib import Path

import fitz

from app.services.direct_adaptation.cover_assets import bundled_cover_assets_available
from app.services.direct_adaptation.cover_apply import merge_cover_apply_results
from app.services.direct_adaptation.main_cover_replace import apply_main_cover_replace
from app.services.direct_adaptation.section_cover_replace import apply_section_cover_replace


def _multi_page_pdf(pages: int = 3) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=595.2, height=841.68)
    data = doc.tobytes()
    doc.close()
    return data


def test_apply_section_cover_stub_on_page_2():
    source = _multi_page_pdf()
    recipe_json = {
        "presentation": {"brand_green": "#8dbb24"},
        "covers": {
            "sections": [
                {
                    "page_number": 2,
                    "section_key": "cardio",
                    "asset_path": "wireframes/portadas-fdl/missing/01-cardio.png",
                }
            ]
        },
    }
    output, result = apply_section_cover_replace(source, recipe_json)
    assert result["sections_applied"] == 1
    assert result["section_covers"][0]["method"] == "stub"
    assert result["section_covers"][0]["section_key"] == "cardio"
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()


def test_apply_section_cover_uses_resolved_asset(tmp_path):
    asset_dir = tmp_path / "wireframes" / "portadas-fdl" / "categorias"
    asset_dir.mkdir(parents=True)
    asset_path = asset_dir / "01-cardio.png"
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 80), 1)
    pix.save(str(asset_path))

    source = _multi_page_pdf()
    recipe_json = {
        "presentation": {"brand_green": "#8dbb24"},
        "covers": {
            "sections": [
                {
                    "page_number": 2,
                    "section_key": "cardio",
                    "asset_path": "wireframes/portadas-fdl/categorias/01-cardio.png",
                }
            ]
        },
    }
    output, result = apply_section_cover_replace(source, recipe_json, extra_asset_roots=[tmp_path])
    assert result["sections_applied"] == 1
    assert result["section_covers"][0]["method"] == "asset"
    assert Path(result["section_covers"][0]["resolved_path"]) == asset_path
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()


def test_merge_cover_apply_results_all_stub():
    main_result = {
        "main_cover": {"method": "stub", "status": "applied"},
        "application_status": "main_cover_stub_applied",
    }
    section_result = {
        "section_covers": [{"section_key": "cardio", "method": "stub", "status": "applied"}],
        "sections_applied": 1,
    }
    merged = merge_cover_apply_results(main_result, section_result)
    assert merged["application_status"] == "covers_stub_applied"
    assert merged["sections_applied"] == 1


def test_main_and_section_pipeline_marks_covers_applied():
    source = _multi_page_pdf()
    recipe_json = {
        "presentation": {"brand_green": "#8dbb24"},
        "covers": {
            "main": {"page_number": 1, "asset_path": "wireframes/portadas-fdl/main/5.png"},
            "sections": [
                {
                    "page_number": 2,
                    "section_key": "cardio",
                    "asset_path": "wireframes/portadas-fdl/categorias/01-cardio.png",
                }
            ],
        },
    }
    main_output, main_result = apply_main_cover_replace(source, recipe_json, project_name="Catalog 2026")
    final_output, section_result = apply_section_cover_replace(main_output, recipe_json)
    merged = merge_cover_apply_results(main_result, section_result)
    if bundled_cover_assets_available():
        assert merged["application_status"] == "covers_applied"
        assert main_result["main_cover"]["method"] == "asset"
        assert section_result["section_covers"][0]["method"] == "asset"
    else:
        assert merged["application_status"] == "covers_stub_applied"
    assert merged["sections_applied"] == 1
    assert hashlib.sha256(final_output).hexdigest() != hashlib.sha256(source).hexdigest()
