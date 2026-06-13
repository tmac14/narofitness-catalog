"""Orchestrate full-PDF parse + pipeline trace for variant detection audit."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportProfile, Supplier
from app.services.import_audit.failure_classifier import classify_all_rows
from app.services.import_audit.metrics import compute_metrics
from app.services.import_audit.page_extraction import (
    PageExtraction,
    SourceSection,
    extract_pages,
    find_unparsed_candidates,
)
from app.services.import_audit.report import build_report_payload
from app.services.import_audit.row_trace import build_audited_row, capture_stage_snapshots
from app.services.import_audit.suspicious_variants import (
    build_groups_detected,
    detect_suspicious_variants,
)
from app.services.import_confirm import enrich_rows_with_db_state
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import resolve_review_status
from app.services.import_spec_validate import validate_parsed_specs_batch
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_pim import seed_pim
from app.services.taxonomy_mapper import map_row_categories


@dataclass
class PageFilter:
    mode: str = "all"
    page: int | None = None
    from_page: int | None = None
    to_page: int | None = None
    pages: list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "page": self.page,
            "from": self.from_page,
            "to": self.to_page,
            "pages": self.pages,
        }

    def matches(self, page_number: int) -> bool:
        if self.mode == "all":
            return True
        if self.mode == "single" and self.page is not None:
            return page_number == self.page
        if self.mode == "range" and self.from_page is not None and self.to_page is not None:
            return self.from_page <= page_number <= self.to_page
        if self.mode == "list" and self.pages:
            return page_number in self.pages
        return True

    def page_numbers_for_extraction(self, total_pages: int) -> set[int] | None:
        if self.mode == "all":
            return None
        if self.mode == "single" and self.page is not None:
            return {self.page}
        if self.mode == "range" and self.from_page is not None and self.to_page is not None:
            return set(range(self.from_page, self.to_page + 1))
        if self.mode == "list" and self.pages:
            return set(self.pages)
        return set(range(1, total_pages + 1))


def _clone_rows(rows: list[ImportRow]) -> list[ImportRow]:
    return copy.deepcopy(rows)


def _rows_by_index(rows: list[ImportRow]) -> dict[int, ImportRow]:
    return {r.row_index: r for r in rows}


def _init_row_names(rows: list[ImportRow]) -> None:
    for row in rows:
        if not row.raw_name:
            row.raw_name = row.name
        if not row.normalized_name:
            row.normalized_name = row.name


def _config_hash(config: dict[str, Any]) -> str:
    blob = json.dumps(config, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(blob.encode()).hexdigest()[:16]


async def run_variant_audit(
    session: AsyncSession,
    pdf_path: Path,
    *,
    page_filter: PageFilter | None = None,
    include_db_diff: bool = True,
    compact: bool = False,
) -> dict[str, Any]:
    """Run full PDF parse, apply production pipeline, return audit report payload."""
    page_filter = page_filter or PageFilter()

    rows = parse_pdf(pdf_path)
    _init_row_names(rows)

    await seed_pim(session, pdf_path=pdf_path, skip_categories=True, skip_brands=True)
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

    stage_store: dict[int, dict[str, dict[str, Any]]] = {}
    capture_stage_snapshots(_rows_by_index(rows), "parse", stage_store)

    after_taxonomy = _clone_rows(rows)
    after_taxonomy = await map_row_categories(session, after_taxonomy, supplier.id, profile.id)
    capture_stage_snapshots(_rows_by_index(after_taxonomy), "taxonomy", stage_store)

    after_grouping = _clone_rows(after_taxonomy)
    after_grouping = apply_grouping(after_grouping, config)
    capture_stage_snapshots(_rows_by_index(after_grouping), "grouping", stage_store)

    after_db = _clone_rows(after_grouping)
    if include_db_diff:
        after_db = await enrich_rows_with_db_state(session, after_db, supplier.id)
    capture_stage_snapshots(_rows_by_index(after_db), "db_diff", stage_store)

    after_specs = _clone_rows(after_db)
    await validate_parsed_specs_batch(session, after_specs)
    capture_stage_snapshots(_rows_by_index(after_specs), "spec_validate", stage_store)

    final_rows = _clone_rows(after_specs)
    for row in final_rows:
        row.review_status = resolve_review_status(row)
    capture_stage_snapshots(_rows_by_index(final_rows), "review", stage_store)

    extract_only = page_filter.page_numbers_for_extraction(0) if page_filter.mode != "all" else None
    total_pages, page_extractions, section_by_page = extract_pages(
        pdf_path,
        page_numbers=extract_only,
    )

    all_audited: list[dict[str, Any]] = []
    for row in final_rows:
        page_num = row.page_number or 0
        section = section_by_page.get(page_num, SourceSection())
        page_ext = page_extractions.get(page_num)
        snapshots = stage_store.get(row.row_index)
        audited = build_audited_row(
            row,
            source_section=section,
            grouping_strategy=grouping_strategy,
            grouping_config=grouping,
            page_extraction=page_ext,
            stage_snapshots=snapshots,
            compact=compact,
        )
        all_audited.append(audited)

    filtered_audited = [r for r in all_audited if page_filter.matches(r.get("page_number") or 0)]

    unparsed_by_page: dict[int, list[dict[str, Any]]] = {}
    pages_out: list[dict[str, Any]] = []

    pages_to_report = sorted(
        {r.get("page_number") for r in filtered_audited} | set(page_extractions.keys())
    )

    rows_by_page: dict[int, list[dict[str, Any]]] = {}
    for r in filtered_audited:
        pn = r.get("page_number") or 0
        rows_by_page.setdefault(pn, []).append(r)

    all_skus_by_page: dict[int, set[str]] = {}
    for r in all_audited:
        pn = r.get("page_number") or 0
        sku = r.get("normalized_sku")
        if sku:
            all_skus_by_page.setdefault(pn, set()).add(sku.upper())

    for page_num in pages_to_report:
        pe = page_extractions.get(page_num)
        if pe is None:
            pe = PageExtraction(
                page_number=page_num,
                source_section=section_by_page.get(page_num, SourceSection()),
            )
        skus_on_page = all_skus_by_page.get(page_num, set())
        orphans = find_unparsed_candidates(pe, skus_on_page)
        pe.unparsed_candidates = orphans
        unparsed_by_page[page_num] = [o.to_dict() for o in orphans]

        page_dict = pe.to_dict()
        page_dict["rows"] = rows_by_page.get(page_num, [])
        pages_out.append(page_dict)

    suspicious, suspicion_map = detect_suspicious_variants(
        all_audited,
        grouping_config=grouping,
        unparsed_by_page=unparsed_by_page,
    )
    groups = build_groups_detected(all_audited)
    failures = classify_all_rows(all_audited, suspicion_map, unparsed_by_page)

    metrics = compute_metrics(
        total_pages=total_pages,
        pages_in_filter=len(pages_to_report),
        all_audited_rows=all_audited,
        filtered_audited_rows=filtered_audited,
        groups_detected=groups,
        suspicious_candidates=suspicious,
        failure_classifications=failures,
    )

    profile_meta = {
        "parser_key": profile.parser_key,
        "grouping_strategy": grouping_strategy,
        "grouping_config_hash": _config_hash(grouping),
    }

    return build_report_payload(
        pdf_path=pdf_path,
        total_pages=total_pages,
        page_filter=page_filter.to_dict(),
        profile_meta=profile_meta,
        metrics=metrics,
        groups_detected=groups,
        suspicious_candidates=suspicious,
        failure_classifications=failures,
        pages=pages_out,
    )
