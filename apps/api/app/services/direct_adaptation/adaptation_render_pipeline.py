"""Shared FDL direct adaptation render pipeline with output profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.entities import SourceDocument
from app.services.direct_adaptation.cover_page_layout import apply_cover_page_layout
from app.services.direct_adaptation.image_recompose import apply_image_recompose
from app.services.direct_adaptation.main_cover_replace import apply_main_cover_replace
from app.services.direct_adaptation.output_delivery import (
    OUTPUT_PROFILE_ARCHIVE,
    ResolvedOutputDelivery,
)
from app.services.direct_adaptation.pdf_encode import apply_output_profile_encode
from app.services.direct_adaptation.price_overlay import apply_price_overlay
from app.services.direct_adaptation.section_cover_replace import apply_section_cover_replace
from app.services.direct_adaptation.table_recompose import apply_table_recompose
from app.services.direct_adaptation.table_typography_redraw import apply_table_typography_redraw
from app.services.direct_adaptation.cover_apply import merge_cover_apply_results


def render_fdl_adaptation_pdf(
    *,
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    project_name: str,
    source: SourceDocument,
    snapshot_json: dict[str, Any] | None,
    output_delivery: ResolvedOutputDelivery,
    extra_asset_roots: list[Path] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    layout_output, layout_result = apply_cover_page_layout(pdf_bytes, recipe_json)
    main_output, main_result = apply_main_cover_replace(
        layout_output,
        recipe_json,
        project_name=project_name,
        extra_asset_roots=extra_asset_roots,
    )
    section_output, section_result = apply_section_cover_replace(
        main_output,
        recipe_json,
        extra_asset_roots=extra_asset_roots,
    )
    render_result = merge_cover_apply_results(main_result, section_result)
    render_result["cover_page_layout"] = layout_result
    output = section_output

    if snapshot_json is not None:
        output, price_result = apply_price_overlay(output, snapshot_json, recipe_json)
        render_result["price_overlay"] = price_result
        output, image_result = apply_image_recompose(
            output,
            recipe_json,
            snapshot_json=snapshot_json,
        )
        render_result["image_recompose"] = image_result
        output, table_result = apply_table_recompose(
            output,
            recipe_json,
            project_name=project_name,
            snapshot_json=snapshot_json,
            price_rects_by_page=price_result.get("price_rects_by_page"),
        )
        render_result["table_recompose"] = table_result
        if output_delivery.output_profile == OUTPUT_PROFILE_ARCHIVE:
            output, typography_result = apply_table_typography_redraw(
                output,
                recipe_json,
                snapshot_json=snapshot_json,
            )
            render_result["table_typography_redraw"] = typography_result

    pre_encode_bytes = len(output)
    output, encode_metrics = apply_output_profile_encode(
        output,
        output_profile=output_delivery.output_profile,
        email_budget_bytes=output_delivery.email_budget_bytes,
        archive_soft_warn_bytes=output_delivery.archive_soft_warn_bytes,
    )
    render_result["encode"] = encode_metrics
    render_result["pre_encode_byte_length"] = pre_encode_bytes
    render_result["output_delivery"] = {
        "profile": output_delivery.output_profile,
        "delivery_mode": output_delivery.delivery_mode,
        "encode_pass": encode_metrics.get("encode_pass"),
        "byte_length": encode_metrics.get("byte_length"),
        "within_budget": encode_metrics.get("within_budget"),
    }
    return output, render_result
