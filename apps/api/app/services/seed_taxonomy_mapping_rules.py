"""Idempotent seed for controlled taxonomy mapping rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, TaxonomyMappingRule

MATCH_SECTION_PATH = "section_path"
MATCH_SECTION_KEYWORD = "section_keyword"
MATCH_SKU_PREFIX = "sku_prefix"


@dataclass(frozen=True)
class TaxonomyMappingRuleSeedRow:
    match_type: str
    match_value: str
    target_category_slug: str
    target_subcategory_slug: str | None = None
    priority: int = 100
    confidence: Decimal = Decimal("1.0")
    requires_review: bool = False


@dataclass
class TaxonomyMappingRuleSeedResult:
    created: int = 0
    updated: int = 0
    deactivated: int = 0


DEFAULT_TAXONOMY_MAPPING_RULE_ROWS: tuple[TaxonomyMappingRuleSeedRow, ...] = (
    TaxonomyMappingRuleSeedRow(
        MATCH_SKU_PREFIX,
        "DOBNEXO",
        "discos",
        priority=15,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SKU_PREFIX,
        "DOB3C",
        "discos",
        priority=16,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SKU_PREFIX,
        "DOBC",
        "discos",
        priority=17,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SKU_PREFIX,
        "DOBN",
        "discos",
        priority=18,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SKU_PREFIX,
        "DOB",
        "discos",
        priority=19,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL|soporte discos",
        "soportes-y-mancuerneros",
        priority=23,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL|sopote",
        "soportes-y-mancuerneros",
        priority=23,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL|slam ball",
        "cross-training",
        priority=31,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL|wall ball",
        "cross-training",
        priority=32,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL|bumper",
        "discos",
        priority=24,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL|disco",
        "discos",
        priority=25,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > BICI",
        "cardio",
        "bicicletas-estaticas",
        priority=20,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > REMO",
        "cardio",
        "remos",
        priority=21,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > CINTA",
        "cardio",
        "cintas-de-correr",
        priority=22,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > CINTAS",
        "cardio",
        "cintas-de-correr",
        priority=22,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > ELIPTICA",
        "cardio",
        "elipticas",
        priority=23,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > BICIS",
        "cardio",
        "bicicletas-estaticas",
        priority=24,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > SKI",
        "cardio",
        priority=26,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > TRINEO",
        "cardio",
        priority=27,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > CLIMBER",
        "cardio",
        priority=28,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CARDIO > MULTIESTACION",
        "cardio",
        priority=29,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "MANCUERNAS",
        "mancuernas",
        priority=25,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "MUSCULACION",
        "musculacion",
        priority=28,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "MATERIAL DE ESTUDIO",
        "material-de-estudio",
        priority=29,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_PATH,
        "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
        "cross-training",
        priority=30,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "DISCOS Y BARRAS|mancuerna",
        "mancuernas",
        priority=35,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "DISCOS Y BARRAS|disco",
        "discos",
        priority=40,
    ),
    TaxonomyMappingRuleSeedRow(
        MATCH_SECTION_KEYWORD,
        "DISCOS Y BARRAS|barra",
        "barras",
        priority=45,
    ),
)

# Retired rules: deactivated on seed (REPUESTO- is a SKU prefix, not a canonical category).
RETIRED_TAXONOMY_MAPPING_RULE_KEYS: tuple[tuple[str, str], ...] = ((MATCH_SKU_PREFIX, "REPUESTO-"),)


async def _get_category_by_slug(session: AsyncSession, slug: str) -> Category | None:
    return (
        await session.execute(select(Category).where(Category.slug == slug))
    ).scalar_one_or_none()


async def _upsert_rule(
    session: AsyncSession,
    row: TaxonomyMappingRuleSeedRow,
    category_cache: dict[str, Category],
) -> tuple[bool, bool]:
    target_category = category_cache.get(row.target_category_slug)
    if target_category is None:
        target_category = await _get_category_by_slug(session, row.target_category_slug)
        if target_category is None:
            return False, False
        category_cache[row.target_category_slug] = target_category

    target_subcategory_id = None
    if row.target_subcategory_slug:
        subcategory = category_cache.get(row.target_subcategory_slug)
        if subcategory is None:
            subcategory = await _get_category_by_slug(session, row.target_subcategory_slug)
            if subcategory is None:
                return False, False
            category_cache[row.target_subcategory_slug] = subcategory
        target_subcategory_id = subcategory.id

    result = await session.execute(
        select(TaxonomyMappingRule).where(
            TaxonomyMappingRule.match_type == row.match_type,
            TaxonomyMappingRule.match_value == row.match_value,
            TaxonomyMappingRule.supplier_id.is_(None),
            TaxonomyMappingRule.import_profile_id.is_(None),
        )
    )
    rule = result.scalar_one_or_none()
    if rule:
        updated = False
        for attr, value in (
            ("priority", row.priority),
            ("target_category_id", target_category.id),
            ("target_subcategory_id", target_subcategory_id),
            ("confidence", row.confidence),
            ("requires_review", row.requires_review),
            ("is_active", True),
        ):
            if getattr(rule, attr) != value:
                setattr(rule, attr, value)
                updated = True
        return False, updated

    session.add(
        TaxonomyMappingRule(
            match_type=row.match_type,
            match_value=row.match_value,
            priority=row.priority,
            target_category_id=target_category.id,
            target_subcategory_id=target_subcategory_id,
            confidence=row.confidence,
            requires_review=row.requires_review,
            is_active=True,
        )
    )
    await session.flush()
    return True, False


async def _deactivate_retired_rules(session: AsyncSession) -> int:
    deactivated = 0
    for match_type, match_value in RETIRED_TAXONOMY_MAPPING_RULE_KEYS:
        rule = (
            await session.execute(
                select(TaxonomyMappingRule).where(
                    TaxonomyMappingRule.match_type == match_type,
                    TaxonomyMappingRule.match_value == match_value,
                    TaxonomyMappingRule.supplier_id.is_(None),
                    TaxonomyMappingRule.import_profile_id.is_(None),
                )
            )
        ).scalar_one_or_none()
        if rule and rule.is_active:
            rule.is_active = False
            deactivated += 1
    return deactivated


async def seed_taxonomy_mapping_rules(session: AsyncSession) -> TaxonomyMappingRuleSeedResult:
    result = TaxonomyMappingRuleSeedResult()
    category_cache: dict[str, Category] = {}

    for row in DEFAULT_TAXONOMY_MAPPING_RULE_ROWS:
        created, updated = await _upsert_rule(session, row, category_cache)
        if created:
            result.created += 1
        elif updated:
            result.updated += 1

    result.deactivated = await _deactivate_retired_rules(session)

    await session.commit()
    return result
