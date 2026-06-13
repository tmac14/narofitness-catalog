"""Category and taxonomy mapping baseline snapshots for import audit."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Catalog,
    CatalogItem,
    Category,
    ProductMaster,
    ProductVariant,
    TaxonomyMappingRule,
)
from app.services.seed_category_defaults import DEFAULT_CATEGORY_ROWS
from app.services.seed_taxonomy_mapping_rules import (
    MATCH_SKU_PREFIX,
    RETIRED_TAXONOMY_MAPPING_RULE_KEYS,
)

RESET_CLEARED_TABLES = (
    "catalog_exports",
    "catalog_product_layouts",
    "catalog_items",
    "catalogs",
    "supplier_price_entries",
    "supplier_price_lists",
    "import_rows",
    "import_batches",
    "product_master_specs",
    "product_variant_specs",
    "product_images",
    "supplier_product_family_keys",
    "product_variants",
    "product_masters",
)

PRESERVED_TABLES = (
    "categories",
    "taxonomy_mapping_rules",
    "suppliers",
    "import_profiles",
    "spec_definitions",
    "spec_allowed_values",
    "units",
    "category_spec_profiles",
    "app_settings",
    "brands",
)

SEED_DEFAULT_SLUGS = frozenset(
    {row.parent_slug for row in DEFAULT_CATEGORY_ROWS}
    | {row.subcategory_slug for row in DEFAULT_CATEGORY_ROWS if row.subcategory_slug}
)


def _seed_source_for_slug(slug: str) -> str:
    return "seed_category_defaults" if slug in SEED_DEFAULT_SLUGS else "unknown_or_manual"


async def capture_db_counts(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for model, key in (
        (Category, "canonical_categories"),
        (TaxonomyMappingRule, "taxonomy_mapping_rules"),
        (ProductMaster, "product_masters"),
        (ProductVariant, "product_variants"),
        (Catalog, "catalogs"),
        (CatalogItem, "catalogue_items"),
    ):
        result = await session.execute(select(func.count()).select_from(model))
        counts[key] = int(result.scalar_one())
    active_rules = await session.execute(
        select(func.count())
        .select_from(TaxonomyMappingRule)
        .where(TaxonomyMappingRule.is_active.is_(True))
    )
    counts["taxonomy_mapping_rules_active"] = int(active_rules.scalar_one())
    return counts


async def export_category_baseline(
    session: AsyncSession,
    *,
    baseline_mode: str = "pim_only",
) -> dict[str, Any]:
    categories = list(
        (await session.execute(select(Category).order_by(Category.slug))).scalars().all()
    )
    id_to_slug = {c.id: c.slug for c in categories}

    exported: list[dict[str, Any]] = []
    parents = 0
    subcategories = 0
    for cat in categories:
        parent_slug = id_to_slug.get(cat.parent_id) if cat.parent_id else None
        depth = 1 if cat.parent_id else 0
        if depth == 0:
            parents += 1
        else:
            subcategories += 1
        exported.append(
            {
                "id": str(cat.id),
                "name": cat.name,
                "slug": cat.slug,
                "parent_id": str(cat.parent_id) if cat.parent_id else None,
                "parent_slug": parent_slug,
                "depth": depth,
                "seed_source": _seed_source_for_slug(cat.slug),
                "created_at": cat.created_at.isoformat() if cat.created_at else None,
                "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
            }
        )

    repuestos = next((c for c in categories if c.slug == "repuestos"), None)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_mode": baseline_mode,
        "canonical_categories": exported,
        "counts": {
            "parents": parents,
            "subcategories": subcategories,
            "total": len(exported),
        },
        "canonical_category_slugs": sorted(c.slug for c in categories),
        "repuestos_category": {
            "exists": repuestos is not None,
            "id": str(repuestos.id) if repuestos else None,
            "slug": "repuestos" if repuestos else None,
            "origin": "seed_category_defaults" if repuestos else None,
            "note": "Orphan parent in seed; not a target for REPUESTO- SKU prefix mapping",
        },
    }


async def _resolve_rule_slugs(
    session: AsyncSession, rule: TaxonomyMappingRule
) -> tuple[str | None, str | None]:
    target_slug = None
    sub_slug = None
    if rule.target_category_id:
        cat = await session.get(Category, rule.target_category_id)
        target_slug = cat.slug if cat else None
    if rule.target_subcategory_id:
        sub = await session.get(Category, rule.target_subcategory_id)
        sub_slug = sub.slug if sub else None
    return target_slug, sub_slug


async def export_mapping_baseline(session: AsyncSession) -> dict[str, Any]:
    rules = list(
        (await session.execute(select(TaxonomyMappingRule).order_by(TaxonomyMappingRule.priority)))
        .scalars()
        .all()
    )

    active_rules: list[dict[str, Any]] = []
    inactive_rules: list[dict[str, Any]] = []
    for rule in rules:
        target_slug, sub_slug = await _resolve_rule_slugs(session, rule)
        entry = {
            "id": str(rule.id),
            "match_type": rule.match_type,
            "match_value": rule.match_value,
            "target_category_slug": target_slug,
            "target_subcategory_slug": sub_slug,
            "priority": rule.priority,
            "confidence": float(rule.confidence) if rule.confidence is not None else None,
            "is_active": rule.is_active,
            "requires_review": rule.requires_review,
            "supplier_id": str(rule.supplier_id) if rule.supplier_id else None,
            "import_profile_id": str(rule.import_profile_id) if rule.import_profile_id else None,
        }
        if rule.is_active:
            active_rules.append(entry)
        else:
            inactive_rules.append(entry)

    repuesto_rule = next(
        (r for r in rules if r.match_type == MATCH_SKU_PREFIX and r.match_value == "REPUESTO-"),
        None,
    )
    retired_in_code = (MATCH_SKU_PREFIX, "REPUESTO-") in RETIRED_TAXONOMY_MAPPING_RULE_KEYS
    target_slug = None
    if repuesto_rule and repuesto_rule.target_category_id:
        cat = await session.get(Category, repuesto_rule.target_category_id)
        target_slug = cat.slug if cat else None

    repuesto_check: dict[str, Any] = {
        "rule_exists": repuesto_rule is not None,
        "match_type": MATCH_SKU_PREFIX,
        "match_value": "REPUESTO-",
        "target_category_slug": target_slug or ("repuestos" if repuesto_rule else None),
        "is_active": repuesto_rule.is_active if repuesto_rule else False,
        "priority": repuesto_rule.priority if repuesto_rule else None,
        "confidence": float(repuesto_rule.confidence)
        if repuesto_rule and repuesto_rule.confidence
        else None,
        "retired_in_code": retired_in_code,
        "warning": None,
    }
    if repuesto_rule and repuesto_rule.is_active:
        repuesto_check["warning"] = "retired_repuesto_rule_still_active"

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "active_rules": active_rules,
        "inactive_rules": inactive_rules,
        "counts": {
            "active": len(active_rules),
            "inactive": len(inactive_rules),
            "total": len(rules),
        },
        "mapping_rules_summary": [
            f"{r['match_type']}:{r['match_value']} -> {r['target_subcategory_slug'] or r['target_category_slug']}"
            for r in active_rules
        ],
        "repuesto_rule_check": repuesto_check,
    }


def build_reset_summary(
    *,
    reset_counts: dict[str, int] | None,
    counts_before: dict[str, int],
    counts_after: dict[str, int],
) -> dict[str, Any]:
    return {
        "tables_cleared": list(RESET_CLEARED_TABLES),
        "tables_preserved": list(PRESERVED_TABLES),
        "categories_preserved": True,
        "taxonomy_mapping_rules_preserved": True,
        "reset_delete_counts": reset_counts or {},
        "product_masters_count_before": counts_before.get("product_masters", 0),
        "product_masters_count_after": counts_after.get("product_masters", 0),
        "product_variants_count_before": counts_before.get("product_variants", 0),
        "product_variants_count_after": counts_after.get("product_variants", 0),
        "catalogue_items_count_before": counts_before.get("catalogue_items", 0),
        "catalogue_items_count_after": counts_after.get("catalogue_items", 0),
    }
