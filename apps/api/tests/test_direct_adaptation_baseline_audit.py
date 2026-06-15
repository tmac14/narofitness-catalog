"""Tests for Phase 2I FDL baseline exit-gate audit."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.direct_adaptation.baseline_audit import build_baseline_audit, build_table_recompose_status


def test_build_table_recompose_status_pending():
    status = build_table_recompose_status({"table_recompose": {"status": "pending"}})
    assert status["status"] == "pending"
    assert status["capability"] == "direct.table_recompose"


def test_baseline_audit_table_recompose_gate_when_applied():
    source = SimpleNamespace(
        page_count=65,
        sha256="11ebb3956724702796a46ee7536458fdf8ddeade4c389a0c7df0d055435bf06b",
    )
    audit = build_baseline_audit(
        profile_key="fdl_wholesale_tariff",
        source=source,
        price_report={
            "row_count": 871,
            "rows": [{"base_price": {"amount": "10.00"}, "client_price": {"amount": "12.00"}}],
        },
        recipe_json={
            "pricing_policy": {
                "operation": "multiply",
                "factor": "1.20",
                "rounding": "ROUND_HALF_UP",
                "scale": 2,
            }
        },
        render_apply_result={
            "application_status": "covers_stub_applied",
            "price_overlay": {"rows_applied": 400},
            "table_recompose": {"pages_applied": 1},
        },
    )
    assert audit is not None
    assert audit["gates"]["table_recompose"] is True
    assert audit["phase2_preview_mvp_pass"] is True


def test_baseline_audit_mvp_gates_pass():
    source = SimpleNamespace(
        page_count=65,
        sha256="11ebb3956724702796a46ee7536458fdf8ddeade4c389a0c7df0d055435bf06b",
    )
    price_report = {
        "row_count": 871,
        "rows": [
            {
                "base_price": {"amount": "100.00"},
                "client_price": {"amount": "120.00"},
            }
        ],
    }
    recipe_json = {
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
        }
    }
    render_apply_result = {
        "application_status": "covers_stub_applied",
        "price_overlay": {"rows_applied": 400, "apply_rate": 0.45},
    }
    audit = build_baseline_audit(
        profile_key="fdl_wholesale_tariff",
        source=source,
        price_report=price_report,
        recipe_json=recipe_json,
        render_apply_result=render_apply_result,
    )
    assert audit is not None
    assert audit["mvp_gates_pass"] is True
    assert audit["phase2_preview_mvp_pass"] is False
    assert audit["phase2_exit_gate_pass"] is False
    assert audit["parity_track"] == "PHASE-2-PARITY"
    assert audit["gates"]["table_recompose"] is False


def test_baseline_audit_non_fdl_profile_returns_none():
    source = SimpleNamespace(page_count=10, sha256="abc")
    audit = build_baseline_audit(
        profile_key="other_profile",
        source=source,
        price_report={"row_count": 1, "rows": []},
        recipe_json={"pricing_policy": {}},
        render_apply_result=None,
    )
    assert audit is None
