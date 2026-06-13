"""Seed categories, product masters, variants and prices from the FDL tariff PDF."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.database import async_session
from app.models import (
    Catalog,
    CatalogItem,
    ImportProfile,
    ProductVariant,
    Supplier,
    SupplierPriceEntry,
)
from app.services.fdl_block_family import DEFAULT_CROSS_TRAINING_BLOCK_NAME_TOKENS
from app.services.import_confirm import confirm_import
from app.services.import_parsers.fdl_pdf_v1 import compute_stats, parse_pdf
from app.services.import_pipeline import run_preview_pipeline
from app.services.seed_brands import ensure_fallback_commercial_brand
from app.services.seed_paths import DEFAULT_PDF_NAME
from app.services.seed_reset import reset_catalog_data
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.seed_taxonomy import run_taxonomy_seed
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules

DEFAULT_EFFECTIVE_DATE = date(2026, 2, 1)
DEFAULT_PRESENTATION_CATALOG_NAME = "FDL Tarifa 2026"
DEFAULT_PRESENTATION_MARKUP_PERCENT = Decimal("15")

FDL_ATTR_FROM_NAME = {
    "color": [
        "Negro",
        "Blanco",
        "Gris",
        "Rojo",
        "Naranja",
        "Amarillo",
        "Azul",
        "Verde",
        "Rosa",
        "Morado",
        "Violeta",
        "Marrón",
        "Beige",
        "Plata",
        "Dorado",
        "Transparente",
        "Multicolor",
    ],
    "material": ["Goma maciza", "Hierro", "Acero", "Urethane", "Caucho"],
    "casquillo": ["Acero", "Latón"],
}

FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS = {
    "explicit_numeric_sku_regex": r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$",
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
}

FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS = {
    "numeric_suffix_family_regex": (
        r"^(?P<prefix>MKCL|MKCA|MKI|MKN|MKA|MK|DOP4A|DOPH|DNG|DOP|MPS|MU|MP|MH|MBPR|MBPZ|BN|BO|BOR)(?P<size>\d{3})$"
    ),
    "numeric_suffix_family_prefixes": [
        "MKCL",
        "MKCA",
        "MKI",
        "MKN",
        "MKA",
        "MK",
        "DOP4A",
        "DOPH",
        "DOP",
        "DNG",
        "MPS",
        "MU",
        "MP",
        "MH",
        "MBPR",
        "MBPZ",
        "BN",
        "BO",
        "BOR",
    ],
    "numeric_suffix_family_cross_training_prefixes": ["MKCL", "MKCA", "MKI", "MKN", "MKA", "MK"],
    "numeric_suffix_family_cross_training_slug": "cross-training",
    "numeric_suffix_family_cross_training_section_root": "CROSSTRAINING",
    "numeric_suffix_family_mancuerna_prefixes": ["MPS", "MU", "MP", "MH", "MBPR", "MBPZ"],
    "numeric_suffix_family_mancuernas_slug": "mancuernas",
    "numeric_suffix_family_bar_prefixes": ["BN", "BO", "BOR"],
    "numeric_suffix_family_barras_slug": "barras",
    "numeric_suffix_family_section_roots": ["DISCOS Y BARRAS", "MANCUERNAS"],
    "numeric_suffix_family_section": "DISCOS Y BARRAS",
    "numeric_suffix_family_confidence": 0.90,
}

FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS = {
    "numeric_compound_suffix_family_regex": (
        r"^(?P<prefix>JMU|JMP|JMH)(?P<series>\d{3})(?P<weight>\d{2})$"
    ),
    "numeric_compound_suffix_family_prefixes": ["JMU", "JMP", "JMH"],
    "numeric_compound_suffix_family_section_roots": ["MANCUERNAS"],
    "numeric_compound_suffix_family_mancuernas_slug": "mancuernas",
    "numeric_compound_suffix_family_confidence": 0.90,
}

FDL_HYPHEN_SUFFIX_FAMILY_DEFAULTS = {
    "hyphen_suffix_family_regex": r"^(?P<prefix>MPS)(?P<size>\d{3})-(?P<suffix_token>R)$",
    "hyphen_suffix_family_prefixes": ["MPS"],
    "hyphen_suffix_family_suffix_tokens": ["R"],
    "hyphen_suffix_family_section_roots": ["MANCUERNAS"],
    "hyphen_suffix_family_mancuernas_slug": "mancuernas",
    "hyphen_suffix_family_master_key_template": "{prefix}-{suffix_token}",
    "hyphen_suffix_family_confidence": 0.90,
}

FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS = {
    "cross_training_bumper_family_regex": r"^(?P<prefix>DOBHT|DOBCC|DOBF|DOB3C|DOBC|DOBN|DOB)(?P<size>\d{3})$",
    "cross_training_bumper_prefixes": ["DOBHT", "DOBCC", "DOBF", "DOB3C", "DOBC", "DOBN", "DOB"],
    "cross_training_bumper_section_root": "CROSSTRAINING",
    "cross_training_bumper_name_tokens": ["disco", "bumper"],
    "cross_training_bumper_category_slug": "discos",
    "cross_training_bumper_confidence": 0.90,
}

FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS = {
    "cross_training_block_family_regex": r"^(?:CRO\d{2,4}(?:NEXO)?|BOC\d{3}(?:NEXO)?)$",
    "cross_training_block_section_root": "CROSSTRAINING",
    "cross_training_block_category_slug": "cross-training",
    "cross_training_block_name_tokens": list(DEFAULT_CROSS_TRAINING_BLOCK_NAME_TOKENS),
    "cross_training_block_confidence": 0.90,
}

FDL_ALPHA_KIT_DEFAULTS = {
    "alpha_kit_sku_regex": r"^[A-Z]{3,12}$",
}

FDL_ATTR_FROM_SKU_DENY_DEFAULTS = {
    "attr_from_sku_deny": [
        {
            "spec_key": "peso_kg",
            "category_slugs": ["barras"],
            "section_roots": ["DISCOS Y BARRAS"],
        }
    ],
}


@dataclass
class SeedResult:
    exit_code: int
    parsed_rows: int = 0
    importable_rows: int = 0
    masters_created: int = 0
    variants_created: int = 0
    variants_updated: int = 0
    price_entries: int = 0
    rows_blocked: int = 0
    rows_spec_failed: int = 0
    catalog_id: str | None = None
    catalog_name: str | None = None
    catalog_items_created: int = 0


@dataclass
class PresentationCatalogResult:
    catalog_id: UUID
    catalog_name: str
    items_created: int
    items_skipped: int = 0


async def load_fdl_profile(session) -> tuple[Supplier, ImportProfile]:
    supplier = (
        await session.execute(select(Supplier).where(Supplier.code == "FDL"))
    ).scalar_one_or_none()
    if not supplier:
        raise RuntimeError("FDL supplier not found. Run migrations first: npm run db:migrate")

    profile = (
        await session.execute(
            select(ImportProfile).where(
                ImportProfile.supplier_id == supplier.id,
                ImportProfile.is_default.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not profile:
        raise RuntimeError("FDL default import profile not found. Run migrations first.")
    return supplier, profile


async def ensure_fdl_profile_grouping_config(session, profile: ImportProfile) -> None:
    """Merge attr_from_name into the default FDL profile when missing."""
    config = dict(profile.config or {})
    grouping = dict(config.get("grouping") or {})
    changed = False
    if "attr_from_name" not in grouping:
        grouping["attr_from_name"] = FDL_ATTR_FROM_NAME
        changed = True
    if "non_weight_prefixes" not in grouping:
        grouping["non_weight_prefixes"] = ["CRONEXO", "VARJH"]
        changed = True
    if "false_family_suffixes" not in grouping:
        grouping["false_family_suffixes"] = ["NEXO"]
        changed = True
    if "false_family_master_keys" not in grouping:
        grouping["false_family_master_keys"] = ["CRONEXO", "BOCNEXO"]
        changed = True
    for key, value in FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_HYPHEN_SUFFIX_FAMILY_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_ALPHA_KIT_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    for key, value in FDL_ATTR_FROM_SKU_DENY_DEFAULTS.items():
        if grouping.get(key) != value:
            grouping[key] = value
            changed = True
    if changed:
        config["grouping"] = grouping
        profile.config = config
        await session.commit()


async def create_default_presentation_catalog(
    session,
    *,
    price_list_id: UUID,
    catalog_name: str = DEFAULT_PRESENTATION_CATALOG_NAME,
) -> PresentationCatalogResult:
    """Create or update the default presentation catalog with variants from a price list."""
    catalog = (
        await session.execute(select(Catalog).where(Catalog.name == catalog_name))
    ).scalar_one_or_none()
    if not catalog:
        catalog = Catalog(
            name=catalog_name,
            default_markup_percent=DEFAULT_PRESENTATION_MARKUP_PERCENT,
            layout_mode="automatic",
        )
        session.add(catalog)
        await session.flush()

    variant_rows = (
        await session.execute(
            select(ProductVariant.id, ProductVariant.sku)
            .join(SupplierPriceEntry, SupplierPriceEntry.variant_id == ProductVariant.id)
            .where(SupplierPriceEntry.list_id == price_list_id)
            .order_by(ProductVariant.sku)
        )
    ).all()
    variant_ids = [row[0] for row in variant_rows]

    existing_variant_ids = set(
        (
            await session.execute(
                select(CatalogItem.variant_id).where(CatalogItem.catalog_id == catalog.id)
            )
        )
        .scalars()
        .all()
    )

    items_created = 0
    items_skipped = 0
    next_sort = (
        await session.execute(
            select(CatalogItem.sort_order)
            .where(CatalogItem.catalog_id == catalog.id)
            .order_by(CatalogItem.sort_order.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    sort_order = (next_sort + 1) if next_sort is not None else 0

    for variant_id in variant_ids:
        if variant_id in existing_variant_ids:
            items_skipped += 1
            continue
        session.add(
            CatalogItem(
                catalog_id=catalog.id,
                variant_id=variant_id,
                sort_order=sort_order,
            )
        )
        existing_variant_ids.add(variant_id)
        sort_order += 1
        items_created += 1

    await session.commit()
    return PresentationCatalogResult(
        catalog_id=catalog.id,
        catalog_name=catalog_name,
        items_created=items_created,
        items_skipped=items_skipped,
    )


async def run_seed(
    pdf_path: Path,
    *,
    fresh: bool,
    dry_run: bool,
    effective_date: date,
    force_review: bool = False,
    catalog_name: str = DEFAULT_PRESENTATION_CATALOG_NAME,
) -> SeedResult:
    if not pdf_path.is_file():
        print(
            f"PDF not found: {pdf_path}\nCopy the FDL tariff to temp/{DEFAULT_PDF_NAME}",
            file=sys.stderr,
        )
        return SeedResult(exit_code=1)

    content = pdf_path.read_bytes()
    print(f"Parsing {pdf_path}...")
    parsed_rows = parse_pdf(pdf_path)
    stats = compute_stats(parsed_rows)
    print(
        f"Parsed rows: {len(parsed_rows)} (ok={stats.get('ok', 0)}, revisar={stats.get('revisar', 0)})"
    )

    if dry_run:
        print("Dry run — no database changes.")
        return SeedResult(exit_code=0, parsed_rows=len(parsed_rows))

    async with async_session() as session:
        supplier, profile = await load_fdl_profile(session)
        await ensure_fdl_profile_grouping_config(session, profile)

        if fresh:
            print("Resetting catalog and product data...")
            deleted = await reset_catalog_data(session)
            for table, count in deleted.items():
                if count:
                    print(f"  deleted {table}: {count}")

        print("Seeding taxonomy (categories and brands)...")
        taxonomy = await run_taxonomy_seed(pdf_path, skip_categories=False, skip_brands=False)
        if taxonomy.exit_code != 0:
            print("Taxonomy seed failed.", file=sys.stderr)
            return SeedResult(exit_code=1)
        if taxonomy.categories:
            c = taxonomy.categories
            print(
                f"  categories: parents_created={c.parents_created}, "
                f"subcategories_created={c.subcategories_created}"
            )
        if taxonomy.brands:
            b = taxonomy.brands
            print(f"  brands: created={b.created}, total={b.total}")

        print("Seeding spec definitions and taxonomy rules...")
        await seed_spec_definitions(session)
        await seed_taxonomy_mapping_rules(session)
        await ensure_fallback_commercial_brand(session)

        batch, staged_rows, pipeline_stats, _action_stats = await run_preview_pipeline(
            session,
            content=content,
            profile=profile,
            supplier_id=supplier.id,
            filename=pdf_path.name,
            effective_date=effective_date,
        )
        pending = sum(1 for row in staged_rows if row.review_status == "pending")
        needs_review = sum(1 for row in staged_rows if row.review_status == "needs_review")
        print(f"Staged rows: {len(staged_rows)} (pending={pending}, needs_review={needs_review})")

        result = await confirm_import(
            session,
            batch_id=batch.id,
            profile=profile,
            effective_date=effective_date,
            allow_needs_review=force_review,
        )

        print("Creating presentation catalog...")
        presentation = await create_default_presentation_catalog(
            session,
            price_list_id=result.price_list.id,
            catalog_name=catalog_name,
        )

    print("Seed complete.")
    print(f"  price_list_id: {result.price_list.id}")
    print(f"  masters_created: {result.masters_created}")
    print(f"  variants_created: {result.variants_created}")
    print(f"  variants_updated: {result.variants_updated}")
    print(f"  price_entries: {result.entries_created}")
    print(f"  rows_blocked: {result.rows_blocked}")
    print(f"  rows_spec_failed: {result.rows_spec_failed}")
    print(f"  catalog_name: {presentation.catalog_name}")
    print(f"  catalog_id: {presentation.catalog_id}")
    print(f"  catalog_items_created: {presentation.items_created}")
    if presentation.items_skipped:
        print(f"  catalog_items_skipped: {presentation.items_skipped}")
    return SeedResult(
        exit_code=0,
        parsed_rows=len(parsed_rows),
        importable_rows=result.rows_imported,
        masters_created=result.masters_created,
        variants_created=result.variants_created,
        variants_updated=result.variants_updated,
        price_entries=result.entries_created,
        rows_blocked=result.rows_blocked,
        rows_spec_failed=result.rows_spec_failed,
        catalog_id=str(presentation.catalog_id),
        catalog_name=presentation.catalog_name,
        catalog_items_created=presentation.items_created,
    )
