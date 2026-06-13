#!/usr/bin/env python3
"""B2 weight semantics audit — peso_kg / peso_lb full catalog read-only."""
from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from app.database import async_session
from app.models import ImportRow, ProductVariant, ProductVariantSpec, SpecDefinition

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage/b2_weight_semantics")

WEIGHT_KG_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?\b", re.I)
WEIGHT_LB_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*lbs?\b", re.I)
SKU_SUFFIX_LETTER_RE = re.compile(r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$", re.I)
BAR_SUFFIX_FAMILIES = {"BNZ", "BOZ", "BORZ", "BBPB", "BORA"}
BAR_PREFIXES = {"BN", "BO", "BOR", "BBP"}

BASELINE = {"variants": 871, "masters": 534, "peso_kg": 431, "peso_lb": 4}


def infer_evidence(row: dict, spec_key: str, value: float) -> str:
    gr = row.get("grouping_reason") or ""
    parser = row.get("parser_variant_specs") or {}
    name = " ".join(
        filter(None, [row.get("raw_name"), row.get("normalized_name"), row.get("display_name")])
    )
    sku = (row.get("sku") or "").upper()

    if spec_key == "peso_lb":
        if WEIGHT_LB_RE.search(name):
            return "name_lbs"
        return "parser_unknown"

    # peso_kg
    if WEIGHT_KG_RE.search(name):
        return "name_kg"
    if gr.startswith("numeric_suffix_family:") or gr.startswith("fdl_sku_family:"):
        m = SKU_SUFFIX_LETTER_RE.match(sku)
        if m and int(m.group("size")) == int(value):
            return "sku_size_fallback"
        m2 = re.match(r"^(?P<prefix>[A-Z]+)(?P<size>\d{3})$", sku)
        if m2 and int(m2.group("size")) == int(value):
            return "sku_numeric_suffix"
    if gr.startswith("cross_training_bumper_family:"):
        return "name_or_bumper_header"
    if gr.startswith("numeric_compound_suffix_family:"):
        return "compound_suffix_weight"
    if gr.startswith("hyphen_suffix_family:"):
        return "hyphen_suffix"
    if parser.get("peso_kg") == value:
        if WEIGHT_KG_RE.search(name):
            return "name_kg"
    return "unknown"


def classify_row(row: dict, db_peso_kg: float | None, db_peso_lb: float | None) -> list[dict]:
    findings: list[dict] = []
    sku = (row.get("sku") or "").upper()
    gr = row.get("grouping_reason") or ""
    slug = row.get("category_slug") or ""
    name = " ".join(
        filter(None, [row.get("raw_name"), row.get("normalized_name"), row.get("display_name")])
    )
    parser_kg = (row.get("parser_variant_specs") or {}).get("peso_kg")
    parser_lb = (row.get("parser_variant_specs") or {}).get("peso_lb")
    longitud = (row.get("parser_variant_specs") or {}).get("longitud_mm")

    # False positive: bar suffix-letter peso_kg from SKU size
    if db_peso_kg is not None and gr.startswith("fdl_sku_family:"):
        mk = row.get("master_key") or ""
        if mk in BAR_SUFFIX_FAMILIES or (slug == "barras" and mk.endswith(("Z", "B", "A"))):
            m = SKU_SUFFIX_LETTER_RE.match(sku)
            if m and float(m.group("size")) == float(db_peso_kg):
                findings.append(
                    {
                        "classification": "WEIGHT_SPEC_FALSE_POSITIVE",
                        "spec": "peso_kg",
                        "value": db_peso_kg,
                        "reason": "SKU size digits mapped to peso_kg; bar axis is longitud_mm",
                        "evidence": infer_evidence(row, "peso_kg", db_peso_kg),
                        "longitud_mm": longitud,
                    }
                )

    # Correct peso_kg
    if db_peso_kg is not None and not any(f["classification"] == "WEIGHT_SPEC_FALSE_POSITIVE" for f in findings):
        ev = infer_evidence(row, "peso_kg", db_peso_kg)
        if ev in ("name_kg", "sku_numeric_suffix", "compound_suffix_weight", "name_or_bumper_header"):
            findings.append(
                {
                    "classification": "WEIGHT_SPEC_CORRECT",
                    "spec": "peso_kg",
                    "value": db_peso_kg,
                    "evidence": ev,
                }
            )
        elif ev == "sku_size_fallback" and slug != "barras":
            findings.append(
                {
                    "classification": "WEIGHT_SPEC_CORRECT",
                    "spec": "peso_kg",
                    "value": db_peso_kg,
                    "evidence": ev,
                }
            )
        else:
            findings.append(
                {
                    "classification": "SOURCE_DATA_AMBIGUOUS",
                    "spec": "peso_kg",
                    "value": db_peso_kg,
                    "evidence": ev,
                }
            )

    # peso_lb correct
    if db_peso_lb is not None:
        findings.append(
            {
                "classification": "WEIGHT_SPEC_CORRECT",
                "spec": "peso_lb",
                "value": db_peso_lb,
                "evidence": infer_evidence(row, "peso_lb", db_peso_lb),
            }
        )

    # Missing peso_lb with lbs in name
    lb_match = WEIGHT_LB_RE.search(name)
    if lb_match and db_peso_lb is None:
        expected = float(lb_match.group(1).replace(",", "."))
        if gr.startswith("cross_training_block_family:") or "wall ball" in name.lower():
            findings.append(
                {
                    "classification": "WEIGHT_SPEC_MISSING",
                    "spec": "peso_lb",
                    "expected": expected,
                    "reason": "explicit lbs in name/header",
                    "evidence": "name_lbs",
                }
            )
        elif slug == "barras" and "lbs" in name.lower():
            findings.append(
                {
                    "classification": "WEIGHT_UNIT_DECISION_REQUIRED",
                    "spec": "peso_lb",
                    "expected": expected,
                    "reason": "bar load rating in lbs (BOR220); not variant axis",
                    "evidence": "name_lbs_load_rating",
                }
            )

    # Missing peso_kg with kg in name (weight families only)
    kg_match = WEIGHT_KG_RE.search(name)
    if kg_match and db_peso_kg is None and gr.startswith(
        ("numeric_suffix_family:", "cross_training_bumper_family:", "fdl_sku_family:", "hyphen_suffix_family:")
    ):
        findings.append(
            {
                "classification": "WEIGHT_SPEC_MISSING",
                "spec": "peso_kg",
                "expected": float(kg_match.group(1).replace(",", ".")),
                "reason": "kg in name but not persisted",
                "evidence": "name_kg",
            }
        )

    # Dual unit ambiguity
    if kg_match and lb_match and db_peso_kg and db_peso_lb:
        findings.append(
            {
                "classification": "WEIGHT_UNIT_DECISION_REQUIRED",
                "spec": "both",
                "reason": "both kg and lb tokens in source",
            }
        )
    elif kg_match and lb_match and (db_peso_kg or db_peso_lb) and not (db_peso_kg and db_peso_lb):
        findings.append(
            {
                "classification": "WEIGHT_UNIT_DECISION_REQUIRED",
                "spec": "partial_dual",
                "reason": "source has both units; only one persisted",
            }
        )

    return findings


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_session() as session:
        # DB weight specs
        db_rows = (
            await session.execute(
                text("""
                    SELECT v.sku, v.display_name, pm.master_key, c.slug,
                           sd.key, pvs.value_number
                    FROM product_variants v
                    JOIN product_masters pm ON pm.id = v.product_master_id
                    LEFT JOIN categories c ON c.id = pm.category_id
                    JOIN product_variant_specs pvs ON pvs.variant_id = v.id
                    JOIN spec_definitions sd ON sd.id = pvs.spec_definition_id
                    WHERE sd.key IN ('peso_kg', 'peso_lb')
                    ORDER BY v.sku, sd.key
                """)
            )
        ).all()

        db_by_sku: dict[str, dict] = defaultdict(dict)
        for sku, dname, mk, slug, key, val in db_rows:
            db_by_sku[sku.upper()].update(
                {
                    "sku": sku,
                    "display_name": dname,
                    "master_key": mk,
                    "category_slug": slug,
                    key: float(val),
                }
            )

        import_rows = (
            await session.execute(
                select(
                    ImportRow.sku,
                    ImportRow.source_page,
                    ImportRow.grouping_reason,
                    ImportRow.master_key,
                    ImportRow.parsed_variant_specs_raw,
                    ImportRow.raw_name,
                    ImportRow.normalized_name,
                    ImportRow.mapped_category_slug,
                ).where(ImportRow.sku.isnot(None))
            )
        ).all()
        import_by_sku: dict[str, dict] = {}
        for sku, page, gr, mk, pvar, raw, norm, slug in import_rows:
            key = (sku or "").upper()
            if key not in import_by_sku:
                import_by_sku[key] = {
                    "sku": sku,
                    "source_page": page,
                    "grouping_reason": gr,
                    "master_key": mk,
                    "parser_variant_specs": pvar or {},
                    "raw_name": raw,
                    "normalized_name": norm,
                    "category_slug": slug,
                }

        v_total = (await session.execute(select(func.count()).select_from(ProductVariant))).scalar_one()
        kg_count = sum(1 for d in db_by_sku.values() if "peso_kg" in d)
        lb_count = sum(1 for d in db_by_sku.values() if "peso_lb" in d)

    # Merge and classify
    all_skus = set(import_by_sku) | set(db_by_sku)
    inventory: list[dict] = []
    by_class: Counter[str] = Counter()
    by_category: dict[str, Counter] = defaultdict(Counter)
    by_page: dict[int, Counter] = defaultdict(Counter)
    false_positives: list[dict] = []
    missing: list[dict] = []
    unit_decisions: list[dict] = []

    for sku in sorted(all_skus):
        imp = import_by_sku.get(sku, {})
        db = db_by_sku.get(sku, {})
        merged = {**imp, **db, "display_name": db.get("display_name") or imp.get("normalized_name")}
        pk = db.get("peso_kg")
        pl = db.get("peso_lb")
        findings = classify_row(merged, pk, pl)
        entry = {
            "sku": sku,
            "category_slug": merged.get("category_slug"),
            "master_key": merged.get("master_key"),
            "grouping_reason": merged.get("grouping_reason"),
            "source_page": merged.get("source_page"),
            "peso_kg": pk,
            "peso_lb": pl,
            "parser_peso_kg": (merged.get("parser_variant_specs") or {}).get("peso_kg"),
            "parser_peso_lb": (merged.get("parser_variant_specs") or {}).get("peso_lb"),
            "findings": findings,
        }
        inventory.append(entry)
        for f in findings:
            by_class[f["classification"]] += 1
            if merged.get("category_slug"):
                by_category[merged["category_slug"]][f["classification"]] += 1
            if merged.get("source_page"):
                by_page[merged["source_page"]][f["classification"]] += 1
            if f["classification"] == "WEIGHT_SPEC_FALSE_POSITIVE":
                false_positives.append({**entry, "finding": f})
            elif f["classification"] == "WEIGHT_SPEC_MISSING":
                missing.append({**entry, "finding": f})
            elif f["classification"] == "WEIGHT_UNIT_DECISION_REQUIRED":
                unit_decisions.append({**entry, "finding": f})

    # Aggregate by family
    family_stats: dict[str, dict] = defaultdict(
        lambda: {"peso_kg": 0, "peso_lb": 0, "false_positive": 0, "skus": []}
    )
    for e in inventory:
        gr = e.get("grouping_reason") or "unknown"
        fam = gr.split(":")[0] if ":" in gr else gr
        if e.get("peso_kg"):
            family_stats[fam]["peso_kg"] += 1
        if e.get("peso_lb"):
            family_stats[fam]["peso_lb"] += 1
        if any(f["classification"] == "WEIGHT_SPEC_FALSE_POSITIVE" for f in e["findings"]):
            family_stats[fam]["false_positive"] += 1
            family_stats[fam]["skus"].append(e["sku"])

    # Pages with weight evidence
    pages_with_kg: set[int] = set()
    pages_with_lb: set[int] = set()
    for sku, imp in import_by_sku.items():
        name = " ".join(filter(None, [imp.get("raw_name"), imp.get("normalized_name")]))
        if WEIGHT_KG_RE.search(name):
            if imp.get("source_page"):
                pages_with_kg.add(imp["source_page"])
        if WEIGHT_LB_RE.search(name):
            if imp.get("source_page"):
                pages_with_lb.add(imp["source_page"])

    baseline_ok = (
        v_total == BASELINE["variants"]
        and kg_count == BASELINE["peso_kg"]
        and lb_count == BASELINE["peso_lb"]
    )

    sub_batches = [
        {
            "batch_id": "B2-A-BAR-SUFFIX-LETTER-PESO-REMOVAL",
            "scope": "Remove peso_kg from fdl_sku_family barras suffix-letter (BNZ/BOZ/BORZ/BBPB/BORA) where size=length cm",
            "skus": [e["sku"] for e in false_positives],
            "risk": "LOW — does not touch numeric_suffix_family weight families",
            "grouping_impact": "none",
        },
        {
            "batch_id": "B2-B-WALL-BALL-PESO-LB",
            "scope": "Extend peso_lb extraction for cross-training wall-ball block where lbs explicit",
            "skus": [e["sku"] for e in missing if e.get("category_slug") == "cross-training"],
            "risk": "MEDIUM — commercial rule: lb as primary axis vs kg",
            "grouping_impact": "none",
        },
        {
            "batch_id": "B2-C-BAR-LOAD-RATING-LBS",
            "scope": "BOR220/BOR220A load-rating lbs — commercial decision only, not variant axis",
            "risk": "HIGH if auto-extracted as peso_lb",
            "grouping_impact": "none",
        },
    ]

    report = {
        "task_id": "IMPORT-FDL-SPEC-B2-WEIGHT-SEMANTICS-AUDIT",
        "status": "B2_WEIGHT_SEMANTICS_AUDIT_COMPLETE" if baseline_ok else "B2_WEIGHT_SEMANTICS_AUDIT_INCOMPLETE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only_confirmation": {"code_modified": False, "database_modified": False},
        "baseline": {
            "expected": BASELINE,
            "actual": {"variants": v_total, "peso_kg_rows": kg_count, "peso_lb_rows": lb_count},
            "baseline_ok": baseline_ok,
        },
        "counts": {
            "peso_kg_variants": kg_count,
            "peso_lb_variants": lb_count,
            "by_category": {
                slug: {
                    "peso_kg": sum(1 for e in inventory if e.get("category_slug") == slug and e.get("peso_kg")),
                    "peso_lb": sum(1 for e in inventory if e.get("category_slug") == slug and e.get("peso_lb")),
                }
                for slug in sorted({e.get("category_slug") for e in inventory if e.get("category_slug")})
            },
            "by_classification": dict(by_class),
        },
        "pages_with_weight_evidence": {
            "kg_pages": sorted(pages_with_kg),
            "lb_pages": sorted(pages_with_lb),
        },
        "false_positives": false_positives,
        "missing_specs": missing,
        "unit_decisions": unit_decisions,
        "family_stats": {k: {**v, "skus": v["skus"][:20]} for k, v in family_stats.items()},
        "weight_axis_families": [
            "numeric_suffix_family (discos/mancuernas/CT bumpers)",
            "numeric_compound_suffix_family (JMU/JMP/JMH)",
            "hyphen_suffix_family (MPS-R)",
            "cross_training_bumper_family",
            "fdl_sku_family (suffix-letter mancuernas MH*A etc — weight when size=kg)",
            "cross_training_block wall-ball (peso_lb axis when extracted)",
        ],
        "commercial_decisions": [
            "Wall balls: peso_lb as sole variant axis vs dual kg+lb display",
            "Bar load ratings (1500 lbs, 1000 lbs): store as spec or ignore (not variant axis)",
            "material-de-estudio peso_kg: discovery works; profile optional per B3B",
        ],
        "recommended_sub_batches": sub_batches,
        "agent_2_plan_mode_prompt": (
            "SPEC-B2-A-BAR-SUFFIX-LETTER-PESO-REMOVAL: In fdl_sku_family grouping for barras "
            "suffix-letter masters (BNZ/BOZ/BORZ/BBPB/BORA), skip attr_from_sku peso_kg when "
            "bar length extractor applies; do not modify numeric_suffix_family weight paths."
            if false_positives
            else None
        ),
        "inventory_sample": {
            "peso_lb_all": [e for e in inventory if e.get("peso_lb")],
            "false_positive_all": false_positives,
            "missing_top": missing[:30],
        },
    }

    out = OUTPUT_DIR / "b2_weight_semantics_audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# B2 Weight Semantics Audit",
        "",
        f"**Status:** `{report['status']}`",
        "",
        f"- peso_kg: **{kg_count}** | peso_lb: **{lb_count}**",
        f"- False positives: **{len(false_positives)}**",
        f"- Missing: **{len(missing)}**",
        f"- Unit decisions: **{len(unit_decisions)}**",
        "",
        "## False positives (bar suffix-letter)",
    ]
    for fp in false_positives:
        md.append(f"- `{fp['sku']}` peso_kg={fp.get('peso_kg')} ({fp.get('grouping_reason')})")
    (OUTPUT_DIR / "b2_weight_semantics_audit.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"status": report["status"], "kg": kg_count, "lb": lb_count, "fp": len(false_positives), "missing": len(missing)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
