#!/usr/bin/env python3
"""Minimal full-catalog audit compatible with post_c2a_mk_validation output shape."""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.database import async_session
from app.models import ImportRow, ProductMaster, ProductVariant
from app.services.import_audit.pipeline import PageFilter, run_variant_audit
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.models import ImportProfile, Supplier
from app.services.taxonomy_mapper import map_row_categories


async def main(output_dir: Path) -> None:
    pdf = resolve_pdf_path(None)
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_session() as session:
        report = await run_variant_audit(session, pdf, page_filter=PageFilter(), include_db_diff=True)
        masters = (await session.execute(select(func.count()).select_from(ProductMaster))).scalar_one()
        variants = (await session.execute(select(func.count()).select_from(ProductVariant))).scalar_one()
        singletons = (
            await session.execute(
                select(func.count())
                .select_from(
                    select(ProductMaster.id)
                    .join(ProductVariant, ProductVariant.product_master_id == ProductMaster.id)
                    .group_by(ProductMaster.id)
                    .having(func.count(ProductVariant.id) == 1)
                    .subquery()
                )
            )
        ).scalar_one()

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
        grouping = (profile.config or {}).get("grouping") or {}
        parsed = [r for r in parse_pdf(pdf) if r.sku]
        mapped = await map_row_categories(session, parsed, supplier.id, profile.id)
        apply_grouping(mapped, {"grouping": grouping})
        importable = sum(1 for row in mapped if can_confirm_row(row)[0])
        blocked = len(mapped) - importable

    suspicious = report.get("suspicious_candidates") or []
    family_candidates = suspicious  # legacy audit counted heuristic groups; approximate via suspicious list
    high_conf = [c for c in family_candidates if str(c.get("confidence", "")).lower() == "high" or c.get("score", 0) >= 0.85]

    payload = {
        "audit_version": "1.0",
        "agent": "agent5_full_catalog",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow": "IMPORT-FDL-MASTER-NAME-CONSISTENCY-POST-VALIDATION",
        "pdf_path": str(pdf),
        "db_snapshot": {
            "masters_total": masters,
            "variants_total": variants,
            "singleton_masters_count": singletons,
        },
        "metrics": {
            "total_rows_parsed": len(parsed),
            "rows_importable": importable,
            "rows_blocked": blocked,
            "masters_in_db": masters,
            "variants_in_db": variants,
            "singleton_masters_in_db": singletons,
            "family_candidates": len(family_candidates),
            "high_confidence_family_candidates": len(high_conf),
        },
        "pipeline_metrics": report.get("metrics") or {},
        "profile": report.get("profile_meta") or {},
        "suspicious_candidates": suspicious,
    }

    out = output_dir / "full_catalog_import_audit.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "metrics": payload["metrics"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("/data/audit/full_catalog/post_master_name_consistency"))
    args = parser.parse_args()
    asyncio.run(main(args.output_dir))
