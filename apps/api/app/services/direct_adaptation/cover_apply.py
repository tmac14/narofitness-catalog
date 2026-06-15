"""Merge main and section cover apply results."""

from __future__ import annotations

from typing import Any


def merge_cover_apply_results(main_result: dict[str, Any], section_result: dict[str, Any]) -> dict[str, Any]:
    section_covers = section_result.get("section_covers") or []
    sections_applied = int(section_result.get("sections_applied", 0))
    main_cover = main_result.get("main_cover") or {}
    main_method = main_cover.get("method")

    if sections_applied == 0:
        application_status = main_result.get("application_status", "pending")
    else:
        section_methods = {entry.get("method") for entry in section_covers}
        if main_method == "stub" and section_methods == {"stub"}:
            application_status = "covers_stub_applied"
        elif main_method == "asset" and section_methods == {"asset"}:
            application_status = "covers_applied"
        else:
            application_status = "covers_mixed_applied"

    return {
        "main_cover": main_cover,
        "section_covers": section_covers,
        "sections_applied": sections_applied,
        "application_status": application_status,
        "output_sha256": section_result.get("output_sha256") or main_result.get("output_sha256"),
    }
