"""Serialize audited import rows with full pipeline trace."""

from __future__ import annotations

from typing import Any

from app.services.import_audit.page_extraction import (
    PageExtraction,
    SourceSection,
    match_raw_line_index,
)
from app.services.import_parsers.base import ImportRow
from app.services.import_review import BLOCKING_REASONS, can_confirm_row


def _row_snapshot(row: ImportRow) -> dict[str, Any]:
    return {
        "sku": row.sku,
        "raw_name": row.raw_name,
        "normalized_name": row.normalized_name,
        "category_path": row.category_path,
        "mapped_category_slug": row.mapped_category_slug,
        "mapped_category_confidence": row.mapped_category_confidence,
        "master_key": row.master_key,
        "master_name": row.master_name,
        "grouping_reason": row.grouping_reason,
        "grouping_confidence": row.grouping_confidence,
        "parsed_variant_specs_raw": dict(row.parsed_variant_specs_raw or {}),
        "parsed_common_specs_raw": dict(row.parsed_common_specs_raw or {}),
        "review_reasons": list(row.review_reasons or []),
        "review_status": row.review_status,
        "import_action": row.import_action,
        "status": row.status.value,
    }


def _extract_raw_sku(raw_lines: list[str]) -> str | None:
    from app.services.import_parsers.fdl_pdf_v1 import SKU_RE

    for text in raw_lines:
        ts = text.strip()
        if SKU_RE.match(ts):
            return ts
    return None


def _infer_variant_axes(
    variant_specs: dict[str, Any],
    sku: str | None,
    grouping_config: dict[str, Any],
) -> list[str]:
    axes = list(variant_specs.keys())
    if axes:
        return axes

    if not sku:
        return []

    upper = sku.upper()
    length_prefixes = {"BN", "BO", "BOR"}
    for prefix in length_prefixes:
        if upper.startswith(prefix):
            return ["length_cm"]
    numeric_prefixes = grouping_config.get("numeric_suffix_family_prefixes") or (
        "DOP4A",
        "DOPH",
        "DNG",
        "DOP",
        "MPS",
        "MU",
        "MP",
    )
    for prefix in numeric_prefixes:
        if upper.startswith(prefix):
            return ["peso_kg"]
    attr_from_sku = grouping_config.get("attr_from_sku") or {}
    return list(attr_from_sku.keys())


def _raw_extraction_mode(raw_lines: list[str]) -> str:
    if len(raw_lines) == 1:
        return "inline"
    return "buffer"


def build_audited_row(
    row: ImportRow,
    *,
    source_section: SourceSection,
    grouping_strategy: str,
    grouping_config: dict[str, Any],
    page_extraction: PageExtraction | None = None,
    stage_snapshots: dict[str, dict[str, Any]] | None = None,
    failure_domain: str | None = None,
    suspicion_flags: list[str] | None = None,
    compact: bool = False,
) -> dict[str, Any]:
    review_reasons = list(row.review_reasons or [])
    blocking_reasons = [r for r in review_reasons if r in BLOCKING_REASONS]
    variant_specs = dict(row.parsed_variant_specs_raw or {})
    common_specs = dict(row.parsed_common_specs_raw or {})
    variant_axes = _infer_variant_axes(variant_specs, row.sku, grouping_config)
    raw_lines = list(row.raw_lines or [])
    raw_line_index = None
    if page_extraction is not None:
        raw_line_index = match_raw_line_index(raw_lines, page_extraction.lines)

    can_confirm, confirm_gate = can_confirm_row(row, allow_needs_review=False)

    audited: dict[str, Any] = {
        "page_number": row.page_number,
        "source_row_index": row.row_index,
        "source_section": source_section.to_dict(),
        "raw_lines": raw_lines,
        "raw_line_index": raw_line_index,
        "raw_extraction_mode": _raw_extraction_mode(raw_lines),
        "raw_sku": _extract_raw_sku(raw_lines),
        "normalized_sku": row.sku,
        "raw_name": row.raw_name or row.name,
        "normalized_name": row.normalized_name or row.name,
        "price": str(row.price_amount) if row.price_amount is not None else None,
        "inferred_attributes": {
            "variant_specs": variant_specs,
            "common_specs": common_specs,
            "variant_axes": variant_axes,
        },
        "source_taxonomy_path": row.category_path,
        "canonical_category": {
            "slug": row.mapped_category_slug,
            "id": str(row.mapped_category_id) if row.mapped_category_id else None,
            "confidence": (
                float(row.mapped_category_confidence)
                if row.mapped_category_confidence is not None
                else None
            ),
        },
        "grouping_strategy": grouping_strategy,
        "grouping_reason": row.grouping_reason,
        "proposed_master_key": row.master_key,
        "variant_axes": variant_axes,
        "review_reasons": review_reasons,
        "blocking_reasons": blocking_reasons,
        "final_decision": {
            "parser_status": row.status.value,
            "review_status": row.review_status,
            "import_action": row.import_action,
            "can_confirm": can_confirm,
            "confirm_gate": confirm_gate,
        },
        "failure_domain": failure_domain,
        "suspicion_flags": list(suspicion_flags or []),
    }

    if not compact and stage_snapshots:
        audited["stage_snapshots"] = stage_snapshots

    return audited


def capture_stage_snapshots(
    rows_by_index: dict[int, ImportRow],
    stage_name: str,
    store: dict[int, dict[str, dict[str, Any]]],
) -> None:
    for idx, row in rows_by_index.items():
        store.setdefault(idx, {})[stage_name] = _row_snapshot(row)
