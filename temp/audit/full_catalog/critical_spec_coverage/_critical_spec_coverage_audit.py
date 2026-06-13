#!/usr/bin/env python3
"""Read-only critical spec coverage audit — full FDL catalog."""
from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.database import async_session
from app.models import (
    Category,
    CategorySpecProfile,
    ImportProfile,
    ImportRow,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    Supplier,
)
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.spec_resolver import load_printable_variant_columns
from app.services.taxonomy_mapper import map_row_categories

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage")

WEIGHT_KG_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?\b", re.I)
WEIGHT_LB_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*lbs?\b", re.I)
COLOR_WORDS = re.compile(
    r"(?i)\b(negro|blanco|rojo|azul|verde|naranja|amarillo|gris|rosa|violeta|morado|marron|beige|plata|dorado|multicolor)\b"
)
LENGTH_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:mm|cms?|m)\b", re.I)
DIAMETER_RE = re.compile(r"(?i)diam(?:etro|\.?)\s*(\d+(?:[.,]\d+)?)\s*mm")
CAPACITY_RE = re.compile(r"(?i)(\d+)\s*balones?")

CRITICAL_AXIS_BY_CATEGORY: dict[str, list[str]] = {
    "discos": ["peso_kg"],
    "cross-training": ["peso_kg", "peso_lb", "color"],
    "mancuernas": ["peso_kg"],
    "barras": ["peso_kg", "longitud_mm"],
    "cardio": [],
    "bicicletas-estaticas": ["smart_connect"],
    "remos": ["smart_connect"],
    "cintas-de-correr": ["smart_connect"],
    "material-de-estudio": [],
    "musculacion": [],
    "agarres": [],
    "boxeo": [],
    "suelos": [],
    "racks-y-estructuras": [],
    "bancos-jaulas-y-soportes": [],
    "soportes-y-mancuerneros": [],
    "repuestos": [],
    "elipticas": [],
    "stepper": [],
    "linea-a-placas": [],
    "linea-convergente-a-disco": [],
    "home": [],
}

GROUPING_WEIGHT_FAMILIES = re.compile(
    r"^(numeric_suffix_family|fdl_sku_family|cross_training_bumper_family|cross_training_block_family|hyphen_suffix_family):"
)


async def load_db_inventory(session) -> dict[str, Any]:
    spec_defs = {
        row.key: str(row.id)
        for row in (await session.execute(select(SpecDefinition))).scalars().all()
    }
    profiles_by_cat: dict[str, list[str]] = defaultdict(list)
    rows = (
        await session.execute(
            select(Category.slug, SpecDefinition.key)
            .join(CategorySpecProfile, CategorySpecProfile.category_id == Category.id)
            .join(SpecDefinition, SpecDefinition.id == CategorySpecProfile.spec_definition_id)
        )
    ).all()
    for slug, key in rows:
        profiles_by_cat[slug].append(key)

    variants = (
        await session.execute(
            select(
                ProductVariant.sku,
                ProductVariant.display_name,
                ProductMaster.master_key,
                ProductMaster.name,
                Category.slug,
                Category.name,
                ProductMaster.id,
            )
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .outerjoin(Category, ProductMaster.category_id == Category.id)
        )
    ).all()

    import_rows = (
        await session.execute(
            select(
                ImportRow.sku,
                ImportRow.source_page,
                ImportRow.grouping_reason,
                ImportRow.parsed_variant_specs_raw,
                ImportRow.parsed_common_specs_raw,
                ImportRow.raw_name,
                ImportRow.normalized_name,
            ).where(ImportRow.sku.isnot(None))
        )
    ).all()
    import_by_sku: dict[str, dict] = {}
    for sku, page, greason, pvar, pcom, raw, norm in import_rows:
        key = (sku or "").upper()
        if key not in import_by_sku:
            import_by_sku[key] = {
                "source_page": page,
                "grouping_reason": greason,
                "parsed_variant_specs_raw": pvar,
                "parsed_common_specs_raw": pcom,
                "raw_name": raw,
                "normalized_name": norm,
            }

    spec_rows = (
        await session.execute(
            select(
                ProductVariant.sku,
                SpecDefinition.key,
                ProductVariantSpec.value_number,
                ProductVariantSpec.value_text,
                ProductVariantSpec.value_boolean,
            )
            .join(ProductVariantSpec, ProductVariantSpec.variant_id == ProductVariant.id)
            .join(SpecDefinition, SpecDefinition.id == ProductVariantSpec.spec_definition_id)
        )
    ).all()
    db_specs: dict[str, dict[str, Any]] = defaultdict(dict)
    for sku, key, num, text, boolean in spec_rows:
        if boolean is not None:
            db_specs[sku][key] = boolean
        elif num is not None:
            db_specs[sku][key] = float(num)
        elif text is not None:
            db_specs[sku][key] = text

    masters: dict[str, list[dict]] = defaultdict(list)
    for row in variants:
        sku, dname, mk, mname, slug, cname, mid = row
        imp = import_by_sku.get((sku or "").upper(), {})
        masters[mk].append(
            {
                "sku": sku,
                "display_name": dname,
                "master_name": mname,
                "category_slug": slug,
                "category_name": cname,
                "page": imp.get("source_page"),
                "grouping_reason": imp.get("grouping_reason"),
                "parser_variant_specs": imp.get("parsed_variant_specs_raw") or {},
                "parser_common_specs": imp.get("parsed_common_specs_raw") or {},
                "db_specs": db_specs.get(sku, {}),
                "raw_name": imp.get("raw_name"),
                "normalized_name": imp.get("normalized_name"),
                "master_id": str(mid),
            }
        )
    return {
        "spec_definitions": sorted(spec_defs.keys()),
        "profiles_by_category": dict(profiles_by_cat),
        "masters": dict(masters),
        "variant_count": len(variants),
        "master_count": len(masters),
        "db_spec_row_count": len(spec_rows),
    }


def evidence_in_text(text: str) -> dict[str, bool]:
    t = text or ""
    return {
        "peso_kg": bool(WEIGHT_KG_RE.search(t)),
        "peso_lb": bool(WEIGHT_LB_RE.search(t)),
        "color": bool(COLOR_WORDS.search(t)),
        "longitud_mm": bool(LENGTH_RE.search(t)),
        "diametro_mm": bool(DIAMETER_RE.search(t)),
        "capacidad_balones": bool(CAPACITY_RE.search(t)),
        "smart_connect": bool(re.search(r"(?i)smart\s*(?:connect|conect)", t)),
    }


def classify_master_gaps(master_key: str, members: list[dict]) -> list[dict]:
    gaps: list[dict] = []
    if not members:
        return gaps
    slug = members[0]["category_slug"] or "unknown"
    pages = sorted({m["page"] for m in members if m["page"]})
    variant_count = len(members)
    grouping_reasons = {m["grouping_reason"] for m in members if m["grouping_reason"]}
    is_weight_family = any(
        gr and GROUPING_WEIGHT_FAMILIES.match(gr or "") for gr in grouping_reasons
    )
    is_singleton = variant_count == 1

    db_spec_sets = [frozenset(m["db_specs"].items()) for m in members]
    all_same_specs = len({s for s in db_spec_sets}) == 1 and db_spec_sets[0]
    all_empty_db = all(len(m["db_specs"]) == 0 for m in members)

    names = [m["display_name"] or m["normalized_name"] or "" for m in members]
    names_unique = len(set(names)) == len(names)

    for m in members:
        text = " ".join(filter(None, [m["raw_name"], m["normalized_name"], m["display_name"]]))
        ev = evidence_in_text(text)
        parser = m["parser_variant_specs"] or {}
        db = m["db_specs"] or {}
        for spec_key, present in ev.items():
            if not present:
                continue
            if spec_key in parser and spec_key not in db:
                gaps.append(
                    {
                        "classification": "SPEC_EXTRACTION_BUG",
                        "severity": "P2",
                        "pattern": f"parser_has_{spec_key}_not_persisted",
                        "sku": m["sku"],
                        "master_key": master_key,
                        "category_slug": slug,
                        "pages": pages,
                        "evidence": text[:120],
                    }
                )
            elif spec_key not in parser and spec_key not in db and is_weight_family:
                gaps.append(
                    {
                        "classification": "SPEC_EXTRACTION_BUG",
                        "severity": "P1" if variant_count > 1 else "P2",
                        "pattern": f"name_evidence_{spec_key}_missing",
                        "sku": m["sku"],
                        "master_key": master_key,
                        "category_slug": slug,
                        "pages": pages,
                        "evidence": text[:120],
                    }
                )

    if variant_count > 1 and is_weight_family:
        missing_axis = [
            m["sku"]
            for m in members
            if "peso_kg" not in m["db_specs"] and "peso_lb" not in m["db_specs"]
        ]
        if missing_axis:
            gaps.append(
                {
                    "classification": "P1_CRITICAL_SPEC_GAP",
                    "severity": "P1",
                    "pattern": "multi_variant_weight_family_missing_peso",
                    "master_key": master_key,
                    "category_slug": slug,
                    "pages": pages,
                    "variant_count": variant_count,
                    "skus": missing_axis,
                }
            )
        elif all_same_specs or (all_empty_db and not names_unique):
            gaps.append(
                {
                    "classification": "P1_CRITICAL_SPEC_GAP",
                    "severity": "P1",
                    "pattern": "multi_variant_indistinguishable_specs",
                    "master_key": master_key,
                    "category_slug": slug,
                    "pages": pages,
                    "variant_count": variant_count,
                }
            )

    if variant_count > 1 and any("color" in (m["grouping_reason"] or "") for m in members):
        color_missing = [m["sku"] for m in members if "color" not in m["db_specs"]]
        if color_missing:
            gaps.append(
                {
                    "classification": "SPEC_EXTRACTION_BUG",
                    "severity": "P1",
                    "pattern": "color_family_missing_color_spec",
                    "master_key": master_key,
                    "category_slug": slug,
                    "pages": pages,
                    "skus": color_missing,
                }
            )

    if is_singleton and all_empty_db and names_unique:
        gaps.append(
            {
                "classification": "P3_OPTIONAL_SPEC_BACKLOG",
                "severity": "P3",
                "pattern": "singleton_empty_specs_name_distinguishable",
                "master_key": master_key,
                "category_slug": slug,
                "pages": pages,
                "sku": members[0]["sku"],
                "display_name": names[0][:80],
            }
        )

    return gaps


def build_category_matrix(masters: dict[str, list[dict]], profiles: dict[str, list[str]]) -> list[dict]:
    by_cat: dict[str, dict] = defaultdict(
        lambda: {
            "variants": 0,
            "masters": 0,
            "multi_variant_masters": 0,
            "empty_spec_variants": 0,
            "spec_counts": Counter(),
            "p1_gaps": 0,
            "p2_gaps": 0,
        }
    )
    for mk, members in masters.items():
        slug = members[0]["category_slug"] or "unknown"
        cat = by_cat[slug]
        cat["variants"] += len(members)
        cat["masters"] += 1
        if len(members) > 1:
            cat["multi_variant_masters"] += 1
        for m in members:
            if not m["db_specs"]:
                cat["empty_spec_variants"] += 1
            for k in m["db_specs"]:
                cat["spec_counts"][k] += 1

    matrix = []
    for slug, data in sorted(by_cat.items()):
        critical = CRITICAL_AXIS_BY_CATEGORY.get(slug, [])
        profile_keys = profiles.get(slug, [])
        coverage = {}
        for key in critical:
            if data["variants"]:
                coverage[key] = round(100.0 * data["spec_counts"].get(key, 0) / data["variants"], 1)
            else:
                coverage[key] = 0.0
        matrix.append(
            {
                "category_slug": slug,
                "variants": data["variants"],
                "masters": data["masters"],
                "multi_variant_masters": data["multi_variant_masters"],
                "empty_spec_variants": data["empty_spec_variants"],
                "empty_spec_pct": round(100.0 * data["empty_spec_variants"] / max(data["variants"], 1), 1),
                "profile_specs": profile_keys,
                "critical_specs_expected": critical,
                "critical_coverage_pct": coverage,
                "top_db_specs": dict(data["spec_counts"].most_common(8)),
            }
        )
    return matrix


async def profile_visibility_gaps(session, profiles: dict[str, list[str]]) -> list[dict]:
    gaps = []
    categories = (await session.execute(select(Category))).scalars().all()
    for cat in categories:
        slug = cat.slug
        if slug in profiles:
            continue
        columns = await load_printable_variant_columns(session, cat.id, variants=[])
        if columns:
            gaps.append(
                {
                    "classification": "PROFILE_VISIBILITY_GAP",
                    "severity": "P3",
                    "category_slug": slug,
                    "note": "category has printable columns via inheritance but no explicit profile rows",
                }
            )
    # Categories with multi-variant but no peso profile when expected
    for slug, keys in profiles.items():
        if slug in ("discos", "mancuernas", "barras") and "peso_kg" not in keys:
            gaps.append(
                {
                    "classification": "PROFILE_VISIBILITY_GAP",
                    "severity": "P1",
                    "category_slug": slug,
                    "missing": "peso_kg",
                }
            )
    return gaps


async def pipeline_drift_check(session, pdf) -> dict:
    parsed = [r for r in parse_pdf(pdf) if r.sku]
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
    mapped = await map_row_categories(session, parsed, supplier.id, profile.id)
    apply_grouping(mapped, {"grouping": grouping})
    parser_with_specs = sum(1 for r in mapped if r.parsed_variant_specs_raw)
    parser_empty = len(mapped) - parser_with_specs
    importable = sum(1 for r in mapped if can_confirm_row(r)[0])
    return {
        "rows_parsed": len(mapped),
        "rows_importable": importable,
        "rows_blocked": len(mapped) - importable,
        "parser_variants_with_specs": parser_with_specs,
        "parser_variants_empty_specs": parser_empty,
    }


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = resolve_pdf_path(None)

    async with async_session() as session:
        inv = await load_db_inventory(session)
        pipeline = await pipeline_drift_check(session, pdf)
        profile_gaps = await profile_visibility_gaps(session, inv["profiles_by_category"])

    all_gaps: list[dict] = []
    for mk, members in inv["masters"].items():
        all_gaps.extend(classify_master_gaps(mk, members))
    all_gaps.extend(profile_gaps)

    # Source not available patterns
    source_unavailable = []
    for mk, members in inv["masters"].items():
        for m in members:
            text = m["display_name"] or ""
            if re.search(r"(?i)\b(material|acabado|cromado|aluminio|goma|cuero)\b", text):
                if "material" not in m["db_specs"] and "material" not in (m["parser_variant_specs"] or {}):
                    source_unavailable.append(
                        {
                            "classification": "SOURCE_DATA_NOT_AVAILABLE",
                            "severity": "P3",
                            "sku": m["sku"],
                            "pattern": "material_mentioned_not_structured",
                            "note": "Free-text mention only; no reliable enum without commercial taxonomy",
                        }
                    )

    cat_matrix = build_category_matrix(inv["masters"], inv["profiles_by_category"])

    p1 = [g for g in all_gaps if g.get("severity") == "P1" or g.get("classification") == "P1_CRITICAL_SPEC_GAP"]
    p2 = [g for g in all_gaps if g.get("severity") == "P2" or g.get("classification") == "SPEC_EXTRACTION_BUG"]
    p3 = [g for g in all_gaps if g.get("severity") == "P3"]

    empty_variants = sum(1 for mk, ms in inv["masters"].items() for m in ms if not m["db_specs"])
    multi_masters = sum(1 for ms in inv["masters"].values() if len(ms) > 1)

    # Deduplicate p1 by pattern+master
    seen = set()
    p1_unique = []
    for g in p1:
        key = (g.get("pattern"), g.get("master_key"), g.get("sku"))
        if key not in seen:
            seen.add(key)
            p1_unique.append(g)

    global_metrics = {
        "variants_total": inv["variant_count"],
        "masters_total": inv["master_count"],
        "db_spec_rows_total": inv["db_spec_row_count"],
        "variants_empty_db_specs": empty_variants,
        "variants_empty_db_specs_pct": round(100.0 * empty_variants / max(inv["variant_count"], 1), 1),
        "multi_variant_masters": multi_masters,
        "parser_coverage": pipeline,
        "p1_gap_count": len(p1_unique),
        "p2_gap_count": len(p2),
        "p3_gap_count": len(p3),
        "spec_definitions": inv["spec_definitions"],
    }

    # Recommend first batch: aggregate P1 patterns
    p1_patterns = Counter(g.get("pattern") for g in p1_unique)
    first_batch = None
    if p1_patterns:
        top_pattern, count = p1_patterns.most_common(1)[0]
        first_batch = {
            "batch_id": "SPEC-B1-WEIGHT-AXIS-COMPLETENESS",
            "pattern": top_pattern,
            "affected_count": count,
            "agent": "Agent 2 Plan Mode",
            "scope": "Systemic weight/color axis extraction for numeric_suffix and bumper families — only where name/header evidence exists",
        }

    report = {
        "task_id": "IMPORT-FDL-CRITICAL-SPEC-COVERAGE-AUDIT",
        "status": "CRITICAL_SPEC_COVERAGE_AUDIT_COMPLETE",
        "read_only": True,
        "global_metrics": global_metrics,
        "category_matrix": cat_matrix,
        "prioritized_gaps": {
            "P1": p1_unique[:40],
            "P2": p2[:40],
            "P3": p3[:30],
        },
        "pattern_summary": dict(Counter(g.get("pattern") for g in all_gaps).most_common(20)),
        "classification_counts": dict(Counter(g.get("classification") for g in all_gaps)),
        "source_unavailable_samples": source_unavailable[:20],
        "recommended_batches": [
            first_batch,
            {
                "batch_id": "SPEC-B2-CARDIO-PROFILE-ENRICHMENT",
                "scope": "Optional dimension/feature specs for cardio where PDF has explicit tokens only",
                "severity": "P3",
            },
            {
                "batch_id": "SPEC-B3-MATERIAL-ACABADO",
                "scope": "Commercial decision required before enum extraction",
                "severity": "P3",
                "note": "SOURCE_DATA_NOT_AVAILABLE for most rows",
            },
        ],
        "answers": {
            "categories_needing_variant_specs": [
                "discos",
                "cross-training",
                "mancuernas",
                "barras",
            ],
            "explicit_evidence_specs": [
                "peso_kg",
                "peso_lb",
                "color",
                "longitud_mm",
                "capacidad_balones",
                "smart_connect",
            ],
            "master_level_specs": ["material", "casquillo", "carga_maxima_kg", "diametro_casquillo_mm"],
            "variant_level_specs": ["peso_kg", "peso_lb", "color", "smart_connect", "unidades_pack", "capacidad_balones"],
            "variant_axis_specs": ["peso_kg", "peso_lb", "color"],
            "commercially_distinguishable_empty_specs": empty_variants,
            "regression_pages_safe": [11, 12, 13, 14],
        },
    }

    out = OUTPUT_DIR / "critical_spec_coverage_audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = OUTPUT_DIR / "critical_spec_coverage_audit.md"
    md.write_text(
        "\n".join(
            [
                "# Critical Spec Coverage Audit",
                "",
                f"**Status:** {report['status']}",
                "",
                "## Global metrics",
                f"- Variants: {global_metrics['variants_total']}",
                f"- Empty DB specs: {global_metrics['variants_empty_db_specs']} ({global_metrics['variants_empty_db_specs_pct']}%)",
                f"- P1 gaps: {global_metrics['p1_gap_count']}",
                f"- P2 gaps: {global_metrics['p2_gap_count']}",
                "",
                "## First recommended batch",
                json.dumps(first_batch, ensure_ascii=False, indent=2) if first_batch else "None",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "output": str(out), "metrics": global_metrics}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
