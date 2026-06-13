"""Typed SQLAlchemy model factories for unit tests (no DB session required)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from app.models.entities import (
    Brand,
    CatalogItem,
    Category,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecAllowedValue,
    SpecDefinition,
    Unit,
)


def make_brand(name: str, *, slug: str | None = None) -> Brand:
    slug_value = slug or name.lower().replace(" ", "-")
    return Brand(id=uuid4(), name=name, slug=slug_value)


def make_category(
    name: str,
    *,
    slug: str | None = None,
    parent_id: UUID | None = None,
    parent: Category | None = None,
) -> Category:
    slug_value = slug or name.lower().replace(" ", "-")
    category = Category(id=uuid4(), name=name, slug=slug_value, parent_id=parent_id)
    category.parent = parent
    return category


def make_unit(*, symbol: str, code: str | None = None, label: str | None = None) -> Unit:
    code_value = code or symbol
    label_value = label or symbol
    return Unit(id=uuid4(), code=code_value, label=label_value, symbol=symbol)


def make_spec_definition(
    key: str,
    *,
    label: str | None = None,
    data_type: str = "text",
    role: str = "variant_axis",
    scope: str = "variant",
    unit: Unit | None = None,
    sort_order: int = 0,
    is_active: bool = True,
    is_printable: bool = True,
    definition_id: UUID | None = None,
) -> SpecDefinition:
    spec_id = definition_id or uuid4()
    definition = SpecDefinition(
        id=spec_id,
        key=key,
        label=label or key,
        data_type=data_type,
        scope=scope,
        role=role,
        sort_order=sort_order,
        is_active=is_active,
        is_printable=is_printable,
        unit_id=unit.id if unit else None,
    )
    definition.unit = unit
    return definition


def make_allowed_value(
    definition: SpecDefinition,
    *,
    value_key: str,
    label: str,
    allowed_id: UUID | None = None,
) -> SpecAllowedValue:
    return SpecAllowedValue(
        id=allowed_id or uuid4(),
        spec_definition_id=definition.id,
        value_key=value_key,
        label=label,
    )


def make_product_master(
    name: str,
    *,
    master_id: UUID | None = None,
    brand: Brand | None = None,
    category: Category | None = None,
    description: str | None = None,
    images: list | None = None,
) -> ProductMaster:
    master = ProductMaster(
        id=master_id or uuid4(),
        name=name,
        brand_id=brand.id if brand else None,
        category_id=category.id if category else None,
        description=description,
    )
    master.brand = brand
    master.category = category
    master.images = images or []
    return master


def make_variant_spec(
    definition: SpecDefinition,
    *,
    value_number: Decimal | None = None,
    value_text: str | None = None,
    allowed_value: SpecAllowedValue | None = None,
    variant_id: UUID | None = None,
) -> ProductVariantSpec:
    spec = ProductVariantSpec(
        id=uuid4(),
        variant_id=variant_id or uuid4(),
        spec_definition_id=definition.id,
        value_number=value_number,
        value_text=value_text,
        allowed_value_id=allowed_value.id if allowed_value else None,
    )
    spec.spec_definition = definition
    spec.allowed_value = allowed_value
    return spec


def make_master_spec(
    definition: SpecDefinition,
    *,
    master_id: UUID,
    value_number: Decimal | None = None,
    value_text: str | None = None,
    allowed_value: SpecAllowedValue | None = None,
) -> ProductMasterSpec:
    spec = ProductMasterSpec(
        id=uuid4(),
        master_id=master_id,
        spec_definition_id=definition.id,
        value_number=value_number,
        value_text=value_text,
        allowed_value_id=allowed_value.id if allowed_value else None,
    )
    spec.spec_definition = definition
    spec.allowed_value = allowed_value
    return spec


def make_product_variant(
    sku: str,
    *,
    variant_id: UUID | None = None,
    master: ProductMaster | None = None,
    display_name: str | None = None,
    reference_label: str | None = None,
    raw_name: str | None = None,
    brand: Brand | None = None,
    specs: list[ProductVariantSpec] | None = None,
    supplier_id: UUID | None = None,
) -> ProductVariant:
    master_obj = master or make_product_master("Test master")
    variant = ProductVariant(
        id=variant_id or uuid4(),
        product_master_id=master_obj.id,
        supplier_id=supplier_id or uuid4(),
        sku=sku,
        display_name=display_name or sku,
        reference_label=reference_label,
        raw_name=raw_name if raw_name is not None else display_name,
        brand_id=brand.id if brand else None,
    )
    variant.master = master_obj
    variant.brand = brand
    variant.specs = specs or []
    return variant


def make_catalog_item(
    variant: ProductVariant,
    *,
    sort_order: int = 0,
    catalog_id: UUID | None = None,
) -> CatalogItem:
    return CatalogItem(
        id=uuid4(),
        catalog_id=catalog_id or uuid4(),
        variant_id=variant.id,
        sort_order=sort_order,
        variant=variant,
    )
