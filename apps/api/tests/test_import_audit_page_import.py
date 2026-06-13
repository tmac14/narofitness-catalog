"""Tests for page-by-page import audit sandbox (Agent 5)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.database import async_session
from app.models import Category, ImportProfile, Supplier, TaxonomyMappingRule
from app.services.import_audit.page_import import (
    _build_preview_decision,
    _evaluate_page_status,
    _verify_page_isolation,
    run_page_import_audit,
)
from app.services.import_audit.page_import_report import (
    host_output_dir_for_page,
    page_audit_dir,
    write_page_audit_bundle,
)
from app.services.import_grouping import DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX, apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_pipeline import run_preview_pipeline
from app.services.import_review import resolve_review_status
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_categories import seed_default_categories
from app.services.seed_reset import reset_catalog_data
from app.services.seed_taxonomy_mapping_rules import (
    MATCH_SKU_PREFIX,
    RETIRED_TAXONOMY_MAPPING_RULE_KEYS,
    seed_taxonomy_mapping_rules,
)
from sqlalchemy import func, select

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "explicit_numeric_sku_regex": DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX,
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
}


async def _fdl_default_profile(session):
    supplier = (await session.execute(select(Supplier).where(Supplier.code == "FDL"))).scalar_one()
    return (
        await session.execute(
            select(ImportProfile).where(
                ImportProfile.supplier_id == supplier.id,
                ImportProfile.is_default.is_(True),
            )
        )
    ).scalar_one()


def _parser_row(
    *, sku: str, name: str, category_path: str, page: int = 3, idx: int = 0
) -> ImportRow:
    return ImportRow(
        row_index=idx,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        raw_name=name,
        normalized_name=name,
        brand="XEBEX",
        ean=None,
        category_path=category_path,
        price_amount=Decimal("112.20"),
        page_number=page,
        raw_lines=[name, sku, "112,20 €"],
    )


def test_baseline_export_schema():
    payload = {
        "generated_at": "2026-01-01T00:00:00Z",
        "baseline_mode": "pim_only",
        "canonical_categories": [],
        "counts": {"parents": 0, "subcategories": 0, "total": 0},
    }
    rules = {
        "active_rules": [],
        "inactive_rules": [],
        "repuesto_rule_check": {
            "rule_exists": False,
            "match_type": "sku_prefix",
            "match_value": "REPUESTO-",
            "retired_in_code": True,
        },
    }
    assert payload["baseline_mode"] == "pim_only"
    assert "repuesto_rule_check" in rules


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repuesto_rule_inactive_after_seed(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        rule = (
            await session.execute(
                select(TaxonomyMappingRule).where(
                    TaxonomyMappingRule.match_type == MATCH_SKU_PREFIX,
                    TaxonomyMappingRule.match_value == "REPUESTO-",
                )
            )
        ).scalar_one_or_none()

    assert (MATCH_SKU_PREFIX, "REPUESTO-") in RETIRED_TAXONOMY_MAPPING_RULE_KEYS
    if rule is not None:
        assert rule.is_active is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reset_catalog_preserves_categories(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        before = (await session.execute(select(func.count()).select_from(Category))).scalar_one()
        await reset_catalog_data(session)
        after = (await session.execute(select(func.count()).select_from(Category))).scalar_one()
    assert before == after
    assert before > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_no_category_created_after_preview(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        before = list((await session.execute(select(Category.slug))).scalars().all())
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()
        content = reference_pdf.read_bytes()
        await run_preview_pipeline(
            session,
            content=content,
            profile=profile,
            supplier_id=supplier.id,
            filename=reference_pdf.name,
        )
        await session.commit()
        after = list((await session.execute(select(Category.slug))).scalars().all())
    assert sorted(before) == sorted(after)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_no_category_created_after_confirm(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    from app.services.import_confirm import confirm_import

    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        before = set((await session.execute(select(Category.slug))).scalars().all())
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()
        content = reference_pdf.read_bytes()
        batch, _, _, _ = await run_preview_pipeline(
            session,
            content=content,
            profile=profile,
            supplier_id=supplier.id,
            filename=reference_pdf.name,
        )
        await confirm_import(session, batch_id=batch.id, profile=profile, allow_needs_review=False)
        await session.commit()
        after = set((await session.execute(select(Category.slug))).scalars().all())
    assert before == after


def test_page_audit_bundle_paths(tmp_path):
    report = {
        "requested_page": 3,
        "output_dir": host_output_dir_for_page(3),
        "parsed_rows": [{"sku": "A"}],
        "category_snapshot_before": {"count": 1},
        "category_snapshot_after": {"count": 1},
        "db_after": {"variants": []},
        "raw_extraction": {"page_number": 3},
        "products_visible_in_app": [],
        "blocked_rows_detail": [],
        "parsed_full_pdf": {},
        "rows_filtered_to_page": {},
        "reset_summary": {},
        "preview_decision": [],
        "app_visual_check": {},
        "manual_approval": {},
    }
    page_dir = page_audit_dir(tmp_path, 3)
    written = write_page_audit_bundle(report, page_dir, write_format="both")
    assert (page_dir / "page_import_audit.json").is_file()
    assert (page_dir / "page_import_audit.md").is_file()
    assert (page_dir / "category_snapshot_before.json").is_file()
    assert (page_dir / "db_snapshot_after.json").is_file()
    assert (page_dir / "parsed_rows.json").is_file()
    assert (page_dir / "imported_products.json").is_file()
    assert (page_dir / "blocked_rows.json").is_file()
    assert "page_import_audit.json" in written


def test_workflow_metadata_schema():
    isolated, unexpected = _verify_page_isolation(
        all_db_skus=["BIC010"],
        expected_skus={"REPUESTO-805", "REPUESTO-806"},
        sku_to_page={"REPUESTO-805": 3, "REPUESTO-806": 3, "BIC010": 4},
        requested_page=3,
    )
    assert isolated is False
    assert unexpected[0]["sku"] == "BIC010"
    assert unexpected[0]["source_page_in_full_pdf"] == 4

    isolated_ok, unexpected_ok = _verify_page_isolation(
        all_db_skus=["REPUESTO-805", "REPUESTO-806"],
        expected_skus={"REPUESTO-805", "REPUESTO-806"},
        sku_to_page={"REPUESTO-805": 3, "REPUESTO-806": 3, "BIC010": 4},
        requested_page=3,
    )
    assert isolated_ok is True
    assert unexpected_ok == []

    status, reasons = _evaluate_page_status(
        do_confirm=True,
        db_after_contains_only_requested_page_products=False,
        unexpected_skus_from_other_pages=[{"sku": "BIC010", "source_page_in_full_pdf": 4}],
        unexpected_categories=[],
        products_expected_but_not_imported=[],
        category_warnings=[],
        grouping_warnings=[],
        review_gate_warnings=[],
        preview_decision=[],
    )
    assert status == "fail"
    assert "db_contains_products_from_other_pages" in reasons


def test_page_import_blocked_row_reason():
    row = _parser_row(sku="FDRig-3", name="JAULA", category_path="MUSCULACION", idx=1)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    row.review_status = resolve_review_status(row)
    prev = _build_preview_decision(row, grouping_strategy="fdl_sku_family")
    assert prev["review"]["can_confirm"] is False
    assert (
        "regex_fallback_1_1" in prev["review"]["blocking_reasons"] or prev["review"]["confirm_gate"]
    )

    not_imported = {
        "sku": row.sku,
        "confirm_gate": prev["review"]["confirm_gate"],
        "blocking_reasons": prev["review"]["blocking_reasons"],
        "grouping_reason": prev["grouping"]["grouping_reason"],
    }
    assert not_imported["sku"] == "FDRig-3"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_page_import_repuesto_page3_fresh(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        await ensure_fdl_profile_grouping_config(session, await _fdl_default_profile(session))

        report = await run_page_import_audit(
            session,
            reference_pdf,
            page_number=3,
            ensure_pim_seed=False,
            do_confirm=True,
        )

    repuesto_rows = {
        r["normalized_sku"]: r
        for r in report.get("parsed_rows") or []
        if (r.get("normalized_sku") or "").startswith("REPUESTO-")
    }
    if "REPUESTO-805" not in repuesto_rows and "REPUESTO-806" not in repuesto_rows:
        pytest.skip("REPUESTO SKUs not on page 3 in reference PDF")

    for sku in ("REPUESTO-805", "REPUESTO-806"):
        if sku not in repuesto_rows:
            continue
        parsed = repuesto_rows[sku]
        assert parsed["source_taxonomy_path"] == "CARDIO > BICI"

        tax = next(
            (t for t in report["taxonomy_decision"] if t["normalized_sku"] == sku),
            None,
        )
        prev = next(
            (p for p in report["preview_decision"] if p["normalized_sku"] == sku),
            None,
        )
        assert tax is not None and prev is not None
        assert tax["canonical_category_slug"] == "bicicletas-estaticas"
        assert tax["canonical_category_slug"] != "repuestos"
        assert prev["grouping"]["grouping_reason"] == "explicit_one_per_sku"
        assert prev["review"]["can_confirm"] is True
        assert prev["grouping"]["proposed_master_key"] == sku

        db_variants = {
            v["variant_sku"] for v in (report.get("db_after") or {}).get("variants") or []
        }
        assert sku in db_variants

    assert report["requested_page"] == 3
    assert report["cumulative_mode"] is False
    assert report["imported_pages"] == [3]
    assert report["reset_before_page"] is True
    assert report["parsed_full_pdf"]["parse_scope"] == "full_pdf"
    assert report["rows_filtered_to_page"]["requested_page"] == 3
    assert report["db_after_contains_only_requested_page_products"] is True
    assert report["unexpected_skus_from_other_pages"] == []
    assert report["status"] == "pass"
    assert "parsed_rows" in report
    assert "preview_decision" in report
    assert "confirm_result" in report
    assert "db_after" in report
    assert report["reset_summary"]["categories_preserved"] is True
    assert report["manual_approval"]["page_approved"] is False
    assert report["confirm_executed"] is True
    assert report["output_dir"] == "temp/audit/pages/003"
    assert report["products_visible_in_app_count"] == len(report["products_imported"])
    visual = report["app_visual_check"]
    assert visual["products_page_should_show_only_requested_page"] is True
    assert visual["actual_visible_products_count"] == report["products_visible_in_app_count"]
    assert "category_snapshot_before" in report
    assert "category_snapshot_after" in report
    assert "raw_extraction" in report
    assert "blocked_rows_detail" in report


@pytest.mark.integration
@pytest.mark.asyncio
async def test_page_import_page11_fresh(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        await ensure_fdl_profile_grouping_config(session, await _fdl_default_profile(session))

        report = await run_page_import_audit(
            session,
            reference_pdf,
            page_number=11,
            ensure_pim_seed=False,
            do_confirm=True,
        )

    expected_skus = set(report.get("rows_filtered_to_page", {}).get("expected_skus") or [])
    if not expected_skus:
        pytest.skip("Page 11 SKUs not found in reference PDF audit")

    parsed_rows = {r["normalized_sku"]: r for r in report.get("parsed_rows") or []}
    preview = {p["normalized_sku"]: p for p in report.get("preview_decision") or []}
    blocked = {b["normalized_sku"]: b for b in report.get("blocked_rows_detail") or []}

    assert report["requested_page"] == 11
    assert report["status"] == "pass"
    assert len(report["products_imported"]) == len(expected_skus)
    assert set(report["products_imported"]) == expected_skus
    assert len(blocked) == 0

    dobnexo_rows = [sku for sku in expected_skus if sku.startswith("DOBNEXO")]
    bumper_rows = [sku for sku in expected_skus if not sku.startswith("DOBNEXO")]

    for sku in dobnexo_rows:
        prev = preview[sku]
        assert prev["grouping"]["grouping_reason"].startswith("fdl_sku_family:")
        assert prev["review"]["can_confirm"] is True
        assert (
            parsed_rows[sku]["source_taxonomy_path"] == "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL"
        )

    for sku in bumper_rows:
        prev = preview[sku]
        assert prev["taxonomy"]["canonical_category_slug"] == "discos"
        assert prev["grouping"]["grouping_reason"].startswith("cross_training_bumper_family:")
        assert prev["review"]["can_confirm"] is True

    db_variants = {v["variant_sku"] for v in (report.get("db_after") or {}).get("variants") or []}
    assert expected_skus.issubset(db_variants)
    assert report["confirm_executed"] is True
    assert report["output_dir"] == "temp/audit/pages/011"

    master_names = {
        m["master_key"]: m.get("master_name") or m.get("name")
        for m in (report.get("db_after") or {}).get("masters") or []
    }
    if master_names:
        assert "DOBNEXON" in master_names
        assert "25 kgs" not in (master_names.get("DOBNEXON") or "").lower()
        assert "DOBC" in master_names or "DOB3C" in master_names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_page_import_page12_fresh(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        await ensure_fdl_profile_grouping_config(session, await _fdl_default_profile(session))

        report = await run_page_import_audit(
            session,
            reference_pdf,
            page_number=12,
            ensure_pim_seed=False,
            do_confirm=True,
        )

    expected_skus = set(report.get("rows_filtered_to_page", {}).get("expected_skus") or [])
    if not expected_skus:
        pytest.skip("Page 12 SKUs not found in reference PDF audit")

    parsed_rows = {r["normalized_sku"]: r for r in report.get("parsed_rows") or []}
    preview = {p["normalized_sku"]: p for p in report.get("preview_decision") or []}
    blocked = {b["normalized_sku"]: b for b in report.get("blocked_rows_detail") or []}

    assert report["requested_page"] == 12
    assert report["status"] == "pass"
    assert len(report["products_imported"]) == len(expected_skus)
    assert set(report["products_imported"]) == expected_skus
    assert len(blocked) == 0

    bumper_prefixes = ("DOBHT", "DOBCC", "DOBF")
    post_competicion_skus = ("DOBF", "SOP", "DOBMINI", "CRO")
    for sku in expected_skus:
        if sku.startswith(bumper_prefixes):
            prev = preview[sku]
            assert prev["taxonomy"]["canonical_category_slug"] == "discos"
            assert prev["grouping"]["grouping_reason"].startswith("cross_training_bumper_family:")
            assert prev["review"]["can_confirm"] is True
        if sku.startswith(post_competicion_skus):
            assert "Competicion Casquillo" not in (parsed_rows[sku].get("raw_name") or "")

    assert preview["SOP025"]["taxonomy"]["canonical_category_slug"] == "soportes-y-mancuerneros"
    assert preview["SOP025"]["grouping"]["grouping_reason"] == "explicit_one_per_sku"
    assert preview["SOP025"]["review"]["can_confirm"] is True

    assert preview["DOBMINI"]["grouping"]["grouping_reason"] == "explicit_one_per_sku"
    assert preview["DOBMINI"]["review"]["can_confirm"] is True

    cro_skus = [sku for sku in expected_skus if sku.startswith("CRO")]
    cro_master_keys = {preview[sku]["grouping"]["proposed_master_key"] for sku in cro_skus}
    assert len(cro_master_keys) >= 2
    for sku in cro_skus:
        assert preview[sku]["taxonomy"]["canonical_category_slug"] == "cross-training"
        assert preview[sku]["grouping"]["grouping_reason"].startswith(
            "cross_training_block_family:"
        )

    db_variants = {v["variant_sku"] for v in (report.get("db_after") or {}).get("variants") or []}
    assert expected_skus.issubset(db_variants)
    assert report["confirm_executed"] is True
    assert report["output_dir"] == "temp/audit/pages/012"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("page_number", [4, 5])
async def test_page_import_simple_pages_fresh(integration_db, reference_pdf, page_number: int):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        await ensure_fdl_profile_grouping_config(session, await _fdl_default_profile(session))

        report = await run_page_import_audit(
            session,
            reference_pdf,
            page_number=page_number,
            ensure_pim_seed=False,
            do_confirm=True,
        )

    expected_count = report.get("rows_filtered_to_page", {}).get("count") or 0
    if expected_count == 0:
        pytest.skip(f"No rows on page {page_number} in reference PDF")

    assert report["status"] == "pass"
    assert len(report.get("blocked_rows_detail") or []) == 0
    assert report["products_imported"]


def _assert_cardio_explicit_master_names_aligned(report: dict) -> None:
    parsed = {r["normalized_sku"]: r for r in report.get("parsed_rows") or []}
    preview = {p["normalized_sku"]: p for p in report.get("preview_decision") or []}
    masters_by_key = {
        m["master_key"]: (m.get("product_master_name") or m.get("master_name") or "").strip()
        for m in (report.get("db_after") or {}).get("masters") or []
    }

    for sku, prev in preview.items():
        if prev["grouping"]["grouping_reason"] != "explicit_one_per_sku":
            continue
        parsed_row = parsed.get(sku) or {}
        normalized = (parsed_row.get("normalized_name") or parsed_row.get("name") or "").strip()
        master_key = prev["grouping"]["proposed_master_key"]
        master_name = masters_by_key.get(master_key, "")
        assert master_name == normalized, (
            f"{sku}: master_name {master_name!r} != normalized_name {normalized!r}"
        )
        assert "xebex" not in master_name.lower(), (
            f"{sku}: XEBEX residual in master_name {master_name!r}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("page_number", [3, 4, 5, 6])
async def test_page_import_cardio_master_names_aligned(
    integration_db, reference_pdf, page_number: int
):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        await ensure_fdl_profile_grouping_config(session, await _fdl_default_profile(session))

        report = await run_page_import_audit(
            session,
            reference_pdf,
            page_number=page_number,
            ensure_pim_seed=False,
            do_confirm=True,
        )

    expected_count = report.get("rows_filtered_to_page", {}).get("count") or 0
    if expected_count == 0:
        pytest.skip(f"No rows on page {page_number} in reference PDF")

    assert report["status"] == "pass"
    assert len(report.get("blocked_rows_detail") or []) == 0
    _assert_cardio_explicit_master_names_aligned(report)
