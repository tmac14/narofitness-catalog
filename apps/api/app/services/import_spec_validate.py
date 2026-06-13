"""Validate parsed spec keys against the active spec definition vocabulary."""

from __future__ import annotations

from typing import Any

from app.services.import_review import append_reason
from app.services.spec_writer import (
    load_spec_definitions,
    preview_color_enum_warning,
    preview_spec_hard_errors,
)


def _apply_spec_validation_errors(row: Any, errors: list[str]) -> None:
    if not errors:
        return
    if any(err.startswith("unknown spec key") for err in errors):
        append_reason(row, "unknown_spec_key")
    else:
        append_reason(row, "spec_validation_failed")
    if hasattr(row, "review_status"):
        row.review_status = "needs_review"


async def validate_parsed_specs(session, row: Any) -> list[str]:
    """Return hard spec validation errors for a staged/parser row."""
    definitions = await load_spec_definitions(session)
    errors = preview_spec_hard_errors(
        definitions,
        common_specs=getattr(row, "parsed_common_specs_raw", None) or {},
        variant_specs=getattr(row, "parsed_variant_specs_raw", None) or {},
    )
    _apply_spec_validation_errors(row, errors)

    for bucket in (
        getattr(row, "parsed_common_specs_raw", None) or {},
        getattr(row, "parsed_variant_specs_raw", None) or {},
    ):
        warning = preview_color_enum_warning(definitions, bucket.get("color"))
        if warning:
            append_reason(row, warning)

    return errors


async def validate_parsed_specs_batch(session, rows: list[Any]) -> dict[int, list[str]]:
    definitions = await load_spec_definitions(session)
    out: dict[int, list[str]] = {}

    for row in rows:
        errors = preview_spec_hard_errors(
            definitions,
            common_specs=getattr(row, "parsed_common_specs_raw", None) or {},
            variant_specs=getattr(row, "parsed_variant_specs_raw", None) or {},
        )
        if errors:
            _apply_spec_validation_errors(row, errors)
            index = getattr(row, "source_row_index", getattr(row, "row_index", 0))
            out[index] = errors

        for bucket in (
            getattr(row, "parsed_common_specs_raw", None) or {},
            getattr(row, "parsed_variant_specs_raw", None) or {},
        ):
            warning = preview_color_enum_warning(definitions, bucket.get("color"))
            if warning:
                append_reason(row, warning)

    return out
