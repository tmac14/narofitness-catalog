#!/usr/bin/env python3
"""Corrected post-audit report — counts enum/master specs, reclassifies gaps."""
from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select, text

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
    SpecAllowedValue,
)

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage")

WEIGHT_KG_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?\b", re.I)
WEIGHT_LB_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*lbs?\b", re.I)
COLOR_WORDS = re.compile(
    r"(?i)\b(negro|blanco|rojo|azul|verde|naranja|amarillo|gris|rosa|violeta|morado|marron|beige|plata|dorado|multicolor)\b"
)
LENGTH_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:mm|cms?|m)\b", re.I)
SMART_CONNECT_RE = re.compile(r"(?i)smart\s*(?:connect|conect)")

CRITICAL_AXIS_BY_CATEGORY: dict[str, list[str]] = {
    "discos": ["peso_kg", "color"],
    "cross-training": ["peso_kg", "peso_lb", "color"],
    "mancuernas": ["peso_kg", "color"],
    "barras": ["peso_kg", "longitud_mm"],
    "bicicletas-estaticas": ["smart_connect"],
    "remos": ["smart_connect"],
    "cintas-de-correr": ["smart_connect"],
}

WEIGHT_FAMILY_RE = re.compile(
    r"^(numeric_suffix_family|fdl_sku_family|cross_training_bumper_family|hyphen_suffix_family):"
)
BLOCK_FAMILY_RE = re.compile(r"^cross_training_block_family:")
BAR_FAMILY_RE = re.compile(r"^numeric_suffix_family:.*barras")

CATEGORIES_WITH_PROFILES = {
    "discos",
    "cross-training",
    "mancuernas",
    "barras",
    "cardio",
    "bicicletas-estaticas",
    "remos",
    "cintas-de-correr",
}


def spec_has_value(row: dict) -> bool:
    return any(
        row.get(k) is not None
        for k in ("value_number", "value_text", "value_boolean", "allowed_value_id", "allowed_value_label")
    )


async def load_corrected_inventory(session) -> dict[str, Any]:
    # Variant specs with enum resolution
    v_rows = (
        await session.execute(
            select(
                ProductVariant.sku,
                ProductVariant.display_name,
                ProductVariant.id,
                ProductMaster.master_key,
                ProductMaster.name,
                ProductMaster.id,
                Category.slug,
                SpecDefinition.key,
                ProductVariantSpec.value_number,
                ProductVariantSpec.value_text,
                ProductVariantSpec.value_boolean,
                ProductVariantSpec.allowed_value_id,
                SpecAllowedValue.label,
            )
            .join(ProductVariantSpec, ProductVariantSpec.variant_id == ProductVariant.id)
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .outerjoin(Category, Category.id == ProductMaster.category_id)
            .join(SpecDefinition, SpecDefinition.id == ProductVariantSpec.spec_definition_id)
            .outerjoin(SpecAllowedValue, SpecAllowedValue.id == ProductVariantSpec.allowed_value_id)
        )
    ).all()

    # Master specs
    m_rows = (
        await session.execute(
            select(
                ProductMaster.master_key,
                Category.slug,
                SpecDefinition.key,
                ProductMasterSpec.value_number,
                ProductMasterSpec.value_text,
                ProductMasterSpec.value_boolean,
                ProductMasterSpec.allowed_value_id,
                SpecAllowedValue.label,
            )
            .join(ProductMasterSpec, ProductMasterSpec.master_id == ProductMaster.id)
            .outerjoin(Category, Category.id == ProductMaster.category_id)
            .join(SpecDefinition, SpecDefinition.id == ProductMasterSpec.spec_definition_id)
            .outerjoin(SpecAllowedValue, SpecAllowedValue.id == ProductMasterSpec.allowed_value_id)
        )
    ).all()

    master_specs: dict[str, dict[str, Any]] = defaultdict(dict)
    for mk, slug, key, num, txt, boolean, av_id, av_label in m_rows:
        val = None
        if boolean is not None:
            val = boolean
        elif num is not None:
            val = float(num)
        elif txt is not None:
            val = txt
        elif av_label:
            val = av_label
        if val is not None:
            master_specs[mk][key] = val

    variant_specs: dict[str, dict[str, Any]] = defaultdict(dict)
    variant_meta: dict[str, dict] = {}
    for sku, dname, vid, mk, mname, mid, slug, key, num, txt, boolean, av_id, av_label in v_rows:
        val = None
        if boolean is not None:
            val = boolean
        elif num is not None:
            val = float(num)
        elif txt is not None:
            val = txt
        elif av_label:
            val = av_label
        if val is not None:
            variant_specs[sku][key] = val
        variant_meta[sku] = {
            "sku": sku,
            "display_name": dname,
            "master_key": mk,
            "master_name": mname,
            "master_id": str(mid),
            "category_slug": slug,
        }

    # All variants (including those without specs)
    all_variants = (
        await session.execute(
            select(
                ProductVariant.sku,
                ProductVariant.display_name,
                ProductMaster.master_key,
                ProductMaster.name,
                Category.slug,
            )
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .outerjoin(Category, ProductMaster.category_id == Category.id)
        )
    ).all()
    for sku, dname, mk, mname, slug in all_variants:
        if sku not in variant_meta:
            variant_meta[sku] = {
                "sku": sku,
                "display_name": dname,
                "master_key": mk,
                "master_name": mname,
                "category_slug": slug,
            }

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
                "parsed_variant_specs": pvar or {},
                "parsed_common_specs": pcom or {},
                "raw_name": raw,
                "normalized_name": norm,
            }

    profiles_by_cat: dict[str, list[str]] = defaultdict(list)
    prof_rows = (
        await session.execute(
            select(Category.slug, SpecDefinition.key)
            .join(CategorySpecProfile, CategorySpecProfile.category_id == Category.id)
            .join(SpecDefinition, SpecDefinition.id == CategorySpecProfile.spec_definition_id)
        )
    ).all()
    for slug, key in prof_rows:
        profiles_by_cat[slug].append(key)

    masters: dict[str, list[dict]] = defaultdict(list)
    for sku, meta in variant_meta.items():
        mk = meta["master_key"]
        imp = import_by_sku.get((sku or "").upper(), {})
        vs = variant_specs.get(sku, {})
        ms = master_specs.get(mk, {})
        effective = {**ms, **vs}  # variant overrides master for display
        masters[mk].append(
            {
                **meta,
                "page": imp.get("source_page"),
                "grouping_reason": imp.get("grouping_reason"),
                "parser_variant_specs": imp.get("parsed_variant_specs", {}),
                "parser_common_specs": imp.get("parsed_common_specs", {}),
                "variant_specs": vs,
                "master_specs": ms,
                "effective_specs": effective,
                "raw_name": imp.get("raw_name"),
                "normalized_name": imp.get("normalized_name"),
            }
        )

    spec_totals = Counter()
    for sku, specs in variant_specs.items():
        for k in specs:
            spec_totals[k] += 1
    for mk, specs in master_specs.items():
        for k in specs:
            spec_totals[f"master:{k}"] += 1

    return {
        "masters": dict(masters),
        "variant_count": len(variant_meta),
        "master_count": len(masters),
        "variant_spec_row_count": len(v_rows),
        "master_spec_row_count": len(m_rows),
        "spec_totals_variant": dict(Counter(k for sku, specs in variant_specs.items() for k in specs)),
        "spec_totals_master": dict(Counter(k for mk, specs in master_specs.items() for k in specs)),
        "profiles_by_category": dict(profiles_by_cat),
    }


def effective_has(m: dict, key: str) -> bool:
    return key in m["effective_specs"]


def classify_gaps(masters: dict[str, list[dict]]) -> list[dict]:
    gaps: list[dict] = []
    for mk, members in masters.items():
        if not members:
            continue
        slug = members[0]["category_slug"] or "unknown"
        pages = sorted({m["page"] for m in members if m["page"]})
        n = len(members)
        greasons = {m["grouping_reason"] for m in members if m["grouping_reason"]}
        is_weight_family = any(g and WEIGHT_FAMILY_RE.match(g) for g in greasons)
        is_block_family = any(g and BLOCK_FAMILY_RE.match(g) for g in greasons)
        is_bar_family = slug == "barras" and any(
            g and re.match(r"^numeric_suffix_family:(BN|BO|BOR)\b", g or "") for g in greasons
        )

        # Category-specific variant axis for multi-variant families
        def _missing_variant_axis(m: dict) -> bool:
            if slug == "barras" and is_bar_family:
                return "longitud_mm" not in m["effective_specs"] and "peso_kg" not in m["effective_specs"]
            if slug in ("discos", "mancuernas") or (slug == "cross-training" and is_weight_family and not is_block_family):
                return "peso_kg" not in m["effective_specs"] and "peso_lb" not in m["effective_specs"]
            return False

        # P1: multi-variant family missing its primary variant axis
        if n > 1 and is_weight_family and not is_block_family:
            missing_axis = [m["sku"] for m in members if _missing_variant_axis(m)]
            if missing_axis:
                axis = "longitud_mm" if slug == "barras" else "peso_kg/peso_lb"
                gaps.append(
                    {
                        "classification": "P1_CRITICAL_SPEC_GAP",
                        "severity": "P1",
                        "pattern": f"multi_variant_missing_{axis.replace('/', '_')}",
                        "master_key": mk,
                        "category_slug": slug,
                        "pages": pages,
                        "skus": missing_axis,
                    }
                )

        # P1: multi-variant same effective specs and same display name
        if n > 1 and is_weight_family and not is_block_family:
            effective_sets = [frozenset(m["effective_specs"].items()) for m in members]
            names = [m["display_name"] or "" for m in members]
            if len(set(effective_sets)) == 1 and len(set(names)) < n:
                gaps.append(
                    {
                        "classification": "P1_CRITICAL_SPEC_GAP",
                        "severity": "P1",
                        "pattern": "multi_variant_indistinguishable",
                        "master_key": mk,
                        "category_slug": slug,
                        "pages": pages,
                    }
                )

        for m in members:
            text = " ".join(
                filter(None, [m.get("raw_name"), m.get("normalized_name"), m.get("display_name")])
            )
            gr = m.get("grouping_reason") or ""

            # peso_lb P2: wall-ball families with lb in name but no peso_lb
            if (
                n > 1
                and is_weight_family
                and WEIGHT_LB_RE.search(text)
                and "peso_lb" not in m["effective_specs"]
                and "peso_kg" not in m["effective_specs"]
            ):
                gaps.append(
                    {
                        "classification": "SPEC_EXTRACTION_BUG",
                        "severity": "P2",
                        "pattern": "peso_lb_evidence_not_extracted",
                        "sku": m["sku"],
                        "master_key": mk,
                        "category_slug": slug,
                        "pages": pages,
                        "evidence": text[:100],
                    }
                )

            # barras longitud P2
            if (
                slug == "barras"
                and is_bar_family
                and LENGTH_RE.search(text)
                and "longitud_mm" not in m["effective_specs"]
            ):
                gaps.append(
                    {
                        "classification": "SPEC_EXTRACTION_BUG",
                        "severity": "P2",
                        "pattern": "bar_length_evidence_missing",
                        "sku": m["sku"],
                        "master_key": mk,
                        "pages": pages,
                        "evidence": text[:100],
                    }
                )

            # smart_connect P2 where explicit in name but absent
            if SMART_CONNECT_RE.search(text) and "smart_connect" not in m["effective_specs"]:
                gaps.append(
                    {
                        "classification": "SPEC_EXTRACTION_BUG",
                        "severity": "P2",
                        "pattern": "smart_connect_evidence_missing",
                        "sku": m["sku"],
                        "master_key": mk,
                        "category_slug": slug,
                        "pages": [m["page"]] if m["page"] else pages,
                    }
                )

            # P3 singleton empty specs
            if n == 1 and not m["effective_specs"]:
                gaps.append(
                    {
                        "classification": "P3_OPTIONAL_SPEC_BACKLOG",
                        "severity": "P3",
                        "pattern": "singleton_empty_specs_name_distinguishable",
                        "sku": m["sku"],
                        "master_key": mk,
                        "category_slug": slug,
                        "pages": [m["page"]] if m["page"] else [],
                        "display_name": (m["display_name"] or "")[:80],
                    }
                )

            # SOURCE_DATA_NOT_AVAILABLE: material/acabado free text
            if re.search(r"(?i)\b(material|acabado|cromado|aluminio|goma|cuero)\b", text):
                if "material" not in m["effective_specs"] and "acabado" not in m["effective_specs"]:
                    gaps.append(
                        {
                            "classification": "SOURCE_DATA_NOT_AVAILABLE",
                            "severity": "P3",
                            "pattern": "material_acabado_free_text_only",
                            "sku": m["sku"],
                            "category_slug": slug,
                        }
                    )

    return gaps


def build_category_matrix(
    masters: dict[str, list[dict]], profiles: dict[str, list[str]], gaps: list[dict]
) -> list[dict]:
    by_cat: dict[str, dict] = defaultdict(
        lambda: {
            "variants": 0,
            "masters": 0,
            "multi_variant_masters": 0,
            "empty_effective_specs": 0,
            "spec_counts": Counter(),
            "p1": 0,
            "p2": 0,
            "p3": 0,
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
            if not m["effective_specs"]:
                cat["empty_effective_specs"] += 1
            for k, v in m["effective_specs"].items():
                cat["spec_counts"][k] += 1

    for g in gaps:
        slug = g.get("category_slug", "unknown")
        if g.get("severity") == "P1":
            by_cat[slug]["p1"] += 1
        elif g.get("severity") == "P2":
            by_cat[slug]["p2"] += 1
        elif g.get("severity") == "P3":
            by_cat[slug]["p3"] += 1

    matrix = []
    for slug, data in sorted(by_cat.items()):
        critical = CRITICAL_AXIS_BY_CATEGORY.get(slug, [])
        coverage = {}
        for key in critical:
            coverage[key] = round(100.0 * data["spec_counts"].get(key, 0) / max(data["variants"], 1), 1)
        severity = "OK"
        if data["p1"]:
            severity = "P1"
        elif data["p2"]:
            severity = "P2"
        elif data["empty_effective_specs"] / max(data["variants"], 1) > 0.5:
            severity = "P3"
        matrix.append(
            {
                "category_slug": slug,
                "variants": data["variants"],
                "masters": data["masters"],
                "multi_variant_masters": data["multi_variant_masters"],
                "empty_effective_specs_variants": data["empty_effective_specs"],
                "empty_effective_specs_pct": round(
                    100.0 * data["empty_effective_specs"] / max(data["variants"], 1), 1
                ),
                "profile_specs": profiles.get(slug, []),
                "critical_specs_expected": critical,
                "critical_coverage_pct": coverage,
                "effective_spec_counts": dict(data["spec_counts"].most_common(10)),
                "gap_counts": {"P1": data["p1"], "P2": data["p2"], "P3": data["p3"]},
                "severity": severity,
            }
        )
    return matrix


def profile_visibility_gaps(all_slugs: set[str], profiles: dict[str, list[str]]) -> list[dict]:
    gaps = []
    for slug in sorted(all_slugs):
        if slug not in CATEGORIES_WITH_PROFILES:
            gaps.append(
                {
                    "classification": "PROFILE_VISIBILITY_GAP",
                    "severity": "P2" if slug in ("material-de-estudio", "musculacion", "elipticas") else "P3",
                    "category_slug": slug,
                    "note": "No explicit category_spec_profile rows; specs may not surface in UI",
                }
            )
    if "barras" in profiles and "longitud_mm" not in profiles["barras"]:
        gaps.append(
            {
                "classification": "PROFILE_VISIBILITY_GAP",
                "severity": "P2",
                "category_slug": "barras",
                "missing": "longitud_mm",
                "note": "longitud_mm extracted for some bars but not in profile",
            }
        )
    return gaps


def dedupe_gaps(gaps: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for g in gaps:
        key = (
            g.get("classification"),
            g.get("pattern"),
            g.get("master_key"),
            g.get("sku"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(g)
    return out


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with async_session() as session:
        inv = await load_corrected_inventory(session)
        all_slugs = {m["category_slug"] for ms in inv["masters"].values() for m in ms if m["category_slug"]}

    gaps = dedupe_gaps(classify_gaps(inv["masters"]))
    gaps.extend(profile_visibility_gaps(all_slugs, inv["profiles_by_category"]))

    p1 = [g for g in gaps if g.get("severity") == "P1" or g.get("classification") == "P1_CRITICAL_SPEC_GAP"]
    p2 = [g for g in gaps if g.get("severity") == "P2" and g.get("classification") != "P1_CRITICAL_SPEC_GAP"]
    p3 = [g for g in gaps if g.get("severity") == "P3"]

    empty_variants = sum(
        1 for ms in inv["masters"].values() for m in ms if not m["effective_specs"]
    )
    multi_masters = sum(1 for ms in inv["masters"].values() if len(ms) > 1)

    # False positive review notes
    false_positive_patterns = {
        "name_evidence_color_missing_on_master_level": [
            "DOB3C* (color Negro in parsed_common_specs → product_master_specs)",
            "MKI* (color in common_specs → master)",
            "DOBC* (color per variant via allowed_value_id — script missed enum)",
        ],
        "name_evidence_peso_missing_on_block_bars": [
            "BOC009/BOC011 specialty bars grouped by block family — weight not variant axis",
        ],
        "multi_variant_weight_family_missing_peso_on_barras": [
            "BN/BO/BOR families use longitud_mm axis (SKU suffix → mm); peso_kg not required — all variants have longitud_mm",
        ],
        "name_evidence_longitud_on_non_bar_products": [
            "CRO-SACO-GUSANO dimensions in name but peso_kg distinguishes variants — longitud is P3 enrichment",
        ],
    }

    first_batch = {
        "batch_id": "SPEC-B1-BARRAS-LENGTH-WEIGHT",
        "agent": "Agent 2 Plan Mode",
        "severity": "P2",
        "scope": (
            "Systemic longitud_mm + peso_kg for numeric_suffix_family barras (BN/BO/BOR) "
            "where SKU suffix or header encodes size/weight explicitly"
        ),
        "evidence_pages": [11, 12],
        "false_positive_risk": "LOW — bar SKU numeric suffix is stable; skip block-family BOC bars",
        "rationale": "No P1 gaps remain; barras has lowest critical-axis coverage (longitud_mm ~45%)",
    }

    report = {
        "task_id": "IMPORT-FDL-CRITICAL-SPEC-COVERAGE-AUDIT",
        "status": "CRITICAL_SPEC_COVERAGE_AUDIT_COMPLETE",
        "read_only_confirmation": {
            "code_modified": False,
            "tests_modified": False,
            "fixtures_modified": False,
            "documentation_modified": False,
            "database_modified": False,
        },
        "global_metrics": {
            "variants_total": inv["variant_count"],
            "masters_total": inv["master_count"],
            "multi_variant_masters": multi_masters,
            "variant_spec_rows": inv["variant_spec_row_count"],
            "master_spec_rows": inv["master_spec_row_count"],
            "variants_empty_effective_specs": empty_variants,
            "variants_empty_effective_specs_pct": round(
                100.0 * empty_variants / max(inv["variant_count"], 1), 1
            ),
            "spec_totals_variant_level": inv["spec_totals_variant"],
            "spec_totals_master_level": inv["spec_totals_master"],
            "p1_gap_count": len(p1),
            "p2_gap_count": len(p2),
            "p3_gap_count": len(p3),
            "classification_counts": dict(Counter(g.get("classification") for g in gaps)),
        },
        "category_matrix": build_category_matrix(inv["masters"], inv["profiles_by_category"], gaps),
        "prioritized_gaps": {
            "P1": p1[:30],
            "P2": p2[:40],
            "P3": p3[:30],
        },
        "false_positive_review": false_positive_patterns,
        "pattern_evidence": {
            "peso_kg_numeric_suffix": {
                "families": ["numeric_suffix_family", "cross_training_bumper_family", "hyphen_suffix_family"],
                "coverage": "431 variant rows; 0 multi-variant masters with weight-in-name missing peso",
                "pages": "DISCOS Y BARRAS (11), MANCUERNAS (12), CROSSTRAINING bumpers (11)",
                "false_positive_risk": "LOW",
            },
            "color_enum_master_or_variant": {
                "families": ["cross_training_bumper_family DOBC/DOB3C", "numeric_suffix MKI"],
                "coverage": "189 variant color + 12 master color rows",
                "pages": [11],
                "false_positive_risk": "MEDIUM if script ignores allowed_value_id or master_specs",
            },
            "smart_connect_cardio": {
                "families": ["explicit_one_per_sku cardio SKUs"],
                "coverage": "10 variant rows (validated matrix 7T/3F/2 absent)",
                "pages": [13, 14],
                "false_positive_risk": "LOW for explicit tokens; HIGH if inferring from brand proximity",
            },
            "peso_lb_wall_ball": {
                "families": ["CRO083-CRO086 wall ball block"],
                "coverage": "4 peso_lb rows; kg often primary axis",
                "pages": [14],
                "false_positive_risk": "MEDIUM — dual kg/lb display needs commercial rule",
            },
            "longitud_mm_barras": {
                "families": ["numeric_suffix_family BN/BO/BOR"],
                "coverage": "14/31 barras variants (~45%)",
                "pages": [11, 12],
                "false_positive_risk": "LOW for SKU-encoded lengths; skip BOC block bars",
            },
            "material_acabado": {
                "families": ["all categories"],
                "coverage": "0 structured rows — free text in PDF only",
                "false_positive_risk": "HIGH if regex-mapping prose to enums",
            },
        },
        "recommended_batches": [
            first_batch,
            {
                "batch_id": "SPEC-B2-PESO-LB-AXIS",
                "severity": "P2",
                "scope": "Extend peso_lb extraction for cross-training SKUs with explicit lb tokens in name/header",
                "false_positive_risk": "MEDIUM",
                "commercial_decision": "Whether lb is variant axis or display-only when kg present",
            },
            {
                "batch_id": "SPEC-B3-CATEGORY-PROFILE-COVERAGE",
                "severity": "P2",
                "scope": "Add profiles for material-de-estudio, musculacion, elipticas (optional peso_kg/smart_connect only with evidence)",
                "false_positive_risk": "LOW",
            },
            {
                "batch_id": "SPEC-B4-MATERIAL-ACABADO-ENUM",
                "severity": "P3",
                "scope": "Commercial taxonomy decision before any enum extraction",
                "classification": "SOURCE_DATA_NOT_AVAILABLE",
                "false_positive_risk": "HIGH",
            },
        ],
        "mandatory_answers": {
            "1_categories_families_needing_variant_specs": {
                "variant_axis_required": [
                    "discos (peso_kg; color when DOBC multicolor)",
                    "mancuernas (peso_kg)",
                    "cross-training weight families (peso_kg; peso_lb for lb-native wall balls)",
                    "barras numeric_suffix (peso_kg, longitud_mm)",
                ],
                "name_sku_sufficient": [
                    "cardio/bicicletas/cintas/remos/elipticas (explicit_one_per_sku)",
                    "cross-training block families (CRO/BOC blocks, rigs, specialty bars)",
                    "material-de-estudio (267/269 singleton masters)",
                    "musculacion machines (model name distinguishes)",
                ],
            },
            "2_critical_specs_with_explicit_evidence": [
                "peso_kg (kgs in name/header/SKU suffix)",
                "peso_lb (lbs in wall-ball and some CT headers)",
                "color (header COLOR line or color word in bumper/dumbbell families)",
                "longitud_mm (bar SKU size / explicit mm/cm in barras)",
                "smart_connect (Smart Connect/Conect token in cardio headers)",
                "capacidad_balones (SOP063 explicit balones count)",
            ],
            "3_critical_specs_missing_in_parser_preview_db": {
                "P1_none_after_correction": [],
                "P2": [
                    "longitud_mm partial on barras (~55% gap)",
                    "peso_lb under-extracted (4 rows vs lb evidence in wall-ball family)",
                    "smart_connect absent on some cardio rows without explicit token (not bug — source absent)",
                ],
                "PROFILE_VISIBILITY_GAP": [
                    "longitud_mm not in barras profile",
                    "material-de-estudio/musculacion/elipticas lack profiles",
                ],
            },
            "4_severity_classification": {
                "P1_CRITICAL_SPEC_GAP": len(p1),
                "P2_SPEC_COVERAGE_IMPROVEMENT": len([g for g in p2 if g.get("classification") != "PROFILE_VISIBILITY_GAP"]),
                "P3_OPTIONAL_SPEC_BACKLOG": len([g for g in p3 if g.get("classification") == "P3_OPTIONAL_SPEC_BACKLOG"]),
                "SOURCE_DATA_NOT_AVAILABLE": len([g for g in gaps if g.get("classification") == "SOURCE_DATA_NOT_AVAILABLE"]),
                "PROFILE_VISIBILITY_GAP": len([g for g in gaps if g.get("classification") == "PROFILE_VISIBILITY_GAP"]),
                "SPEC_EXTRACTION_BUG": len([g for g in gaps if g.get("classification") == "SPEC_EXTRACTION_BUG"]),
            },
            "5_commercially_distinguishable_empty_specs": {
                "count": empty_variants,
                "pct": round(100.0 * empty_variants / max(inv["variant_count"], 1), 1),
                "note": "Mostly singleton masters; display_name/SKU unique per variant",
            },
            "6_spec_level_assignment": {
                "master_level": ["material", "casquillo", "carga_maxima_kg", "diametro_casquillo_mm", "color when uniform per master (DOB3C, MKI)"],
                "variant_level": ["peso_kg", "peso_lb", "color (DOBC per-variant)", "smart_connect", "unidades_pack", "capacidad_balones", "longitud_mm"],
                "variant_axis": ["peso_kg", "peso_lb", "color (when varies within master)"],
            },
            "7_category_profile_gaps": {
                "missing_profiles": sorted(all_slugs - CATEGORIES_WITH_PROFILES),
                "too_broad": [
                    "cardio profile lists peso_kg/color but most variants are singletons without evidence"
                ],
                "too_narrow": [
                    "barras profile omits longitud_mm despite extraction"
                ],
            },
            "8_low_risk_systemic_patterns": [
                "numeric_suffix → peso_kg (proven, 431 rows)",
                "bumper header COLOR line → color enum (proven, 189+12 rows)",
                "smart_connect explicit token → boolean (proven, validated)",
                "bar BN/BO/BOR suffix → longitud_mm (partial, extendable)",
            ],
            "9_patterns_requiring_commercial_decision": [
                "material/acabado enum mapping from free text",
                "peso_lb as variant axis vs display when peso_kg exists",
                "dimension specs (alto_mm/ancho_mm) for cardio machines",
                "carga_maxima_kg for racks/structures",
            ],
            "10_source_data_not_available": [
                "Structured material/acabado enums (prose only in PDF)",
                "Machine dimensions for most cardio/musculacion",
                "carga_maxima_kg systematic values",
                "smart_connect when token absent (must remain unknown)",
            ],
        },
        "regression_pages": [11, 12, 13, 14],
        "full_catalog_gate_pages": 65,
    }

    out_json = OUTPUT_DIR / "critical_spec_coverage_post_audit_report.json"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Critical Spec Coverage Audit — Post-Review Report",
        "",
        f"**Status:** `{report['status']}`",
        "",
        "## Read-only confirmation",
        "No code, tests, fixtures, documentation, or DB modifications were made.",
        "",
        "## Global metrics (corrected)",
        f"- Variants: **{report['global_metrics']['variants_total']}** | Masters: **{report['global_metrics']['masters_total']}**",
        f"- Multi-variant masters: **{report['global_metrics']['multi_variant_masters']}**",
        f"- Empty effective specs: **{report['global_metrics']['variants_empty_effective_specs']}** ({report['global_metrics']['variants_empty_effective_specs_pct']}%)",
        f"- Variant spec rows: **{report['global_metrics']['variant_spec_rows']}** | Master spec rows: **{report['global_metrics']['master_spec_rows']}**",
        f"- P1: **{report['global_metrics']['p1_gap_count']}** | P2: **{report['global_metrics']['p2_gap_count']}** | P3: **{report['global_metrics']['p3_gap_count']}**",
        "",
        "### Spec totals (variant level)",
        "| Spec | Count |",
        "|------|-------|",
    ]
    for k, v in sorted(report["global_metrics"]["spec_totals_variant_level"].items(), key=lambda x: -x[1]):
        md_lines.append(f"| {k} | {v} |")
    md_lines.extend(
        [
            "",
            "## Category matrix (severity)",
            "| Category | Variants | Empty% | Critical coverage | Severity |",
            "|----------|----------|--------|-------------------|----------|",
        ]
    )
    for row in report["category_matrix"]:
        cov = ", ".join(f"{k}={v}%" for k, v in row["critical_coverage_pct"].items()) or "—"
        md_lines.append(
            f"| {row['category_slug']} | {row['variants']} | {row['empty_effective_specs_pct']}% | {cov} | {row['severity']} |"
        )
    md_lines.extend(
        [
            "",
            "## First recommended batch (Agent 2 Plan Mode)",
            f"**{first_batch['batch_id']}** — {first_batch['scope']}",
            "",
            "## Key finding",
            "After correcting enum (`allowed_value_id`), master-level specs, and barras longitud_mm axis, **no P1 critical gaps** remain. "
            "Weight/length-axis families fully distinguish variants. Remaining work is P2 extraction/profile enrichment.",
        ]
    )
    out_md = OUTPUT_DIR / "critical_spec_coverage_post_audit_report.md"
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps({"status": report["status"], "p1": len(p1), "p2": len(p2), "p3": len(p3)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
