"""JSON, Markdown and console report emitters for variant detection audit."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_report_payload(
    *,
    pdf_path: Path,
    total_pages: int,
    page_filter: dict[str, Any],
    profile_meta: dict[str, Any],
    metrics: dict[str, Any],
    groups_detected: list[dict[str, Any]],
    suspicious_candidates: list[dict[str, Any]],
    failure_classifications: dict[str, list[Any]],
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "audit_version": "1.0",
        "agent": "agent5",
        "generated_at": datetime.now(UTC).isoformat(),
        "pdf": {
            "path": str(pdf_path),
            "total_pages": total_pages,
            "filter": page_filter,
        },
        "profile": profile_meta,
        "metrics": metrics,
        "groups_detected": groups_detected,
        "suspicious_variant_candidates": suspicious_candidates,
        "failure_classifications": failure_classifications,
        "pages": pages,
    }


def write_json_report(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown_report(payload: dict[str, Any], output_path: Path) -> None:
    lines: list[str] = []
    metrics = payload.get("metrics") or {}
    pdf = payload.get("pdf") or {}
    filt = pdf.get("filter") or {}

    lines.append("# Variant Detection Audit Report")
    lines.append("")
    lines.append(f"**Generated:** {payload.get('generated_at')}")
    lines.append(f"**PDF:** `{pdf.get('path')}`")
    lines.append(f"**Filter:** `{filt.get('mode', 'all')}`")
    lines.append("")

    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for key in (
        "total_pages_analyzed",
        "total_pages_in_filter",
        "rows_extracted",
        "rows_in_filter",
        "suspicious_variant_candidates",
        "possible_false_negatives",
        "detected_groups",
        "blocked_rows",
        "needs_review_rows",
    ):
        lines.append(f"| {key} | {metrics.get(key, 0)} |")
    lines.append("")

    domain_counts = metrics.get("failure_domain_counts") or {}
    if domain_counts:
        lines.append("### Failure Domains")
        lines.append("")
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            if count:
                lines.append(f"- **{domain}**: {count}")
        lines.append("")

    suspicious = payload.get("suspicious_variant_candidates") or []
    if suspicious:
        lines.append("## Suspicious Variant Candidates")
        lines.append("")
        lines.append("| ID | Heuristic | Pages | SKUs | Expected Master |")
        lines.append("|----|-----------|-------|------|-----------------|")
        for c in suspicious[:30]:
            skus = ", ".join((c.get("skus") or [])[:4])
            pages = ", ".join(str(p) for p in (c.get("page_numbers") or [])[:3])
            lines.append(
                f"| {c.get('suspicion_id')} | {c.get('heuristic')} | {pages} | {skus} | {c.get('expected_master_key')} |"
            )
        lines.append("")

    groups = payload.get("groups_detected") or []
    if groups:
        lines.append("## Detected Groups")
        lines.append("")
        for g in groups[:20]:
            skus = ", ".join((g.get("skus") or [])[:6])
            lines.append(
                f"- **{g.get('proposed_master_key')}** ({g.get('member_count')} members): {skus}"
            )
        lines.append("")

    for page in payload.get("pages") or []:
        pn = page.get("page_number")
        lines.append(f"## Page {pn}")
        section = page.get("source_section") or {}
        lines.append(
            f"Section: {section.get('category_main')} > {section.get('category_sub')} "
            f"(brand: {section.get('section_brand')})"
        )
        lines.append("")

        orphans = page.get("unparsed_candidates") or []
        if orphans:
            lines.append("### Unparsed Candidates")
            for o in orphans[:10]:
                lines.append(
                    f"- [{o.get('line_index')}] {o.get('reason')}: `{o.get('text', '')[:80]}`"
                )
            lines.append("")

        rows = page.get("rows") or []
        if rows:
            lines.append("### Audited Rows")
            lines.append("")
            lines.append("| SKU | Master Key | Grouping Reason | Failure Domain | Blocking |")
            lines.append("|-----|------------|-----------------|----------------|----------|")
            for r in rows:
                blocking = ", ".join(r.get("blocking_reasons") or []) or "-"
                lines.append(
                    f"| {r.get('normalized_sku')} | {r.get('proposed_master_key')} | "
                    f"{r.get('grouping_reason')} | {r.get('failure_domain') or '-'} | {blocking} |"
                )
            lines.append("")

    failures = payload.get("failure_classifications") or {}
    lines.append("## Failure Classifications (samples)")
    lines.append("")
    for domain, items in failures.items():
        if not items:
            continue
        lines.append(f"### {domain} ({len(items)})")
        for item in items[:10]:
            lines.append(
                f"- p.{item.get('page_number')} sku={item.get('sku')} "
                f"reason={item.get('grouping_reason')}"
            )
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_console_summary(payload: dict[str, Any], *, report_path: Path | None = None) -> None:
    metrics = payload.get("metrics") or {}
    pdf = payload.get("pdf") or {}
    filt = pdf.get("filter") or {}

    filter_desc = filt.get("mode", "all")
    if filt.get("mode") == "single":
        filter_desc = f"page {filt.get('page')}"
    elif filt.get("mode") == "range":
        filter_desc = f"{filt.get('from')}-{filt.get('to')}"
    elif filt.get("mode") == "list":
        filter_desc = str(filt.get("pages"))

    print("Variant Detection Audit — FDL PDF")
    print(
        f"Pages analyzed: {metrics.get('total_pages_in_filter')} "
        f"(filter {filter_desc}) | "
        f"Rows: {metrics.get('rows_in_filter')} | "
        f"Suspicious: {metrics.get('suspicious_variant_candidates')} | "
        f"Possible FN: {metrics.get('possible_false_negatives')}"
    )
    domain_counts = metrics.get("failure_domain_counts") or {}
    print(
        "Extraction: {extraction} | Normalization: {norm} | Taxonomy: {tax} | "
        "Grouping: {grp} | Gate OK: {gate} | False+: {vis}".format(
            extraction=domain_counts.get("extraction_failure", 0),
            norm=domain_counts.get("normalization_failure", 0),
            tax=domain_counts.get("taxonomy_failure", 0),
            grp=domain_counts.get("grouping_failure", 0),
            gate=domain_counts.get("gate_correct_block", 0),
            vis=domain_counts.get("visual_false_positive", 0),
        )
    )
    if report_path:
        print(f"Report: {report_path}")
