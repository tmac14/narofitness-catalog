"""Review status and confirm gates for non-blocking warnings (COLOR-1 gate)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import (
    can_confirm_row,
    has_blocking_reasons,
    is_blocking_reason,
    resolve_review_status,
)


def _row(*, review_reasons: list[str], review_status: str | None = None) -> ImportRow:
    row = ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku="BOC004",
        name="Barra 2,20 Mts - 20 kgs - 6 Rod - 1500 lbs Agarre 28 mm NEGRA",
        brand="Sin marca",
        ean=None,
        category_path="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
        price_amount=Decimal("172.21"),
        review_reasons=list(review_reasons),
    )
    if review_status is not None:
        row.review_status = review_status
    return row


def test_unknown_color_review_reason_is_not_blocking():
    assert not is_blocking_reason("unknown_color_value:NEGRA")
    assert not has_blocking_reasons(_row(review_reasons=["unknown_color_value:NEGRA"]))


def test_resolve_review_status_pending_for_only_unknown_color():
    row = _row(review_reasons=["unknown_color_value:NEGRA"])
    assert resolve_review_status(row) == "pending"


def test_can_confirm_row_allows_only_unknown_color_without_override():
    row = _row(review_reasons=["unknown_color_value:NEGRA"])
    row.review_status = resolve_review_status(row)
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate
    assert gate is None


def test_can_confirm_row_allows_needs_review_when_only_non_blocking_warnings():
    row = _row(review_reasons=["unknown_color_value:Azul Petróleo"], review_status="needs_review")
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate
    assert gate is None


def test_can_confirm_row_still_blocks_real_blocking_reasons():
    row = _row(review_reasons=["false_family_pattern", "low_grouping_confidence"])
    row.review_status = resolve_review_status(row)
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert not ok
    assert gate == "needs_review_blocked"


def test_safe_one_per_sku_fallback_reasons_are_non_blocking_when_mapped():
    row = ImportRow(
        row_index=0,
        status=RowStatus.REVISAR,
        sku="REM002",
        name="Remo producto",
        normalized_name="Remo producto",
        brand="FDL",
        ean=None,
        category_path="CARDIO",
        price_amount=Decimal("100"),
        grouping_reason="one_per_sku_fallback",
        mapped_category_id=uuid4(),
        mapped_category_confidence=1.0,
        review_reasons=["regex_fallback_1_1", "low_grouping_confidence"],
        review_status="needs_review",
    )
    assert not has_blocking_reasons(row)
    ok, gate = can_confirm_row(row)
    assert ok, gate
