"""JSON and Markdown report writers for page import audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def page_audit_dir(output_base: Path, page_number: int) -> Path:

    return output_base / "audit" / "pages" / f"{page_number:03d}"


def host_output_dir_for_page(page_number: int) -> str:

    return f"temp/audit/pages/{page_number:03d}"


def write_json_artifact(payload: Any, output_path: Path) -> None:

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_page_import_json(payload: dict[str, Any], output_path: Path) -> None:

    write_json_artifact(payload, output_path)


def write_page_audit_bundle(
    report: dict[str, Any],
    page_dir: Path,
    *,
    write_format: str = "both",
) -> dict[str, str]:
    """Write all per-page audit artifacts into page_dir."""

    page_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}

    main_json = page_dir / "page_import_audit.json"

    write_page_import_json(report, main_json)

    written["page_import_audit.json"] = str(main_json)

    if write_format in ("md", "both"):
        md_path = page_dir / "page_import_audit.md"

        write_page_import_markdown(report, md_path)

        written["page_import_audit.md"] = str(md_path)

    artifacts: list[tuple[str, Any]] = [
        ("category_snapshot_before.json", report.get("category_snapshot_before") or {}),
        ("category_snapshot_after.json", report.get("category_snapshot_after") or {}),
        ("db_snapshot_after.json", report.get("db_after") or {}),
        ("raw_extraction.json", report.get("raw_extraction") or {}),
        ("parsed_rows.json", report.get("parsed_rows") or []),
        ("imported_products.json", report.get("products_visible_in_app") or []),
        ("blocked_rows.json", report.get("blocked_rows_detail") or []),
    ]

    for filename, payload in artifacts:
        path = page_dir / filename

        write_json_artifact(payload, path)

        written[filename] = str(path)

    return written


def write_page_import_markdown(payload: dict[str, Any], output_path: Path) -> None:

    lines: list[str] = []

    page = payload.get("requested_page") or payload.get("page_number")

    lines.append(f"# Page Import Audit — Page {page}")

    lines.append("")

    lines.append(f"**Output dir:** `{payload.get('output_dir')}`")

    lines.append(f"**PDF:** `{payload.get('pdf_path')}`")

    lines.append(f"**Generated:** {payload.get('generated_at')}")

    lines.append(f"**Workflow:** {payload.get('workflow_mode', 'manual_page_by_page')}")

    lines.append(f"**Status:** `{payload.get('status', 'unknown')}`")

    lines.append(f"**Confirm executed:** `{payload.get('confirm_executed')}`")

    lines.append(f"**Cumulative mode:** `{payload.get('cumulative_mode', False)}`")

    lines.append("")

    lines.append("## Workflow Contract")

    lines.append(f"- Requested page: **{payload.get('requested_page')}**")

    lines.append(f"- Reset before page: **{payload.get('reset_before_page')}**")

    lines.append(f"- Imported pages: `{payload.get('imported_pages')}`")

    full = payload.get("parsed_full_pdf") or {}

    filtered = payload.get("rows_filtered_to_page") or {}

    lines.append(
        f"- Full PDF parsed: **{full.get('total_rows_parsed')}** rows across "
        f"**{full.get('total_pages_with_rows')}** pages (`{full.get('parse_scope')}`)"
    )

    lines.append(f"- Rows filtered to page {page}: **{filtered.get('count')}**")

    lines.append(
        f"- DB contains only scoped page products: "
        f"**{payload.get('db_after_contains_only_requested_page_products')}**"
    )

    lines.append(
        f"- Products visible in app: **{payload.get('products_visible_in_app_count', 0)}**"
    )

    lines.append("")

    visual = payload.get("app_visual_check") or {}

    lines.append("## App Visual Check")

    lines.append(
        f"- Should show only page {page} products: "
        f"**{visual.get('products_page_should_show_only_requested_page')}**"
    )

    lines.append(
        f"- Expected visible: **{visual.get('expected_visible_products_count')}** | "
        f"Actual visible: **{visual.get('actual_visible_products_count')}**"
    )

    lines.append(f"- Visible SKUs: `{visual.get('visible_skus')}`")

    lines.append(f"- Visible categories: `{visual.get('visible_categories')}`")

    lines.append(f"- {visual.get('note', '')}")

    lines.append("")

    reset = payload.get("reset_summary") or {}

    lines.append("## Reset Summary")

    lines.append(
        f"- Masters before/after: {reset.get('product_masters_count_before')} → "
        f"{reset.get('product_masters_count_after')}"
    )

    lines.append(
        f"- Variants before/after: {reset.get('product_variants_count_before')} → "
        f"{reset.get('product_variants_count_after')}"
    )

    lines.append(f"- Categories preserved: {reset.get('categories_preserved')}")

    lines.append(f"- Mapping rules preserved: {reset.get('taxonomy_mapping_rules_preserved')}")

    lines.append("")

    lines.append("## Summary")

    lines.append(f"- Products imported: {len(payload.get('products_imported') or [])}")

    lines.append(f"- Products blocked: {len(payload.get('products_blocked') or [])}")

    not_imported = payload.get("products_expected_but_not_imported") or []

    lines.append(f"- Expected but not imported: {len(not_imported)}")

    lines.append("")

    unexpected_skus = payload.get("unexpected_skus_from_other_pages") or []

    if unexpected_skus:
        lines.append("## Cross-Page Contamination")

        for item in unexpected_skus:
            lines.append(
                f"- **{item.get('sku')}** (PDF page {item.get('source_page_in_full_pdf')}, "
                f"requested {item.get('requested_page')})"
            )

        lines.append("")

    for section_key, title in (
        ("category_warnings", "Category Warnings"),
        ("grouping_warnings", "Grouping Warnings"),
        ("review_gate_warnings", "Review Gate Warnings"),
    ):
        section = payload.get(section_key) or []

        if section:
            lines.append(f"## {title}")

            for w in section:
                lines.append(f"- **{w.get('code')}** ({w.get('sku')}): {w.get('detail')}")

            lines.append("")

    if payload.get("fail_reasons"):
        lines.append("## Fail Reasons")

        for reason in payload["fail_reasons"]:
            lines.append(f"- {reason}")

        lines.append("")

    parsed = payload.get("parsed_rows") or []

    db_after = payload.get("db_after") or {}

    variants = db_after.get("variants") or []

    lines.append("## Parsed Rows (page-filtered)")

    lines.append("| SKU | Parser | Source Path |")

    lines.append("|-----|--------|-------------|")

    for r in parsed:
        lines.append(
            f"| {r.get('normalized_sku')} | {r.get('parser_status')} | {r.get('source_taxonomy_path')} |"
        )

    lines.append("")

    lines.append("## Preview Decisions")

    lines.append("| SKU | Category | Grouping | can_confirm | Gate |")

    lines.append("|-----|----------|----------|-------------|------|")

    for prev in payload.get("preview_decision") or []:
        tax = prev.get("taxonomy") or {}

        grp = prev.get("grouping") or {}

        rev = prev.get("review") or {}

        lines.append(
            f"| {prev.get('normalized_sku')} | {tax.get('canonical_category_slug')} | "
            f"{grp.get('grouping_reason')} | {rev.get('can_confirm')} | {rev.get('confirm_gate') or '-'} |"
        )

    lines.append("")

    if not_imported:
        lines.append("## Blocked / Not Imported")

        for item in not_imported:
            lines.append(
                f"- **{item.get('sku')}**: gate={item.get('confirm_gate')}, "
                f"blocking={item.get('blocking_reasons')}, grouping={item.get('grouping_reason')}"
            )

        lines.append("")

    if variants:
        lines.append("## DB After (full supplier catalog — must be page-only)")

        lines.append("| SKU | Master Key | Category | Price |")

        lines.append("|-----|------------|----------|-------|")

        for v in variants:
            lines.append(
                f"| {v.get('variant_sku')} | {v.get('product_master_sku')} | "
                f"{v.get('category_slug')} | {v.get('price')} |"
            )

        lines.append("")

    lines.append("## Artifact Files")

    for name in (
        "page_import_audit.json",
        "page_import_audit.md",
        "category_snapshot_before.json",
        "category_snapshot_after.json",
        "db_snapshot_after.json",
        "raw_extraction.json",
        "parsed_rows.json",
        "imported_products.json",
        "blocked_rows.json",
    ):
        lines.append(f"- `{payload.get('output_dir')}/{name}`")

    lines.append("")

    approval = payload.get("manual_approval") or {}

    lines.append("## Manual Approval")

    lines.append(f"- Page approved by user: **{approval.get('page_approved', False)}**")

    lines.append(f"- {approval.get('note', '')}")

    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text("\n".join(lines), encoding="utf-8")
