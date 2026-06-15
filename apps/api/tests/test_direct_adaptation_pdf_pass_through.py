"""Tests for Phase 2D FDL pass-through PDF and cover plan."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import fitz

from app.services.adaptation_export_storage import write_pdf_atomic
from app.services.direct_adaptation.cover_plan import build_cover_plan
from app.services.direct_adaptation.fdl_direct_v1 import (
    build_fdl_preview_manifest,
    build_pdf_artifact_metadata,
)


def test_build_cover_plan_from_recipe():
    recipe_json = {
        "covers": {
            "render_mode": "full_bleed",
            "main": {"page_number": 1, "asset_path": "wireframes/portadas-fdl/missing/main.png"},
            "sections": [
                {"page_number": 2, "section_key": "cardio", "asset_path": "wireframes/portadas-fdl/missing/01-cardio.png"},
            ],
        }
    }
    plan = build_cover_plan(recipe_json)
    assert plan["entry_count"] == 2
    assert plan["entries"][0]["role"] == "main"
    assert plan["entries"][1]["section_key"] == "cardio"
    assert plan["application_status"] == "pending"
    assert plan["entries"][0]["asset_status"] == "referenced_not_bundled"


def test_build_fdl_preview_manifest_with_pdf_artifact():
    project = SimpleNamespace(
        id=uuid4(),
        name="NAROFITNESS Catalog 2026",
        profile_key="fdl_wholesale_tariff",
        profile_version="1.0.0",
    )
    recipe = SimpleNamespace(
        id=uuid4(),
        recipe_fingerprint="a" * 64,
        recipe_json={
            "pricing_policy": {
                "operation": "multiply",
                "factor": "1.20",
                "rounding": "ROUND_HALF_UP",
                "scale": 2,
                "currency": "EUR",
            },
            "covers": {"main": {"page_number": 1}, "sections": []},
        },
    )
    source = SimpleNamespace(id=uuid4(), sha256="b" * 64, page_count=2)
    snapshot = SimpleNamespace(
        id=uuid4(),
        snapshot_fingerprint="c" * 64,
        snapshot_json={
            "pages": [
                {
                    "page_number": 3,
                    "product_blocks": [
                        {
                            "rows": [
                                {
                                    "stable_row_id": "row_1",
                                    "reference": "SKU1",
                                    "base_price": {"amount": "10.00", "currency": "EUR"},
                                }
                            ]
                        }
                    ],
                }
            ]
        },
    )
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    pdf_meta = build_pdf_artifact_metadata(
        source=source,
        pdf_bytes=pdf_bytes,
        rel_path="adaptation_exports/x/y.preview.pdf",
        cover_apply_result={
            "main_cover": {"page_number": 1, "method": "stub", "status": "applied"},
            "sections_applied": 0,
            "application_status": "main_cover_stub_applied",
        },
    )
    manifest = build_fdl_preview_manifest(
        project=project,
        recipe=recipe,
        source=source,
        snapshot=snapshot,
        pdf_artifact=pdf_meta,
        cover_apply_result={
            "main_cover": {"page_number": 1, "method": "stub", "status": "applied"},
            "sections_applied": 0,
            "application_status": "main_cover_stub_applied",
        },
    )
    assert manifest["status"] == "main_cover_ready"
    assert manifest["renderer_version"] == "0.19.0"
    assert manifest["cover_plan"]["entry_count"] == 1
    assert manifest["cover_plan"]["application_status"] == "main_cover_stub_applied"
    assert manifest["pdf_artifact"]["byte_length"] == len(pdf_bytes)
    assert manifest["pdf_artifact"]["mode"] == "main_cover_stub_applied"


def test_write_pdf_atomic(tmp_path, monkeypatch):
    from app.config import settings

    private_dir = tmp_path / "private"
    private_dir.mkdir()
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))
    pdf_bytes = b"%PDF-1.4 minimal"
    rel = write_pdf_atomic(project_id=uuid4(), export_id=uuid4(), pdf_bytes=pdf_bytes)
    assert (private_dir / rel).read_bytes() == pdf_bytes
