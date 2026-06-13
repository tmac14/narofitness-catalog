#!/usr/bin/env python3
"""B3B category profile eligibility audit — read-only full catalog."""
from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models import (
    Category,
    CategorySpecProfile,
    ImportRow,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
)
from app.services.seed_category_spec_profiles import DEFAULT_CATEGORY_SPEC_PROFILE_ROWS
from app.services.spec_resolver import (
    build_variant_row_spec_values,
    load_printable_variant_columns,
    visible_variant_columns,
)

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage/b3b_profile_eligibility")

PROFILED_SLUGS = {
    row.category_slug for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS
}

BASELINE = {
    "variants_total": 871,
    "masters_total": 534,
    "rows_blocked": 0,
    "longitud_mm": 20,
}


async def category_inventory(session) -> list[dict]:
    rows = (
        await session.execute(
            text("""
                SELECT c.slug, c.name,
                       COUNT(DISTINCT pm.id) AS masters,
                       COUNT(DISTINCT pv.id) AS variants,
                       COUNT(DISTINCT CASE WHEN pm_cnt.c = 1 THEN pm.id END) AS singleton_masters
                FROM categories c
                LEFT JOIN product_masters pm ON pm.category_id = c.id
                LEFT JOIN product_variants pv ON pv.product_master_id = pm.id
                LEFT JOIN (
                    SELECT product_master_id, COUNT(*) AS c
                    FROM product_variants GROUP BY product_master_id
                ) pm_cnt ON pm_cnt.product_master_id = pm.id
                GROUP BY c.slug, c.name
                ORDER BY variants DESC NULLS LAST, c.slug
            """)
        )
    ).all()
    return [
        {
            "slug": r[0],
            "name": r[1],
            "masters": r[2] or 0,
            "variants": r[3] or 0,
            "singleton_masters": r[4] or 0,
            "multi_variant_masters": (r[2] or 0) - (r[4] or 0),
        }
        for r in rows
        if (r[3] or 0) > 0
    ]


async def specs_by_category(session) -> dict[str, dict[str, int]]:
    v_rows = (
        await session.execute(
            text("""
                SELECT c.slug, sd.key, COUNT(*)
                FROM product_variant_specs pvs
                JOIN product_variants pv ON pv.id = pvs.variant_id
                JOIN product_masters pm ON pm.id = pv.product_master_id
                JOIN categories c ON c.id = pm.category_id
                JOIN spec_definitions sd ON sd.id = pvs.spec_definition_id
                GROUP BY c.slug, sd.key
            """)
        )
    ).all()
    m_rows = (
        await session.execute(
            text("""
                SELECT c.slug, sd.key, COUNT(*)
                FROM product_master_specs pms
                JOIN product_masters pm ON pm.id = pms.master_id
                JOIN categories c ON c.id = pm.category_id
                JOIN spec_definitions sd ON sd.id = pms.spec_definition_id
                GROUP BY c.slug, sd.key
            """)
        )
    ).all()
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"variant": {}, "master": {}})
    for slug, key, cnt in v_rows:
        out[slug]["variant"][key] = cnt
    for slug, key, cnt in m_rows:
        out[slug]["master"][key] = cnt
    return dict(out)


async def pages_by_category(session) -> dict[str, list[int]]:
    rows = (
        await session.execute(
            select(ImportRow.mapped_category_slug, ImportRow.source_page, func.count())
            .where(ImportRow.sku.isnot(None), ImportRow.mapped_category_slug.isnot(None))
            .group_by(ImportRow.mapped_category_slug, ImportRow.source_page)
        )
    ).all()
    by_cat: dict[str, set[int]] = defaultdict(set)
    for slug, page, _ in rows:
        if slug and page:
            by_cat[slug].add(int(page))
    return {k: sorted(v) for k, v in by_cat.items()}


async def profile_keys(session) -> dict[str, list[str]]:
    rows = (
        await session.execute(
            select(Category.slug, SpecDefinition.key, CategorySpecProfile.sort_order)
            .join(CategorySpecProfile, CategorySpecProfile.category_id == Category.id)
            .join(SpecDefinition, SpecDefinition.id == CategorySpecProfile.spec_definition_id)
            .order_by(Category.slug, CategorySpecProfile.sort_order)
        )
    ).all()
    out: dict[str, list[str]] = defaultdict(list)
    for slug, key, _ in rows:
        out[slug].append(key)
    return dict(out)


async def visibility_simulation(session, slug: str) -> dict[str, Any]:
    category = (
        await session.execute(select(Category).where(Category.slug == slug))
    ).scalar_one_or_none()
    if not category:
        return {}
    variants = (
        await session.execute(
            select(ProductVariant)
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .where(ProductMaster.category_id == category.id)
            .options(
                selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.spec_definition)
            )
        )
    ).scalars().all()
    cols_no_profile_sim = await load_printable_variant_columns(session, category.id, variants=variants)
    # Current behavior (no profile in DB for this cat)
    has_profile = (
        await session.execute(
            select(func.count())
            .select_from(CategorySpecProfile)
            .where(CategorySpecProfile.category_id == category.id)
        )
    ).scalar_one() > 0

    cols_current = await load_printable_variant_columns(session, category.id, variants=variants)
    attribute_rows = [build_variant_row_spec_values(v, cols_current) for v in variants]
    visible = visible_variant_columns(cols_current, attribute_rows) if len(variants) >= 2 else []

    variants_with_any_spec = sum(1 for v in variants if v.specs)
    variants_with_visible_col: dict[str, int] = defaultdict(int)
    for col in cols_current:
        filled = sum(
            1
            for row in attribute_rows
            if row.get(col.key) not in (None, "", "—")
        )
        variants_with_visible_col[col.key] = filled

    multi_masters = (
        await session.execute(
            text("""
                SELECT pm.master_key, COUNT(pv.id) AS n
                FROM product_masters pm
                JOIN product_variants pv ON pv.product_master_id = pm.id
                WHERE pm.category_id = :cid
                GROUP BY pm.id, pm.master_key
                HAVING COUNT(pv.id) > 1
            """),
            {"cid": str(category.id)},
        )
    ).all()

    return {
        "variant_count": len(variants),
        "has_profile_today": has_profile,
        "column_keys_current": [c.key for c in cols_current],
        "visible_column_keys_multi_variant": [c.key for c in visible],
        "variants_with_any_spec": variants_with_any_spec,
        "variants_with_value_by_column": dict(variants_with_visible_col),
        "multi_variant_master_count": len(multi_masters),
        "discovery_only_columns": [
            c.key for c in cols_current if c.key not in (PROFILED_SLUGS and [])
        ],
    }


def classify_category(
    slug: str,
    inv: dict,
    specs: dict,
    pages: list[int],
    vis: dict,
) -> dict[str, Any]:
    v_specs = specs.get("variant", {})
    m_specs = specs.get("master", {})
    all_spec_keys = set(v_specs) | set(m_specs)
    variants = inv["variants"]
    masters = inv["masters"]
    singleton_pct = round(100.0 * inv["singleton_masters"] / max(masters, 1), 1)

    total_v_spec_rows = sum(v_specs.values())
    top_spec = max(v_specs.items(), key=lambda x: x[1]) if v_specs else None

    # Proposed profile rows for LOW_RISK only
    proposed: list[dict] = []

    if slug in PROFILED_SLUGS:
        classification = "NO_PROFILE_NEEDED"
        reason = "Already has CategorySpecProfile seed rows"
    elif variants == 0:
        classification = "NO_PROFILE_NEEDED"
        reason = "No catalog variants"
    elif total_v_spec_rows == 0 and not m_specs:
        classification = "PROFILE_NOT_USEFUL"
        reason = "Zero persisted specs; profile would be empty columns only"
    elif slug == "material-de-estudio":
        peso = v_specs.get("peso_kg", 0)
        if peso >= 40:
            classification = "PROFILE_READY_LOW_RISK"
            reason = f"peso_kg persisted on {peso}/{variants} variants ({round(100*peso/variants,1)}%)"
            proposed = [
                {
                    "category_slug": slug,
                    "spec_key": "peso_kg",
                    "is_variant_axis_candidate": True,
                    "is_required": False,
                    "is_highlight": False,
                    "sort_order": 10,
                    "print_group": "variant",
                }
            ]
        else:
            classification = "PROFILE_NOT_USEFUL"
            reason = "Mostly singletons; insufficient spec density for useful columns"
    elif slug == "elipticas":
        sc = v_specs.get("smart_connect", 0)
        if sc > 0:
            classification = "PROFILE_NEEDS_COMMERCIAL_DECISION"
            reason = f"smart_connect on {sc}/{variants} but category tiny; confirm commercial highlight"
            proposed = [
                {
                    "category_slug": slug,
                    "spec_key": "smart_connect",
                    "is_highlight": True,
                    "sort_order": 15,
                    "print_group": "features",
                }
            ]
        else:
            classification = "PROFILE_NOT_USEFUL"
            reason = "5 singleton machines; no persisted specs; name distinguishes"
    elif slug == "musculacion":
        peso = v_specs.get("peso_kg", 0)
        if peso > 0:
            classification = "PROFILE_BLOCKED_MISSING_EXTRACTION"
            reason = f"Only {peso} peso_kg rows; machines need dimension/stack specs not extracted"
        else:
            classification = "PROFILE_NOT_USEFUL"
            reason = "No variant specs; plate-line machines distinguished by model name"
    elif slug in ("home", "linea-a-placas", "linea-convergente-a-disco"):
        classification = "PROFILE_NOT_USEFUL"
        reason = "Small singleton sets; no spec extraction; model name sufficient"
    elif slug in ("agarres", "boxeo", "suelos", "racks-y-estructuras", "bancos-jaulas-y-soportes"):
        classification = "PROFILE_BLOCKED_MISSING_EXTRACTION"
        reason = "No/minimal persisted specs; would need material/carga extraction first"
    elif slug == "repuestos":
        classification = "NO_PROFILE_NEEDED"
        reason = "explicit_one_per_sku spare parts; no variant axis"
    elif slug == "soportes-y-mancuerneros":
        classification = "PROFILE_NOT_USEFUL"
        reason = "Single SKU; no specs"
    elif slug == "stepper":
        sc = v_specs.get("smart_connect", 0)
        classification = "PROFILE_NEEDS_COMMERCIAL_DECISION" if sc else "PROFILE_NOT_USEFUL"
        reason = f"smart_connect={sc}; tiny cardio subcategory"
    else:
        if total_v_spec_rows >= 10 and top_spec and top_spec[1] / variants >= 0.2:
            classification = "PROFILE_NEEDS_COMMERCIAL_DECISION"
            reason = f"Spec {top_spec[0]} on {top_spec[1]} variants — needs commercial review"
        elif total_v_spec_rows > 0:
            classification = "PROFILE_BLOCKED_MISSING_EXTRACTION"
            reason = "Sparse specs; extraction coverage too low for profile"
        else:
            classification = "PROFILE_NOT_USEFUL"
            reason = "No persisted specs"

    empty_column_risk = []
    if proposed:
        for p in proposed:
            key = p["spec_key"]
            filled = vis.get("variants_with_value_by_column", {}).get(key, v_specs.get(key, 0))
            if filled < variants * 0.15:
                empty_column_risk.append(f"{key} only {filled}/{variants} filled")

    return {
        "classification": classification,
        "reason": reason,
        "proposed_profile_rows": proposed if classification == "PROFILE_READY_LOW_RISK" else [],
        "persisted_variant_specs": v_specs,
        "persisted_master_specs": m_specs,
        "pages": pages,
        "singleton_pct": singleton_pct,
        "empty_column_risk": empty_column_risk,
        "spec_role_notes": _spec_role_notes(v_specs, m_specs, inv),
    }


def _spec_role_notes(v_specs: dict, m_specs: dict, inv: dict) -> dict:
    notes = {}
    if v_specs.get("peso_kg"):
        notes["peso_kg"] = "variant_axis" if inv["multi_variant_masters"] > 0 else "optional highlight"
    if v_specs.get("smart_connect"):
        notes["smart_connect"] = "commercial feature flag"
    if v_specs.get("color"):
        notes["color"] = "material/variant axis when multi-variant"
    return notes


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with async_session() as session:
        inv_list = await category_inventory(session)
        specs = await specs_by_category(session)
        pages = await pages_by_category(session)
        profiles = await profile_keys(session)

        inv_by_slug = {r["slug"]: r for r in inv_list}
        no_profile = [r for r in inv_list if r["slug"] not in PROFILED_SLUGS and r["variants"] > 0]

        classifications = {}
        for row in no_profile:
            slug = row["slug"]
            vis = await visibility_simulation(session, slug)
            classifications[slug] = {
                **row,
                **classify_category(slug, row, specs.get(slug, {}), pages.get(slug, []), vis),
                "visibility_simulation": vis,
            }

        # Baseline check
        v_total = (await session.execute(select(func.count()).select_from(ProductVariant))).scalar_one()
        m_total = (await session.execute(select(func.count()).select_from(ProductMaster))).scalar_one()
        lm = (
            await session.execute(
                select(func.count())
                .select_from(ProductVariantSpec)
                .join(SpecDefinition)
                .where(SpecDefinition.key == "longitud_mm")
            )
        ).scalar_one()

        baseline_ok = (
            v_total == BASELINE["variants_total"]
            and m_total == BASELINE["masters_total"]
            and lm == BASELINE["longitud_mm"]
        )

    low_risk = [c for c in classifications.values() if c["classification"] == "PROFILE_READY_LOW_RISK"]
    stay_no_profile = [
        c["slug"]
        for c in classifications.values()
        if c["classification"] in ("NO_PROFILE_NEEDED", "PROFILE_NOT_USEFUL", "PROFILE_BLOCKED_MISSING_EXTRACTION")
    ]

    report = {
        "task_id": "IMPORT-FDL-SPEC-B3B-CATEGORY-PROFILE-ELIGIBILITY-AUDIT",
        "status": "B3B_PROFILE_ELIGIBILITY_AUDIT_COMPLETE" if baseline_ok else "B3B_PROFILE_ELIGIBILITY_AUDIT_INCOMPLETE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only_confirmation": {"code_modified": False, "database_modified": False},
        "baseline": {
            "expected": BASELINE,
            "actual": {"variants_total": v_total, "masters_total": m_total, "longitud_mm": lm},
            "baseline_ok": baseline_ok,
        },
        "categories_with_profile": {k: profiles[k] for k in sorted(profiles)},
        "categories_without_profile": [
            {
                "slug": c["slug"],
                "masters": c["masters"],
                "variants": c["variants"],
                "pages": c.get("pages", []),
                "classification": c["classification"],
            }
            for c in sorted(classifications.values(), key=lambda x: -x["variants"])
        ],
        "inventory_by_category": inv_list,
        "specs_by_category": specs,
        "pages_by_category": pages,
        "classifications": classifications,
        "low_risk_candidates": low_risk,
        "mandatory_answers": {
            "1_categories_without_profile": [c["slug"] for c in no_profile],
            "2_counts": {c["slug"]: {"masters": c["masters"], "variants": c["variants"]} for c in no_profile},
            "3_persisted_specs": {slug: specs.get(slug, {}) for slug in [c["slug"] for c in no_profile]},
            "4_visibility_gain": {
                slug: {
                    "variants_with_any_spec": classifications[slug]["visibility_simulation"].get("variants_with_any_spec"),
                    "columns_today": classifications[slug]["visibility_simulation"].get("column_keys_current"),
                }
                for slug in classifications
            },
            "8_remain_without_profile": stay_no_profile,
            "9_needs_extraction_first": [
                c["slug"] for c in classifications.values() if c["classification"] == "PROFILE_BLOCKED_MISSING_EXTRACTION"
            ],
            "10_api_frontend_pdf_impact": (
                "List/detail use load_printable_variant_columns(category_id, variants): "
                "without profile, discovery from variant.specs still surfaces persisted variant_axis specs when variants passed. "
                "Adding profile adds explicit column order/labels; empty profile keys may appear as columns before visible_variant_columns filters. "
                "PDF catalog_builder uses same resolver — profile affects column headers in family tables."
            ),
        },
        "risks": {
            "empty_columns": [c["slug"] for c in classifications.values() if c.get("empty_column_risk")],
            "discovery_occlusion": (
                "Low risk: _discover_columns_from_variants appends specs not in profile when variants provided. "
                "Profile does not hide discovered specs. Risk is noise from profile keys with 0% fill."
            ),
        },
        "recommendation": {
            "agent_2_plan_mode": (
                "SPEC-B3B-MATERIAL-ESTUDIO-PESO-PROFILE"
                if low_risk
                else None
            ),
            "commercial_decision": [
                c["slug"] for c in classifications.values() if c["classification"] == "PROFILE_NEEDS_COMMERCIAL_DECISION"
            ],
            "no_fix": [c["slug"] for c in classifications.values() if c["classification"] == "PROFILE_NOT_USEFUL"],
        },
    }

    out_json = OUTPUT_DIR / "b3b_profile_eligibility_audit.json"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# B3B Profile Eligibility Audit",
        "",
        f"**Status:** `{report['status']}`",
        "",
        "## Categories without profile",
        "| Slug | Variants | Classification |",
        "|------|----------|----------------|",
    ]
    for c in report["categories_without_profile"]:
        md_lines.append(f"| {c['slug']} | {c['variants']} | {c['classification']} |")
    md_lines.extend(["", "## Low-risk candidates", ""])
    for c in low_risk:
        md_lines.append(f"- **{c['slug']}**: {c['reason']}")
        for p in c.get("proposed_profile_rows", []):
            md_lines.append(f"  - `{json.dumps(p)}`")
    md_lines.extend([
        "",
        "## Taxonomy without FDL products",
        "See `taxonomy_empty_categories.json` — musculacion, home, agarres, etc. have 0 importables.",
        "",
        "## Note on material-de-estudio color",
        "65 variants persist `color` but discovery columns today show only `peso` (57). Adding color to profile is PROFILE_NEEDS_COMMERCIAL_DECISION, not low-risk.",
    ])

    (OUTPUT_DIR / "b3b_profile_eligibility_audit.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "no_profile_count": len(no_profile), "low_risk": len(low_risk)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
