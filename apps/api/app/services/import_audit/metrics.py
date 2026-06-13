"""Aggregate metrics for variant detection audit reports."""

from __future__ import annotations

from collections import Counter
from typing import Any

ONE_PER_SKU_PREFIXES = ("one_per_sku", "explicit_one_per_sku")


def compute_metrics(
    *,
    total_pages: int,
    pages_in_filter: int,
    all_audited_rows: list[dict[str, Any]],
    filtered_audited_rows: list[dict[str, Any]],
    groups_detected: list[dict[str, Any]],
    suspicious_candidates: list[dict[str, Any]],
    failure_classifications: dict[str, list[Any]],
) -> dict[str, Any]:
    def _row_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
        with_sku = sum(1 for r in rows if r.get("normalized_sku"))
        with_price = sum(1 for r in rows if r.get("price"))
        blocked = sum(
            1
            for r in rows
            if not (r.get("final_decision") or {}).get("can_confirm")
            and (r.get("final_decision") or {}).get("confirm_gate")
            in ("blocking_reason", "needs_review_blocked")
        )
        needs_review = sum(
            1
            for r in rows
            if (r.get("final_decision") or {}).get("review_status") == "needs_review"
        )
        one_per_sku = sum(
            1
            for r in rows
            if (r.get("grouping_reason") or "").startswith(ONE_PER_SKU_PREFIXES)
            or r.get("grouping_reason") == "one_per_sku_fallback"
        )
        unmapped = sum(1 for r in rows if "unmapped_category" in (r.get("review_reasons") or []))
        return {
            "rows_extracted": len(rows),
            "rows_with_sku": with_sku,
            "rows_without_sku": len(rows) - with_sku,
            "rows_with_price": with_price,
            "one_per_sku_rows": one_per_sku,
            "blocked_rows": blocked,
            "needs_review_rows": needs_review,
            "unmapped_categories": unmapped,
        }

    full_stats = _row_stats(all_audited_rows)
    filtered_stats = _row_stats(filtered_audited_rows)

    heuristic_counter = Counter(c.get("heuristic") for c in suspicious_candidates)
    false_negatives = sum(1 for c in suspicious_candidates if c.get("possible_false_negative"))

    domain_counts = {k: len(v) for k, v in failure_classifications.items()}

    return {
        "total_pages_analyzed": total_pages,
        "total_pages_in_filter": pages_in_filter,
        "rows_extracted": full_stats["rows_extracted"],
        "rows_in_filter": filtered_stats["rows_extracted"],
        "rows_with_sku": full_stats["rows_with_sku"],
        "rows_without_sku": full_stats["rows_without_sku"],
        "rows_with_price": full_stats["rows_with_price"],
        "detected_groups": len(groups_detected),
        "one_per_sku_rows": full_stats["one_per_sku_rows"],
        "blocked_rows": full_stats["blocked_rows"],
        "needs_review_rows": full_stats["needs_review_rows"],
        "unmapped_categories": full_stats["unmapped_categories"],
        "suspicious_variant_candidates": len(suspicious_candidates),
        "possible_false_negatives": false_negatives,
        "failure_domain_counts": domain_counts,
        "top_suspicion_heuristics": heuristic_counter.most_common(10),
        "filtered": filtered_stats,
    }
