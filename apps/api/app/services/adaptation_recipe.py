"""Default direct-adaptation recipe scaffolding."""

from __future__ import annotations

import hashlib
import json
from typing import Any

RECIPE_SCHEMA_VERSION = "direct-adaptation-recipe/v1"


def recipe_fingerprint(recipe_json: dict[str, Any]) -> str:
    canonical = json.dumps(recipe_json, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_default_recipe_v1(
    *,
    project_name: str,
    profile_key: str,
    profile_version: str,
    source_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": RECIPE_SCHEMA_VERSION,
        "profile": {
            "key": profile_key,
            "version": profile_version,
            "source_sha256": source_sha256,
        },
        "project": {"name": project_name},
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
            "currency": "EUR",
            "report_columns": ["reference", "base_price", "client_price"],
        },
        "presentation": {
            "brand_green": "#8dbb24",
            "price_background": "#f5f0e7",
            "table_border_width_points": 1.0,
            "image_cell_padding_points": 1.5,
            "section_start_ribbon": "rectangular_centered_first_content_page_only",
            "footer": {
                "section_label": True,
                "brand_line": "NAROFITNESS CATÁLOGO 2026",
                "compact_page_number": True,
            },
        },
        "covers": {
            "render_mode": "full_bleed",
            "main": {
                "page_number": 1,
                "asset_path": "wireframes/portadas-fdl/main/5.png",
                "asset_sha256": "d0cf29c0bbd478bab8b8a829a3fb7b919032d00a8a2dca89f218c35461efdc6a",
            },
            "sections": [
                {"page_number": 2, "section_key": "cardio", "asset_path": "wireframes/portadas-fdl/categorias/01-cardio.png", "asset_sha256": "cd62fd671a6c03950c2c37e86e397e70551bccd2a3b5c05e60dc83aeb4e68ec9"},
                {"page_number": 10, "section_key": "crosstraining", "asset_path": "wireframes/portadas-fdl/categorias/02-crosstraining.png", "asset_sha256": "b7dbccc37ac40f84795d35ab5448f4282e09e0b84e12dc0dc51fb1f70a877dc4"},
                {"page_number": 29, "section_key": "suelo", "asset_path": "wireframes/portadas-fdl/categorias/03-suelo.png", "asset_sha256": "e12b867668f4ad3f247fad8aef0c67915ace9ddbfeacd5ea982a8c8a8689986e"},
                {"page_number": 32, "section_key": "discos-y-barras", "asset_path": "wireframes/portadas-fdl/categorias/04-discos-y-barras.png", "asset_sha256": "c0a2917cb4cfe2f376302d5c09aa43be95344e1ea9e35619abd6edc3cf4ba74a"},
                {"page_number": 36, "section_key": "mancuernas", "asset_path": "wireframes/portadas-fdl/categorias/05-mancuernas.png", "asset_sha256": "c19bd8218b36a13e56254d5943f277868746a997f9273b1555e90d24422f7d24"},
                {"page_number": 42, "section_key": "material-de-estudio", "asset_path": "wireframes/portadas-fdl/categorias/06-material-de-estudio.png", "asset_sha256": "abf50fd346b0f9dc6750e5712e23a9a496dee4421122e914516bcff2704d6971"},
                {"page_number": 60, "section_key": "boxeo", "asset_path": "wireframes/portadas-fdl/categorias/07-boxeo.png", "asset_sha256": "5647ea9ae6a569d5544598447cf8e1a8d16b6738f3e0bce0b8cdf7f5e5a0c3ba"},
                {"page_number": 63, "section_key": "agarres", "asset_path": "wireframes/portadas-fdl/categorias/08-agarres.png", "asset_sha256": "983ad2019f5c0d3f9362065f76135ded3536522184781f503e6723bbc1539e08"},
            ],
        },
        "media_layout": {
            "preserve_source_association": True,
            "center_horizontal": True,
            "center_vertical": True,
            "shared_image_groups": True,
            "adaptive_multi_image_collage": True,
            "draw_cell_borders_after_images": True,
        },
        "image_recompose": {
            "method": "snapshot_image_group_v1",
            "scope": "product_content",
            "geometry_source": "snapshot_image_group_v1",
            "capabilities": ["snapshot_redraw", "adaptive_collage_v1"],
        },
        "price_overlay": {
            "method": "text_search_v1",
            "scope": "product_content",
            "geometry_source": "snapshot_bbox_v1",
        },
        "table_recompose": {
            "method": "presentation_chrome_v1",
            "scope": "product_content",
            "capabilities": ["footer", "price_cell_border", "row_cell_border"],
            "price_cell_border": {
                "method": "text_search_v1",
                "scope": "product_content",
            },
            "row_cell_border": {
                "method": "snapshot_row_bbox_v1",
                "scope": "product_content",
            },
        },
        "regression_pages": [3, 5, 6, 11, 12, 13, 14, 16, 21, 50, 51, 52, 64],
        "output_delivery": {
            "profile": "email_optimized",
            "delivery_mode": "persist",
            "ephemeral_ttl_seconds": 3600,
            "email_budget_bytes": 15 * 1024 * 1024,
            "archive_soft_warn_bytes": 50 * 1024 * 1024,
        },
    }
