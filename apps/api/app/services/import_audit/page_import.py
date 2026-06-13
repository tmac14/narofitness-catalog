"""Page-by-page import sandbox audit orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportProfile, Supplier
from app.services.import_audit.baseline import (
    build_reset_summary,
    capture_db_counts,
)
from app.services.import_audit.db_snapshot import (
    build_products_visible_in_app,
    export_category_snapshot,
    snapshot_all_supplier_products,
    snapshot_category_state,
)
from app.services.import_audit.page_extraction import (
    SourceSection,
    extract_pages,
    match_raw_line_index,
)
from app.services.import_audit.suspicious_variants import detect_suspicious_variants
from app.services.import_audit.taxonomy_trace import build_taxonomy_decision
from app.services.import_confirm import confirm_import
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import BLOCKING_REASONS, can_confirm_row, resolve_review_status
from app.services.import_spec_validate import validate_parsed_specs_batch
from app.services.import_staging import bulk_insert_rows, create_batch
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_reset import reset_catalog_data
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories


def _init_row_names(rows: list[ImportRow]) -> None:
    for row in rows:
        if not row.raw_name:
            row.raw_name = row.name
        if not row.normalized_name:
            row.normalized_name = row.name


def _raw_extraction_mode(raw_lines: list[str]) -> str:
    return "inline" if len(raw_lines) == 1 else "buffer"


def _extract_raw_sku(raw_lines: list[str]) -> str | None:
    from app.services.import_parsers.fdl_pdf_v1 import SKU_RE

    for text in raw_lines:
        ts = text.strip()
        if SKU_RE.match(ts):
            return ts
    return None


def _build_parsed_row(
    row: ImportRow,
    *,
    source_section: SourceSection,
    page_lines: list | None,
) -> dict[str, Any]:
    raw_line_index = None
    if page_lines:
        raw_line_index = match_raw_line_index(row.raw_lines or [], page_lines)
    return {
        "page_number": row.page_number,
        "source_row_index": row.row_index,
        "raw_line_index": raw_line_index,
        "raw_lines": list(row.raw_lines or []),
        "raw_sku": _extract_raw_sku(row.raw_lines or []),
        "normalized_sku": row.sku,
        "raw_name": row.raw_name or row.name,
        "normalized_name": row.normalized_name or row.name,
        "price": str(row.price_amount) if row.price_amount is not None else None,
        "source_taxonomy_path": row.category_path,
        "source_section": source_section.to_dict(),
        "parser_status": row.status.value,
    }


def _build_preview_decision(row: ImportRow, *, grouping_strategy: str) -> dict[str, Any]:
    review_reasons = list(row.review_reasons or [])
    blocking_reasons = [r for r in review_reasons if r in BLOCKING_REASONS]
    can_confirm, confirm_gate = can_confirm_row(row, allow_needs_review=False)
    variant_specs = dict(row.parsed_variant_specs_raw or {})

    return {
        "source_row_index": row.row_index,
        "normalized_sku": row.sku,
        "taxonomy": {
            "canonical_category_slug": row.mapped_category_slug,
            "canonical_category_id": str(row.mapped_category_id)
            if row.mapped_category_id
            else None,
            "confidence": (
                float(row.mapped_category_confidence)
                if row.mapped_category_confidence is not None
                else None
            ),
        },
        "grouping": {
            "grouping_strategy": grouping_strategy,
            "grouping_reason": row.grouping_reason,
            "grouping_confidence": row.grouping_confidence,
            "proposed_master_key": row.master_key,
            "variant_axes": list(variant_specs.keys()),
            "is_one_per_sku": (row.grouping_reason or "").startswith(
                ("one_per_sku", "explicit_one_per_sku")
            ),
            "is_grouped_variant": False,
        },
        "review": {
            "review_reasons": review_reasons,
            "blocking_reasons": blocking_reasons,
            "can_confirm": can_confirm,
            "confirm_gate": confirm_gate,
            "import_action": row.import_action,
            "review_status": row.review_status,
        },
    }


CATEGORY_WARNING_CODES = frozenset(
    {
        "category_not_in_seed",
        "category_created_from_pdf",
        "unmapped_category",
        "retired_repuesto_rule_still_active",
        "mapped_by_retired_sku_prefix",
        "category_mapping_drift",
        "cross_page_contamination",
    }
)
GROUPING_WARNING_CODES = frozenset(
    {
        "one_per_sku_fallback_blocked",
        "low_grouping_confidence",
        "regex_fallback_1_1",
        "incorrect_variant_grouping",
        "suspicious_variant_grouping",
    }
)
REVIEW_GATE_WARNING_CODES = frozenset(
    {
        "incorrect_1_1_blocked",
        "blocked_without_reason",
        "confirm_gate_blocked",
    }
)


def _build_sku_page_index(rows: list[ImportRow]) -> dict[str, int]:
    index: dict[str, int] = {}
    for row in rows:
        if row.sku and row.page_number is not None:
            index[row.sku.upper()] = row.page_number
    return index


def _split_warnings(warnings: list[dict[str, Any]]) -> tuple[list[dict], list[dict], list[dict]]:
    category: list[dict[str, Any]] = []
    grouping: list[dict[str, Any]] = []
    review_gate: list[dict[str, Any]] = []
    for warning in warnings:
        code = warning.get("code") or ""
        if code in CATEGORY_WARNING_CODES:
            category.append(warning)
        elif code in GROUPING_WARNING_CODES:
            grouping.append(warning)
        elif code in REVIEW_GATE_WARNING_CODES:
            review_gate.append(warning)
        else:
            grouping.append(warning)
    return category, grouping, review_gate


def _verify_page_isolation(
    *,
    all_db_skus: list[str],
    expected_skus: set[str],
    sku_to_page: dict[str, int],
    requested_page: int,
) -> tuple[bool, list[dict[str, Any]]]:
    unexpected: list[dict[str, Any]] = []
    for sku in sorted(all_db_skus):
        upper = sku.upper()
        if upper not in expected_skus:
            unexpected.append(
                {
                    "sku": sku,
                    "source_page_in_full_pdf": sku_to_page.get(upper),
                    "requested_page": requested_page,
                }
            )
    contains_only = len(unexpected) == 0
    return contains_only, unexpected


CRITICAL_CATEGORY_CODES = frozenset(
    {
        "retired_repuesto_rule_still_active",
        "mapped_by_retired_sku_prefix",
        "category_mapping_drift",
        "category_created_from_pdf",
        "cross_page_contamination",
    }
)
CRITICAL_GROUPING_CODES = frozenset({"one_per_sku_fallback_blocked"})


def _evaluate_page_status(
    *,
    do_confirm: bool,
    db_after_contains_only_requested_page_products: bool,
    unexpected_skus_from_other_pages: list[dict[str, Any]],
    unexpected_categories: list[str],
    products_expected_but_not_imported: list[dict[str, Any]],
    category_warnings: list[dict[str, Any]],
    grouping_warnings: list[dict[str, Any]],
    review_gate_warnings: list[dict[str, Any]],
    preview_decision: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    fail_reasons: list[str] = []

    if not db_after_contains_only_requested_page_products:
        fail_reasons.append("db_contains_products_from_other_pages")
    if unexpected_skus_from_other_pages:
        fail_reasons.append("unexpected_skus_from_other_pages")
        if "cross_page_contamination" not in fail_reasons:
            fail_reasons.append("cross_page_contamination")
    if unexpected_categories:
        fail_reasons.append("unexpected_categories_created")

    for warning in category_warnings:
        if warning.get("code") in CRITICAL_CATEGORY_CODES:
            fail_reasons.append(f"category:{warning.get('code')}")

    for warning in grouping_warnings:
        if warning.get("code") in CRITICAL_GROUPING_CODES:
            code = warning.get("code")
            if f"grouping:{code}" not in fail_reasons:
                fail_reasons.append(f"grouping:{code}")

    for warning in review_gate_warnings:
        if warning.get("code") == "incorrect_1_1_blocked":
            fail_reasons.append("incorrect_1_1_blocked")

    if do_confirm:
        for item in products_expected_but_not_imported:
            if item.get("can_confirm"):
                fail_reasons.append("importable_product_not_imported")
                break

    for prev in preview_decision:
        grouping = prev.get("grouping") or {}
        review = prev.get("review") or {}
        if (
            grouping.get("grouping_reason") == "explicit_one_per_sku"
            and not review.get("can_confirm")
            and "incorrect_1_1_blocked" not in fail_reasons
        ):
            fail_reasons.append("incorrect_1_1_blocked")

    return ("pass" if not fail_reasons else "fail"), fail_reasons


def _build_warnings(
    *,
    taxonomy_rows: list[dict[str, Any]],
    preview_rows: list[dict[str, Any]],
    unexpected_categories: list[str],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    seen_codes: set[str] = set()

    def add(code: str, sku: str | None, detail: str) -> None:
        key = f"{code}:{sku}"
        if key in seen_codes:
            return
        seen_codes.add(key)
        warnings.append({"code": code, "sku": sku, "detail": detail})

    for tax in taxonomy_rows:
        sku = tax.get("normalized_sku")
        for code in tax.get("warnings") or []:
            add(code, sku, f"Taxonomy warning for {sku}")
        if tax.get("warning_if_category_not_in_seed"):
            add("category_not_in_seed", sku, tax["warning_if_category_not_in_seed"])

    for prev in preview_rows:
        sku = prev.get("normalized_sku")
        grouping = prev.get("grouping") or {}
        review = prev.get("review") or {}
        if grouping.get("grouping_reason") == "one_per_sku_fallback":
            add(
                "one_per_sku_fallback_blocked",
                sku,
                str(grouping.get("grouping_reason") or ""),
            )
        if "low_grouping_confidence" in (review.get("blocking_reasons") or []):
            add("low_grouping_confidence", sku, "below confidence threshold")
        if "regex_fallback_1_1" in (review.get("blocking_reasons") or []):
            add("regex_fallback_1_1", sku, "regex family fallback")
        if "unmapped_category" in (review.get("review_reasons") or []):
            add("unmapped_category", sku, "no mapping rule matched")
        if grouping.get("grouping_reason") == "explicit_one_per_sku" and not review.get(
            "can_confirm"
        ):
            add("incorrect_1_1_blocked", sku, "explicit 1:1 master blocked at review gate")
        if not review.get("can_confirm") and review.get("confirm_gate"):
            add("confirm_gate_blocked", sku, str(review.get("confirm_gate")))

    for slug in unexpected_categories:
        add("category_created_from_pdf", None, slug)

    return warnings


def _expected_skus_for_pages(all_rows: list[ImportRow], pages: list[int]) -> set[str]:
    page_set = set(pages)
    return {r.sku.upper() for r in all_rows if r.sku and (r.page_number or 0) in page_set}


def _build_blocked_rows_detail(preview_decision: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    for prev in preview_decision:
        review = prev.get("review") or {}
        if review.get("can_confirm"):
            continue
        blocked.append(
            {
                "sku": prev.get("normalized_sku"),
                "source_row_index": prev.get("source_row_index"),
                "confirm_gate": review.get("confirm_gate"),
                "blocking_reasons": review.get("blocking_reasons"),
                "review_reasons": review.get("review_reasons"),
                "grouping_reason": (prev.get("grouping") or {}).get("grouping_reason"),
            }
        )
    return blocked


async def run_page_import_audit(
    session: AsyncSession,
    pdf_path: Path,
    *,
    page_number: int,
    ensure_pim_seed: bool = True,
    do_confirm: bool = True,
    allow_needs_review: bool = False,
    reset_products: bool = True,
    cumulative_mode: bool = False,
    imported_pages: list[int] | None = None,
    output_dir: str | None = None,
    baseline_category_ids: set[str] | None = None,
    baseline_slugs: set[str] | None = None,
) -> dict[str, Any]:
    if ensure_pim_seed:
        await seed_taxonomy_mapping_rules(session)

    pages_in_scope = imported_pages if imported_pages is not None else [page_number]

    counts_before_reset = await capture_db_counts(session)
    if reset_products:
        reset_counts = await reset_catalog_data(session)
    else:
        reset_counts = {}

    baseline_ids = baseline_category_ids
    baseline_slug_set = baseline_slugs
    if baseline_ids is None or baseline_slug_set is None:
        baseline_ids, baseline_slug_set, _ = await snapshot_category_state(session)

    counts_after_reset = await capture_db_counts(session)
    reset_summary = build_reset_summary(
        reset_counts=reset_counts,
        counts_before=counts_before_reset,
        counts_after=counts_after_reset,
    )

    baseline_before = {
        "canonical_categories_count": len(baseline_slug_set),
        "canonical_category_slugs": sorted(baseline_slug_set),
        "mapping_rules_count": counts_after_reset.get("taxonomy_mapping_rules", 0),
        "product_masters_count": counts_after_reset.get("product_masters", 0),
        "product_variants_count": counts_after_reset.get("product_variants", 0),
        "catalogue_items_count": counts_after_reset.get("catalogue_items", 0),
    }
    category_snapshot_before = await export_category_snapshot(session)

    supplier = (await session.execute(select(Supplier).where(Supplier.code == "FDL"))).scalar_one()
    profile = (
        await session.execute(
            select(ImportProfile).where(
                ImportProfile.supplier_id == supplier.id,
                ImportProfile.is_default.is_(True),
            )
        )
    ).scalar_one()
    await ensure_fdl_profile_grouping_config(session, profile)
    await session.refresh(profile)

    config = profile.config or {}
    grouping = config.get("grouping") or {}
    grouping_strategy = grouping.get("strategy", "one_master_per_sku")

    all_rows = parse_pdf(pdf_path)
    _init_row_names(all_rows)
    sku_to_page = _build_sku_page_index(all_rows)
    page_rows = [r for r in all_rows if (r.page_number or 0) == page_number]
    if cumulative_mode:
        expected_skus = _expected_skus_for_pages(all_rows, pages_in_scope)
    else:
        expected_skus = {r.sku.upper() for r in page_rows if r.sku}

    _, page_extractions, section_by_page = extract_pages(
        pdf_path,
        page_numbers={page_number},
    )
    page_ext = page_extractions.get(page_number)
    page_lines = page_ext.lines if page_ext else []
    source_section = section_by_page.get(page_number, SourceSection())
    raw_extraction = (
        page_ext.to_dict()
        if page_ext
        else {
            "page_number": page_number,
            "source_section": source_section.to_dict(),
            "lines": [],
            "unparsed_candidates": [],
        }
    )

    page_rows = await map_row_categories(session, page_rows, supplier.id, profile.id)
    page_rows = apply_grouping(page_rows, config)
    from app.services.import_confirm import enrich_rows_with_db_state

    page_rows = await enrich_rows_with_db_state(session, page_rows, supplier.id)
    await validate_parsed_specs_batch(session, page_rows)
    for row in page_rows:
        row.review_status = resolve_review_status(row)

    parsed_rows = [
        _build_parsed_row(
            row,
            source_section=section_by_page.get(row.page_number or page_number, source_section),
            page_lines=page_lines,
        )
        for row in page_rows
    ]

    taxonomy_decision = [
        await build_taxonomy_decision(
            session,
            row,
            baseline_category_ids=baseline_ids,
            baseline_slugs=baseline_slug_set,
            supplier_id=supplier.id,
            import_profile_id=profile.id,
        )
        for row in page_rows
    ]

    preview_decision = [
        _build_preview_decision(row, grouping_strategy=grouping_strategy) for row in page_rows
    ]

    suspicious, suspicion_map = detect_suspicious_variants(
        [
            {
                "page_number": r.page_number,
                "source_row_index": r.row_index,
                "normalized_sku": r.sku,
                "proposed_master_key": r.master_key,
                "grouping_reason": r.grouping_reason,
                "normalized_name": r.normalized_name,
                "inferred_attributes": {"variant_specs": r.parsed_variant_specs_raw or {}},
            }
            for r in page_rows
        ],
        grouping_config=grouping,
        unparsed_by_page={},
    )
    for prev in preview_decision:
        idx = prev["source_row_index"]
        flags = suspicion_map.get(idx, [])
        prev["grouping"]["suspicion_flags"] = flags
        if flags:
            prev["grouping"]["is_grouped_variant"] = any(
                s.get("heuristic") in ("SamePageSkuFamily", "NumericSuffixSplit")
                for s in suspicious
                if prev["normalized_sku"] in (s.get("skus") or [])
            )

    confirm_result: dict[str, Any] = {
        "executed": do_confirm,
        "allow_needs_review": allow_needs_review,
        "rows_imported": 0,
        "rows_blocked": 0,
        "rows_skipped": 0,
        "masters_created": 0,
        "variants_created": 0,
        "variants_updated": 0,
        "entries_created": 0,
        "per_row": [],
    }

    if do_confirm and page_rows:
        batch = await create_batch(
            session,
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename=pdf_path.name,
            parser_key=profile.parser_key,
            row_counts={"total": len(page_rows)},
        )
        staged = await bulk_insert_rows(session, batch.id, page_rows)
        await session.flush()

        result = await confirm_import(
            session,
            batch_id=batch.id,
            row_ids=[s.id for s in staged],
            profile=profile,
            allow_needs_review=allow_needs_review,
        )
        await session.commit()

        confirm_result.update(
            {
                "batch_id": str(batch.id),
                "rows_imported": result.rows_imported,
                "rows_blocked": result.rows_blocked,
                "rows_skipped": result.rows_skipped,
                "masters_created": result.masters_created,
                "variants_created": result.variants_created,
                "variants_updated": result.variants_updated,
                "entries_created": result.entries_created,
            }
        )

        for staged_row in staged:
            ok, gate = can_confirm_row(staged_row, allow_needs_review=allow_needs_review)
            imported = staged_row.review_status == "imported"
            confirm_result["per_row"].append(
                {
                    "source_row_index": staged_row.source_row_index,
                    "sku": staged_row.sku,
                    "would_confirm": ok,
                    "confirm_gate": gate,
                    "imported": imported,
                    "review_status_after": staged_row.review_status,
                }
            )

    db_after = await snapshot_all_supplier_products(session, supplier_id=supplier.id)
    all_db_skus = list(db_after.get("variant_skus") or [])
    imported_skus = {v.upper() for v in all_db_skus}

    db_after_contains_only_requested_page_products, unexpected_skus_from_other_pages = (
        _verify_page_isolation(
            all_db_skus=all_db_skus,
            expected_skus=expected_skus,
            sku_to_page=sku_to_page,
            requested_page=page_number,
        )
    )
    products_expected_but_not_imported = []
    blocked_rows = []
    for row, prev in zip(page_rows, preview_decision, strict=True):
        sku = row.sku or ""
        review = prev["review"]
        if sku.upper() not in imported_skus:
            products_expected_but_not_imported.append(
                {
                    "sku": sku,
                    "source_row_index": row.row_index,
                    "confirm_gate": review.get("confirm_gate"),
                    "blocking_reasons": review.get("blocking_reasons"),
                    "review_reasons": review.get("review_reasons"),
                    "grouping_reason": prev["grouping"].get("grouping_reason"),
                    "can_confirm": review.get("can_confirm"),
                }
            )
        if not review.get("can_confirm"):
            blocked_rows.append(sku)

    inserted_variants = sorted(all_db_skus)
    suspicious_imported = [
        sku
        for sku in inserted_variants
        if any(
            sku in (c.get("skus") or []) and c.get("possible_false_negative") for c in suspicious
        )
    ]

    cats_after_ids, cats_after_slugs, cats_after_list = await snapshot_category_state(session)
    unexpected_categories = sorted(cats_after_slugs - baseline_slug_set)
    category_snapshot_after = await export_category_snapshot(session)

    warnings = _build_warnings(
        taxonomy_rows=taxonomy_decision,
        preview_rows=preview_decision,
        unexpected_categories=unexpected_categories,
    )
    category_warnings, grouping_warnings, review_gate_warnings = _split_warnings(warnings)
    if unexpected_skus_from_other_pages:
        warnings.append(
            {
                "code": "cross_page_contamination",
                "sku": unexpected_skus_from_other_pages[0].get("sku"),
                "detail": (
                    f"{len(unexpected_skus_from_other_pages)} SKU(s) in DB from other PDF pages"
                ),
            }
        )
        category_warnings, grouping_warnings, review_gate_warnings = _split_warnings(warnings)

    products_imported = sorted(imported_skus & expected_skus)
    products_blocked = sorted(blocked_rows)
    blocked_rows_detail = _build_blocked_rows_detail(preview_decision)
    products_visible_in_app = build_products_visible_in_app(db_after)
    products_visible_in_app_count = len(products_visible_in_app)
    expected_visible_products_count = sum(
        1 for prev in preview_decision if (prev.get("review") or {}).get("can_confirm")
    )
    visible_skus = sorted(v["variant_sku"] for v in products_visible_in_app if v.get("variant_sku"))
    visible_categories = sorted(
        {v["category_slug"] for v in products_visible_in_app if v.get("category_slug")}
    )

    status, fail_reasons = _evaluate_page_status(
        do_confirm=do_confirm,
        db_after_contains_only_requested_page_products=db_after_contains_only_requested_page_products,
        unexpected_skus_from_other_pages=unexpected_skus_from_other_pages,
        unexpected_categories=unexpected_categories,
        products_expected_but_not_imported=products_expected_but_not_imported,
        category_warnings=category_warnings,
        grouping_warnings=grouping_warnings,
        review_gate_warnings=review_gate_warnings,
        preview_decision=preview_decision,
    )

    host_output_dir = output_dir or f"temp/audit/pages/{page_number:03d}"

    return {
        "audit_version": "1.2",
        "agent": "agent5_page_import",
        "workflow_mode": "manual_page_by_page",
        "generated_at": datetime.now(UTC).isoformat(),
        "requested_page": page_number,
        "page_number": page_number,
        "output_dir": host_output_dir,
        "pdf_path": str(pdf_path),
        "parsed_full_pdf": {
            "parse_scope": "full_pdf",
            "total_rows_parsed": len(all_rows),
            "total_pages_with_rows": len({r.page_number for r in all_rows if r.page_number}),
        },
        "rows_filtered_to_page": {
            "requested_page": page_number,
            "count": len(page_rows),
            "source_row_indices": [r.row_index for r in page_rows],
            "expected_skus": sorted(expected_skus),
        },
        "reset_before_page": reset_products,
        "cumulative_mode": cumulative_mode,
        "confirm_executed": do_confirm,
        "imported_pages": pages_in_scope,
        "reset_summary": reset_summary,
        "baseline_before": baseline_before,
        "category_snapshot_before": category_snapshot_before,
        "category_snapshot_after": category_snapshot_after,
        "raw_extraction": raw_extraction,
        "parsed_rows": parsed_rows,
        "taxonomy_decision": taxonomy_decision,
        "preview_decision": preview_decision,
        "confirm_result": confirm_result,
        "db_after": db_after,
        "db_after_contains_only_requested_page_products": db_after_contains_only_requested_page_products,
        "unexpected_skus_from_other_pages": unexpected_skus_from_other_pages,
        "products_visible_in_app_count": products_visible_in_app_count,
        "products_visible_in_app": products_visible_in_app,
        "blocked_rows_detail": blocked_rows_detail,
        "status": status,
        "fail_reasons": fail_reasons,
        "products_imported": products_imported,
        "products_blocked": products_blocked,
        "products_expected_but_not_imported": products_expected_but_not_imported,
        "category_warnings": category_warnings,
        "grouping_warnings": grouping_warnings,
        "review_gate_warnings": review_gate_warnings,
        "app_visual_check": {
            "products_page_should_show_only_requested_page": db_after_contains_only_requested_page_products,
            "expected_visible_products_count": expected_visible_products_count,
            "actual_visible_products_count": products_visible_in_app_count,
            "visible_skus": visible_skus,
            "visible_categories": visible_categories,
            "note": (
                f"Open Products page in the app after this run to visually inspect only page "
                f"{page_number} products."
            ),
        },
        "diff": {
            "inserted_masters": [m["master_key"] for m in db_after.get("masters") or []],
            "inserted_variants": inserted_variants,
            "skipped_rows": confirm_result.get("rows_skipped", 0),
            "blocked_rows": blocked_rows,
            "categories_created": unexpected_categories,
            "mappings_created": [],
            "unexpected_categories": unexpected_categories,
            "products_imported_but_suspicious": suspicious_imported,
        },
        "warnings": warnings,
        "suspicious_variant_candidates": suspicious,
        "manual_approval": {
            "page_approved": False,
            "note": "Page is not approved until the user gives explicit OK. Do not advance to the next page automatically.",
        },
    }
