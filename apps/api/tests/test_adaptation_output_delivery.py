"""Tests for adaptation output delivery profiles and APIs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.direct_adaptation.output_delivery import (
    DELIVERY_EPHEMERAL,
    DELIVERY_PERSIST,
    OUTPUT_PROFILE_ARCHIVE,
    OUTPUT_PROFILE_EMAIL,
    OutputDeliveryValidationError,
    resolve_output_delivery,
)
from app.services.direct_adaptation.pdf_encode import apply_output_profile_encode
from app.services.direct_adaptation.parity_audit import build_parity_report


def test_resolve_output_delivery_defaults():
    resolved = resolve_output_delivery({"output_delivery": {}})
    assert resolved.output_profile == OUTPUT_PROFILE_EMAIL
    assert resolved.delivery_mode == DELIVERY_PERSIST


def test_resolve_output_delivery_rejects_final_ephemeral():
    with pytest.raises(OutputDeliveryValidationError):
        resolve_output_delivery(
            {"output_delivery": {}},
            job_request={"delivery_mode": DELIVERY_EPHEMERAL},
            export_kind="final",
        )


def test_email_encode_preserves_small_pdf():
    import fitz

    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    output, metrics = apply_output_profile_encode(
        pdf_bytes,
        output_profile=OUTPUT_PROFILE_EMAIL,
        email_budget_bytes=15 * 1024 * 1024,
        archive_soft_warn_bytes=50 * 1024 * 1024,
    )
    assert output[:4] == b"%PDF"
    assert metrics["within_budget"] is True


def test_parity_report_email_profile_size_gate():
    manifest = {
        "page_count": 65,
        "price_report": {"row_count": 871},
        "price_overlay": {"rows_applied": 871, "apply_rate": 1.0},
        "cover_plan": {"application_status": "covers_applied"},
        "table_recompose": {"cell_borders_drawn": 871},
        "image_recompose": {"images_recomposed": 397, "apply_rate": 0.995, "collages_built": 12},
        "pdf_artifact": {"byte_length": 4_105_095},
        "output_delivery": {"profile": OUTPUT_PROFILE_EMAIL},
        "baseline_audit": {"mvp_gates_pass": True},
        "geometry_summary": {
            "resolve_rate": 1.0,
            "image_groups_resolve_rate": 0.995,
            "image_groups_resolved": 397,
        },
    }
    report = build_parity_report(manifest=manifest)
    assert report["gates"]["output_size_within_budget"]["passed"] is True
