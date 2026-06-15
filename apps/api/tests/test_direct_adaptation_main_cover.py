"""Tests for Phase 2E main cover replacement."""

from __future__ import annotations

import hashlib
from pathlib import Path

import fitz

from app.services.direct_adaptation.main_cover_replace import apply_main_cover_replace


def _two_page_pdf() -> bytes:
    doc = fitz.open()
    doc.new_page(width=595.2, height=841.68)
    doc.new_page(width=595.2, height=841.68)
    data = doc.tobytes()
    doc.close()
    return data


def test_apply_main_cover_stub_changes_output():
    source = _two_page_pdf()
    recipe_json = {
        "presentation": {"brand_green": "#8dbb24"},
        "covers": {"main": {"page_number": 1, "asset_path": "wireframes/portadas-fdl/missing/5.png"}},
    }
    output, result = apply_main_cover_replace(
        source,
        recipe_json,
        project_name="NAROFITNESS Catalog 2026",
    )
    assert result["main_cover"]["method"] == "stub"
    assert result["application_status"] == "main_cover_stub_applied"
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()

    doc = fitz.open(stream=output, filetype="pdf")
    assert doc.page_count == 2
    doc.close()


def test_apply_main_cover_uses_resolved_asset(tmp_path):
    asset_dir = tmp_path / "wireframes" / "portadas-fdl" / "main"
    asset_dir.mkdir(parents=True)
    asset_path = asset_dir / "5.png"
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 80), 1)
    pix.save(str(asset_path))

    source = _two_page_pdf()
    recipe_json = {
        "presentation": {"brand_green": "#8dbb24"},
        "covers": {"main": {"page_number": 1, "asset_path": "wireframes/portadas-fdl/main/5.png"}},
    }
    output, result = apply_main_cover_replace(
        source,
        recipe_json,
        project_name="Catalog",
        extra_asset_roots=[tmp_path],
    )
    assert result["main_cover"]["method"] == "asset"
    assert result["application_status"] == "main_cover_applied"
    assert Path(result["main_cover"]["resolved_path"]) == asset_path

    doc = fitz.open(stream=output, filetype="pdf")
    assert doc.page_count == 2
    doc.close()


def test_apply_main_cover_email_profile_smaller_than_archive(tmp_path):
    asset_dir = tmp_path / "wireframes" / "portadas-fdl" / "main"
    asset_dir.mkdir(parents=True)
    asset_path = asset_dir / "5.png"
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 2400, 3200), 1)
    pix.save(str(asset_path))

    source = _two_page_pdf()
    base_recipe = {
        "presentation": {"brand_green": "#8dbb24"},
        "covers": {"main": {"page_number": 1, "asset_path": "wireframes/portadas-fdl/main/5.png"}},
    }
    email_recipe = {**base_recipe, "output_delivery": {"profile": "email_optimized"}}
    archive_recipe = {**base_recipe, "output_delivery": {"profile": "archive_quality"}}

    email_out, _ = apply_main_cover_replace(
        source,
        email_recipe,
        project_name="Catalog",
        extra_asset_roots=[tmp_path],
    )
    archive_out, _ = apply_main_cover_replace(
        source,
        archive_recipe,
        project_name="Catalog",
        extra_asset_roots=[tmp_path],
    )
    assert len(email_out) < len(archive_out)
