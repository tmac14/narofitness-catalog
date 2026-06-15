"""Tests for Phase 2C FDL direct adaptation price report renderer."""

from __future__ import annotations

from decimal import Decimal

from app.services.direct_adaptation.fdl_direct_v1 import build_price_report
from app.services.direct_adaptation.price_transform import apply_pricing_policy


def test_apply_pricing_policy_multiply_120():
    policy = {
        "operation": "multiply",
        "factor": "1.20",
        "rounding": "ROUND_HALF_UP",
        "scale": 2,
        "currency": "EUR",
    }
    assert apply_pricing_policy(Decimal("100.00"), policy) == Decimal("120.00")
    assert apply_pricing_policy(Decimal("112.20"), policy) == Decimal("134.64")


def test_build_price_report_from_snapshot_rows():
    snapshot_json = {
        "pages": [
            {
                "page_number": 3,
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "reference": "SKU1",
                                "ean": "123",
                                "base_price": {"amount": "100.00", "currency": "EUR"},
                            },
                            {
                                "stable_row_id": "row_2",
                                "reference": "SKU2",
                                "base_price": {"amount": "50.00", "currency": "EUR"},
                            },
                        ]
                    }
                ],
            }
        ]
    }
    recipe_json = {
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
            "currency": "EUR",
        }
    }
    report = build_price_report(snapshot_json, recipe_json)
    assert report["row_count"] == 2
    assert report["rows"][0]["client_price"]["amount"] == "120.00"
    assert report["rows"][1]["client_price"]["amount"] == "60.00"
