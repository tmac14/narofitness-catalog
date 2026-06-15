"""Cover plan manifest section from recipe data."""

from __future__ import annotations

from typing import Any

from app.services.direct_adaptation.cover_assets import resolve_cover_asset


def build_cover_plan(
    recipe_json: dict[str, Any],
    *,
    cover_apply_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    covers = recipe_json.get("covers") or {}
    main = covers.get("main")
    sections = covers.get("sections") or []
    entries: list[dict[str, Any]] = []
    main_apply = (cover_apply_result or {}).get("main_cover") if cover_apply_result else None
    section_apply_by_key = {
        entry.get("section_key"): entry
        for entry in (cover_apply_result or {}).get("section_covers", [])
        if entry.get("section_key")
    }
    if isinstance(main, dict):
        entries.append(
            {
                "role": "main",
                "page_number": main.get("page_number"),
                "asset_path": main.get("asset_path"),
                "asset_sha256": main.get("asset_sha256"),
                "asset_status": _asset_status(main.get("asset_path")),
                "application_status": main_apply.get("status") if main_apply else "pending",
                "application_method": main_apply.get("method") if main_apply else None,
            }
        )
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_key = section.get("section_key")
        section_apply = section_apply_by_key.get(section_key)
        entries.append(
            {
                "role": "section",
                "section_key": section_key,
                "page_number": section.get("page_number"),
                "asset_path": section.get("asset_path"),
                "asset_sha256": section.get("asset_sha256"),
                "asset_status": _asset_status(section.get("asset_path")),
                "application_status": section_apply.get("status") if section_apply else "pending",
                "application_method": section_apply.get("method") if section_apply else None,
            }
        )
    application_status = "pending"
    note = "Cover plan recorded; table recompose deferred"
    if cover_apply_result:
        application_status = cover_apply_result.get("application_status", "pending")
        sections_applied = cover_apply_result.get("sections_applied", 0)
        if sections_applied:
            note = (
                f"Main + {sections_applied} section covers applied "
                f"({application_status}); table recompose deferred"
            )
        else:
            main_method = (main_apply or {}).get("method")
            note = f"Main cover applied via {main_method}; section covers pending"
    return {
        "render_mode": covers.get("render_mode", "full_bleed"),
        "entry_count": len(entries),
        "entries": entries,
        "application_status": application_status,
        "sections_applied": (cover_apply_result or {}).get("sections_applied", 0),
        "note": note,
    }


def _asset_status(asset_path: object) -> str:
    if not asset_path:
        return "missing"
    if resolve_cover_asset(str(asset_path)) is not None:
        return "resolved"
    return "referenced_not_bundled"
