"""Generate a large stress-test catalogue for manual QA and builder validation."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import (
    Catalog,
    CatalogExport,
    CatalogItem,
    CatalogProductLayout,
    Category,
    ProductImage,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    Supplier,
    SupplierPriceEntry,
    SupplierPriceList,
    SupplierProductFamilyKey,
)
from app.services.seed_brands import get_or_create_brand
from app.services.seed_categories import seed_default_categories
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.spec_writer import load_spec_definitions, write_specs

STRESS_CATALOG_NAME = "QA Stress Catalog"
STRESS_SKU_PREFIX = "STRESS-"
STRESS_MASTER_KEY_PREFIX = "STRESS-M"
STRESS_IMAGE_PATH = "stress/placeholder.png"
DEFAULT_MASTER_COUNT = 350


async def load_fdl_supplier(session: AsyncSession) -> Supplier:
    supplier = (
        await session.execute(select(Supplier).where(Supplier.code == "FDL"))
    ).scalar_one_or_none()
    if not supplier:
        raise RuntimeError("FDL supplier not found. Run migrations first: npm run db:migrate")
    return supplier


StressProfileKind = Literal[
    "single",
    "grid_1attr",
    "row_2attr",
    "no_image",
    "no_category",
    "incomplete_variants",
]


@dataclass(frozen=True)
class StressProductProfile:
    kind: StressProfileKind
    variant_count: int
    with_image: bool
    with_category: bool
    incomplete: bool


@dataclass
class StressSeedResult:
    exit_code: int = 0
    catalog_id: str | None = None
    catalog_name: str = STRESS_CATALOG_NAME
    masters_created: int = 0
    masters_skipped: int = 0
    variants_created: int = 0
    variants_skipped: int = 0
    catalog_items_created: int = 0
    catalog_items_skipped: int = 0
    layout_overrides: int = 0
    row_wide_layout_overrides: int = 0
    profile_counts: dict[str, int] = field(default_factory=dict)


def stress_base_kind(index: int) -> Literal["single", "grid_1attr", "row_2attr"]:
    return ("single", "grid_1attr", "row_2attr")[index % 3]


def stress_product_profile(index: int) -> StressProductProfile:
    """Deterministic product profile for index 0..N-1."""
    bucket = index % 100
    base_kind = stress_base_kind(index)

    if bucket < 10:
        return StressProductProfile(
            kind="incomplete_variants",
            variant_count=2 + (index % 3),
            with_image=bucket % 3 != 0,
            with_category=True,
            incomplete=True,
        )
    if bucket < 18:
        return StressProductProfile(
            kind="no_category",
            variant_count=_variant_count_for(base_kind, index),
            with_image=True,
            with_category=False,
            incomplete=False,
        )
    if bucket < 33:
        return StressProductProfile(
            kind="no_image",
            variant_count=_variant_count_for(base_kind, index),
            with_image=False,
            with_category=True,
            incomplete=False,
        )

    return StressProductProfile(
        kind=base_kind,
        variant_count=_variant_count_for(base_kind, index),
        with_image=True,
        with_category=True,
        incomplete=False,
    )


def _variant_count_for(kind: str, index: int) -> int:
    if kind == "single":
        return 1
    return 2 + (index % 3)


def variant_specs_for_profile(profile: StressProductProfile, variant_index: int) -> dict[str, Any]:
    if profile.incomplete or profile.kind == "incomplete_variants":
        return {}
    if profile.kind == "single":
        return {}
    weights = [5, 8, 10, 12, 16, 20]
    colors = ["Negro", "Rojo", "Azul", "Rosa"]
    peso = weights[variant_index % len(weights)]
    if profile.kind == "grid_1attr":
        return {"peso_kg": peso}
    if profile.kind == "row_2attr":
        return {"peso_kg": peso, "color": colors[variant_index % len(colors)]}
    if profile.variant_count > 1:
        return {"peso_kg": peso}
    return {}


def stress_master_key(index: int) -> str:
    return f"{STRESS_MASTER_KEY_PREFIX}{index:04d}"


def stress_sku(master_index: int, variant_index: int) -> str:
    return f"{STRESS_SKU_PREFIX}{master_index:04d}-{variant_index:02d}"


def profile_kind_label(profile: StressProductProfile) -> str:
    if profile.kind == "no_image":
        return "no_image"
    if profile.kind == "no_category":
        return "no_category"
    if profile.incomplete or profile.kind == "incomplete_variants":
        return "incomplete_variants"
    return profile.kind


async def _load_assignable_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.name))
    categories = list(result.scalars().all())
    if len(categories) < 15:
        await seed_default_categories(session)
        result = await session.execute(select(Category).order_by(Category.name))
        categories = list(result.scalars().all())
    return categories


async def delete_stress_data(session: AsyncSession, *, catalog_name: str) -> dict[str, int]:
    """Remove stress catalogue and STRESS-* products (FK-safe)."""
    counts: dict[str, int] = {}

    stress_masters = (
        (
            await session.execute(
                select(ProductMaster.id).where(
                    ProductMaster.master_key.like(f"{STRESS_MASTER_KEY_PREFIX}%")
                )
            )
        )
        .scalars()
        .all()
    )
    master_ids = list(stress_masters)

    variant_filters = [ProductVariant.sku.like(f"{STRESS_SKU_PREFIX}%")]
    if master_ids:
        variant_filters.append(ProductVariant.product_master_id.in_(master_ids))
    stress_variants = (
        (await session.execute(select(ProductVariant.id).where(or_(*variant_filters))))
        .scalars()
        .all()
    )
    variant_ids = list(stress_variants)

    catalog = (
        await session.execute(select(Catalog).where(Catalog.name == catalog_name))
    ).scalar_one_or_none()

    if catalog:
        counts["catalog_product_layouts"] = (
            await session.execute(
                delete(CatalogProductLayout).where(CatalogProductLayout.catalog_id == catalog.id)
            )
        ).rowcount or 0
        counts["catalog_exports"] = (
            await session.execute(
                delete(CatalogExport).where(CatalogExport.catalog_id == catalog.id)
            )
        ).rowcount or 0
        counts["catalog_items"] = (
            await session.execute(delete(CatalogItem).where(CatalogItem.catalog_id == catalog.id))
        ).rowcount or 0
        counts["catalogs"] = (
            await session.execute(delete(Catalog).where(Catalog.id == catalog.id))
        ).rowcount or 0

    if master_ids:
        counts["catalog_product_layouts_by_master"] = (
            await session.execute(
                delete(CatalogProductLayout).where(CatalogProductLayout.master_id.in_(master_ids))
            )
        ).rowcount or 0

    if variant_ids:
        counts["orphan_catalog_items"] = (
            await session.execute(
                delete(CatalogItem).where(CatalogItem.variant_id.in_(variant_ids))
            )
        ).rowcount or 0
        counts["supplier_price_entries"] = (
            await session.execute(
                delete(SupplierPriceEntry).where(SupplierPriceEntry.variant_id.in_(variant_ids))
            )
        ).rowcount or 0
        counts["product_variant_specs"] = (
            await session.execute(
                delete(ProductVariantSpec).where(ProductVariantSpec.variant_id.in_(variant_ids))
            )
        ).rowcount or 0

    if master_ids:
        counts["product_images"] = (
            await session.execute(
                delete(ProductImage).where(ProductImage.master_id.in_(master_ids))
            )
        ).rowcount or 0
        counts["product_master_specs"] = (
            await session.execute(
                delete(ProductMasterSpec).where(ProductMasterSpec.master_id.in_(master_ids))
            )
        ).rowcount or 0
        counts["supplier_product_family_keys"] = (
            await session.execute(
                delete(SupplierProductFamilyKey).where(
                    SupplierProductFamilyKey.product_master_id.in_(master_ids)
                )
            )
        ).rowcount or 0

    if variant_ids:
        counts["product_variants"] = (
            await session.execute(delete(ProductVariant).where(ProductVariant.id.in_(variant_ids)))
        ).rowcount or 0

    if master_ids:
        counts["product_masters"] = (
            await session.execute(delete(ProductMaster).where(ProductMaster.id.in_(master_ids)))
        ).rowcount or 0

    await session.commit()
    return counts


async def run_stress_seed(
    *,
    catalog_name: str = STRESS_CATALOG_NAME,
    master_count: int = DEFAULT_MASTER_COUNT,
    fresh: bool = False,
    dry_run: bool = False,
) -> StressSeedResult:
    result = StressSeedResult(catalog_name=catalog_name)

    async with async_session() as session:
        supplier = await load_fdl_supplier(session)
        brand = await get_or_create_brand(session, "STRESS")

        if fresh and not dry_run:
            deleted = await delete_stress_data(session, catalog_name=catalog_name)
            print(f"Fresh: removed stress data: {deleted}")

        categories = await _load_assignable_categories(session)
        await seed_spec_definitions(session)
        spec_definitions = await load_spec_definitions(session)
        if len(categories) < 15:
            print(
                f"Warning: only {len(categories)} categories available (expected 15+).",
                file=sys.stderr,
            )

        if dry_run:
            profiles = [stress_product_profile(i) for i in range(master_count)]
            for profile in profiles:
                label = profile_kind_label(profile)
                result.profile_counts[label] = result.profile_counts.get(label, 0) + 1
            result.variants_created = sum(p.variant_count for p in profiles)
            print(
                f"Dry run — would create ~{master_count} masters, ~{result.variants_created} variants."
            )
            print(f"Profile distribution: {result.profile_counts}")
            return result

        price_list = SupplierPriceList(
            supplier_id=supplier.id,
            source_filename="stress_seed",
            effective_date=date.today(),
        )
        session.add(price_list)
        await session.flush()

        catalog = (
            await session.execute(select(Catalog).where(Catalog.name == catalog_name))
        ).scalar_one_or_none()
        if not catalog:
            catalog = Catalog(
                name=catalog_name,
                default_markup_percent=Decimal("15"),
                layout_mode="manual",
            )
            session.add(catalog)
            await session.flush()
        elif catalog.layout_mode != "manual":
            catalog.layout_mode = "manual"

        existing_items = (
            (
                await session.execute(
                    select(CatalogItem.variant_id).where(CatalogItem.catalog_id == catalog.id)
                )
            )
            .scalars()
            .all()
        )
        existing_variant_ids = set(existing_items)

        sort_order = (
            await session.execute(
                select(CatalogItem.sort_order)
                .where(CatalogItem.catalog_id == catalog.id)
                .order_by(CatalogItem.sort_order.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        next_sort = (sort_order + 1) if sort_order is not None else 0

        override_candidates: list[ProductMaster] = []
        row_wide_candidates: list[ProductMaster] = []

        for index in range(master_count):
            profile = stress_product_profile(index)
            label = profile_kind_label(profile)
            result.profile_counts[label] = result.profile_counts.get(label, 0) + 1

            master_key = stress_master_key(index)
            existing_master = (
                await session.execute(
                    select(ProductMaster).where(ProductMaster.master_key == master_key)
                )
            ).scalar_one_or_none()

            if existing_master:
                master = existing_master
                result.masters_skipped += 1
            else:
                category_id = None
                if profile.with_category and categories:
                    category_id = categories[index % len(categories)].id
                master = ProductMaster(
                    name=f"Stress Product {index:04d} ({label})",
                    master_key=master_key,
                    catalog_slug=f"stress-{index:04d}",
                    brand_id=brand.id if brand else None,
                    category_id=category_id,
                    status="confirmed",
                )
                session.add(master)
                await session.flush()
                result.masters_created += 1

                if profile.with_image:
                    session.add(
                        ProductImage(
                            master_id=master.id,
                            file_path=STRESS_IMAGE_PATH,
                            is_primary=True,
                            status="confirmed",
                        )
                    )

            if profile.kind == "row_2attr" and len(override_candidates) < 5:
                override_candidates.append(master)
            elif profile.kind == "row_2attr":
                row_wide_candidates.append(master)

            for variant_index in range(profile.variant_count):
                sku = stress_sku(index, variant_index)
                variant = (
                    await session.execute(
                        select(ProductVariant).where(
                            ProductVariant.supplier_id == supplier.id,
                            ProductVariant.sku == sku,
                        )
                    )
                ).scalar_one_or_none()

                if variant:
                    result.variants_skipped += 1
                else:
                    variant_specs = variant_specs_for_profile(profile, variant_index)
                    variant = ProductVariant(
                        product_master_id=master.id,
                        supplier_id=supplier.id,
                        sku=sku,
                        display_name=f"{master.name} / v{variant_index + 1}",
                        sort_order=variant_index,
                    )
                    session.add(variant)
                    await session.flush()
                    if variant_specs:
                        await write_specs(
                            session,
                            master=master,
                            variant=variant,
                            common_specs={},
                            variant_specs=variant_specs,
                            definitions=spec_definitions,
                        )
                    result.variants_created += 1

                    session.add(
                        SupplierPriceEntry(
                            list_id=price_list.id,
                            variant_id=variant.id,
                            price_amount=Decimal("10.00") + Decimal(variant_index),
                            currency="EUR",
                        )
                    )

                if variant.id not in existing_variant_ids:
                    session.add(
                        CatalogItem(
                            catalog_id=catalog.id,
                            variant_id=variant.id,
                            sort_order=next_sort,
                        )
                    )
                    existing_variant_ids.add(variant.id)
                    next_sort += 1
                    result.catalog_items_created += 1
                else:
                    result.catalog_items_skipped += 1

        for master in override_candidates:
            existing = (
                await session.execute(
                    select(CatalogProductLayout).where(
                        CatalogProductLayout.catalog_id == catalog.id,
                        CatalogProductLayout.master_id == master.id,
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                session.add(
                    CatalogProductLayout(
                        catalog_id=catalog.id,
                        master_id=master.id,
                        layout_id="single_standard",
                    )
                )
                result.layout_overrides += 1

        for master in row_wide_candidates:
            existing = (
                await session.execute(
                    select(CatalogProductLayout).where(
                        CatalogProductLayout.catalog_id == catalog.id,
                        CatalogProductLayout.master_id == master.id,
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                session.add(
                    CatalogProductLayout(
                        catalog_id=catalog.id,
                        master_id=master.id,
                        layout_id="variant_row_wide",
                    )
                )
                result.row_wide_layout_overrides += 1

        await session.commit()
        result.catalog_id = str(catalog.id)

    return result
