import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    masters: Mapped[list["ProductMaster"]] = relationship(back_populates="brand")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="brand")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped["Category | None"] = relationship(remote_side=[id])
    masters: Mapped[list["ProductMaster"]] = relationship(back_populates="category")
    spec_profiles: Mapped[list["CategorySpecProfile"]] = relationship(back_populates="category")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)

    spec_definitions: Mapped[list["SpecDefinition"]] = relationship(back_populates="unit")


class SpecDefinition(Base):
    __tablename__ = "spec_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    data_type: Mapped[str] = mapped_column(String(16), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id"))
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_printable: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)

    unit: Mapped[Unit | None] = relationship(back_populates="spec_definitions")
    allowed_values: Mapped[list["SpecAllowedValue"]] = relationship(
        back_populates="spec_definition"
    )


class SpecAllowedValue(Base):
    __tablename__ = "spec_allowed_values"
    __table_args__ = (
        UniqueConstraint("spec_definition_id", "value_key", name="uq_spec_allowed_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    spec_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spec_definitions.id")
    )
    value_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    spec_definition: Mapped[SpecDefinition] = relationship(back_populates="allowed_values")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    import_profiles: Mapped[list["ImportProfile"]] = relationship(back_populates="supplier")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="supplier")
    price_lists: Mapped[list["SupplierPriceList"]] = relationship(back_populates="supplier")
    family_keys: Mapped[list["SupplierProductFamilyKey"]] = relationship(back_populates="supplier")


class ImportProfile(Base):
    __tablename__ = "import_profiles"
    __table_args__ = (UniqueConstraint("supplier_id", "slug", name="uq_supplier_profile_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parser_key: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_default: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier: Mapped[Supplier] = relationship(back_populates="import_profiles")


class ProductMaster(Base):
    __tablename__ = "product_masters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_name: Mapped[str | None] = mapped_column(Text)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id")
    )
    description: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    master_key: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    catalog_slug: Mapped[str | None] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    brand: Mapped[Brand | None] = relationship(back_populates="masters")
    category: Mapped[Category | None] = relationship(back_populates="masters")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="master", cascade="all, delete"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="master", foreign_keys="ProductImage.master_id"
    )
    specs: Mapped[list["ProductMasterSpec"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    family_keys: Mapped[list["SupplierProductFamilyKey"]] = relationship(
        back_populates="product_master"
    )


class ProductMasterSpec(Base):
    __tablename__ = "product_master_specs"
    __table_args__ = (UniqueConstraint("master_id", "spec_definition_id", name="uq_master_spec"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_masters.id")
    )
    spec_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spec_definitions.id")
    )
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    value_text: Mapped[str | None] = mapped_column(Text)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    allowed_value_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spec_allowed_values.id")
    )
    source: Mapped[str] = mapped_column(String(32), default="import")
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    master: Mapped[ProductMaster] = relationship(back_populates="specs")
    spec_definition: Mapped[SpecDefinition] = relationship()
    allowed_value: Mapped[SpecAllowedValue | None] = relationship()


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("supplier_id", "sku", name="uq_supplier_sku"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    product_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_masters.id")
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ean: Mapped[str | None] = mapped_column(String(20))
    display_name: Mapped[str | None] = mapped_column(String(255))
    reference_label: Mapped[str | None] = mapped_column(String(255))
    raw_name: Mapped[str | None] = mapped_column(Text)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="confirmed")
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    master: Mapped[ProductMaster] = relationship(back_populates="variants")
    brand: Mapped[Brand | None] = relationship(back_populates="variants")
    supplier: Mapped[Supplier] = relationship(back_populates="variants")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="variant", foreign_keys="ProductImage.variant_id"
    )
    specs: Mapped[list["ProductVariantSpec"]] = relationship(
        back_populates="variant", cascade="all, delete-orphan"
    )
    price_entries: Mapped[list["SupplierPriceEntry"]] = relationship(back_populates="variant")
    catalog_items: Mapped[list["CatalogItem"]] = relationship(back_populates="variant")


class ProductVariantSpec(Base):
    __tablename__ = "product_variant_specs"
    __table_args__ = (UniqueConstraint("variant_id", "spec_definition_id", name="uq_variant_spec"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id")
    )
    spec_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spec_definitions.id")
    )
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    value_text: Mapped[str | None] = mapped_column(Text)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    allowed_value_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spec_allowed_values.id")
    )
    source: Mapped[str] = mapped_column(String(32), default="import")
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    variant: Mapped[ProductVariant] = relationship(back_populates="specs")
    spec_definition: Mapped[SpecDefinition] = relationship()
    allowed_value: Mapped[SpecAllowedValue | None] = relationship()


class CategorySpecProfile(Base):
    __tablename__ = "category_spec_profiles"
    __table_args__ = (
        UniqueConstraint("category_id", "spec_definition_id", name="uq_category_spec_profile"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))
    spec_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spec_definitions.id")
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_variant_axis_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_highlight: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    print_group: Mapped[str | None] = mapped_column(String(64))

    category: Mapped[Category] = relationship(back_populates="spec_profiles")
    spec_definition: Mapped[SpecDefinition] = relationship()


class SupplierProductFamilyKey(Base):
    __tablename__ = "supplier_product_family_keys"
    __table_args__ = (
        UniqueConstraint("supplier_id", "source_master_key", name="uq_supplier_source_master_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    source_master_key: Mapped[str] = mapped_column(String(128), nullable=False)
    product_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_masters.id")
    )
    import_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_profiles.id")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    supplier: Mapped[Supplier] = relationship(back_populates="family_keys")
    product_master: Mapped[ProductMaster] = relationship(back_populates="family_keys")


class TaxonomyMappingRule(Base):
    __tablename__ = "taxonomy_mapping_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id")
    )
    import_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_profiles.id")
    )
    match_type: Mapped[str] = mapped_column(String(32), nullable=False)
    match_value: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    target_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id")
    )
    target_subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id")
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("1.0"))
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    import_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_profiles.id")
    )
    source_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    parser_key: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    row_counts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=True, index=True
    )
    analysis_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_analysis_snapshots.id"),
        nullable=True,
        index=True,
    )

    rows: Mapped[list["ImportRow"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class ImportRow(Base):
    __tablename__ = "import_rows"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_row_index", name="uq_import_row_batch_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_batches.id"))
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_lines: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    raw_name: Mapped[str | None] = mapped_column(Text)
    normalized_name: Mapped[str | None] = mapped_column(Text)
    detected_category_path_raw: Mapped[str | None] = mapped_column(Text)
    mapped_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id")
    )
    mapped_category_slug: Mapped[str | None] = mapped_column(String(128))
    mapped_category_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    brand_raw: Mapped[str | None] = mapped_column(String(128))
    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id"))
    sku: Mapped[str | None] = mapped_column(String(64))
    ean: Mapped[str | None] = mapped_column(String(20))
    price_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    master_key: Mapped[str | None] = mapped_column(String(128))
    master_name: Mapped[str | None] = mapped_column(Text)
    reference_label: Mapped[str | None] = mapped_column(String(255))
    grouping_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    grouping_reason: Mapped[str | None] = mapped_column(Text)
    parsed_variant_specs_raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    parsed_common_specs_raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    parsed_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    review_reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    review_status: Mapped[str] = mapped_column(String(32), default="pending")
    confirmed_product_master_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_masters.id")
    )
    confirmed_product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    batch: Mapped[ImportBatch] = relationship(back_populates="rows")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_masters.id")
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default="upload")
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), default="confirmed")

    master: Mapped[ProductMaster] = relationship(back_populates="images", foreign_keys=[master_id])
    variant: Mapped[ProductVariant | None] = relationship(
        back_populates="images", foreign_keys=[variant_id]
    )


class SupplierPriceList(Base):
    __tablename__ = "supplier_price_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    import_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_profiles.id")
    )
    source_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    supplier: Mapped[Supplier] = relationship(back_populates="price_lists")
    entries: Mapped[list["SupplierPriceEntry"]] = relationship(back_populates="price_list")


class SupplierPriceEntry(Base):
    __tablename__ = "supplier_price_entries"
    __table_args__ = (UniqueConstraint("list_id", "variant_id", name="uq_list_variant"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_price_lists.id")
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id")
    )
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    price_list: Mapped[SupplierPriceList] = relationship(back_populates="entries")
    variant: Mapped[ProductVariant] = relationship(back_populates="price_entries")


class Catalog(Base):
    __tablename__ = "catalogs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_markup_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"))
    show_iva_column: Mapped[bool] = mapped_column(default=False)
    show_description_column: Mapped[bool] = mapped_column(default=True)
    cover_image_path: Mapped[str | None] = mapped_column(String(512))
    cover_subtitle: Mapped[str | None] = mapped_column(String(255))
    layout_mode: Mapped[str] = mapped_column(String(16), default="automatic", nullable=False)
    uniform_layout_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["CatalogItem"]] = relationship(
        back_populates="catalog", cascade="all, delete"
    )
    exports: Mapped[list["CatalogExport"]] = relationship(back_populates="catalog")
    product_layouts: Mapped[list["CatalogProductLayout"]] = relationship(
        back_populates="catalog", cascade="all, delete-orphan"
    )
    section_covers: Mapped[list["CatalogSectionCover"]] = relationship(
        back_populates="catalog", cascade="all, delete-orphan"
    )


class CatalogSectionCover(Base):
    __tablename__ = "catalog_section_covers"
    __table_args__ = (
        UniqueConstraint("catalog_id", "category_id", name="uq_catalog_section_cover"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    catalog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalogs.id", ondelete="CASCADE")
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT")
    )
    cover_image_path: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    catalog: Mapped[Catalog] = relationship(back_populates="section_covers")
    category: Mapped["Category"] = relationship()


class CatalogProductLayout(Base):
    __tablename__ = "catalog_product_layouts"
    __table_args__ = (UniqueConstraint("catalog_id", "master_id", name="uq_catalog_master_layout"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    catalog_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalogs.id"))
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_masters.id")
    )
    layout_id: Mapped[str] = mapped_column(String(64), nullable=False)

    catalog: Mapped[Catalog] = relationship(back_populates="product_layouts")
    master: Mapped[ProductMaster] = relationship()


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (UniqueConstraint("catalog_id", "variant_id", name="uq_catalog_variant"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    catalog_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalogs.id"))
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id")
    )
    markup_percent: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    final_price_override: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sort_order: Mapped[int] = mapped_column(default=0)

    catalog: Mapped[Catalog] = relationship(back_populates="items")
    variant: Mapped[ProductVariant] = relationship(back_populates="catalog_items")


class CatalogExport(Base):
    __tablename__ = "catalog_exports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    catalog_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalogs.id"))
    file_path: Mapped[str] = mapped_column(String(512))
    engine: Mapped[str] = mapped_column(String(32))
    exported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    catalog: Mapped[Catalog] = relationship(back_populates="exports")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    progress_percent: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str | None] = mapped_column(String(512))
    result_path: Mapped[str | None] = mapped_column(String(512))
    error_message: Mapped[str | None] = mapped_column(Text)
    catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalogs.id", ondelete="SET NULL"), nullable=True
    )
    subject_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    job_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    catalog: Mapped["Catalog | None"] = relationship()


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="application/pdf")
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="valid")
    validation_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str | None] = mapped_column(String(128))


class DocumentAnalysisSnapshot(Base):
    __tablename__ = "document_analysis_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "analyzer_key",
            "analyzer_version",
            "config_fingerprint",
            name="uq_document_analysis_snapshot_contract",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=False, index=True
    )
    snapshot_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    analyzer_key: Mapped[str] = mapped_column(String(128), nullable=False)
    analyzer_version: Mapped[str] = mapped_column(String(32), nullable=False)
    config_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_key: Mapped[str] = mapped_column(String(128), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    profile_match_status: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_document: Mapped["SourceDocument"] = relationship()


class CatalogAdaptationProject(Base):
    __tablename__ = "catalog_adaptation_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=False, index=True
    )
    analysis_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_analysis_snapshots.id"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    profile_key: Mapped[str] = mapped_column(String(128), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    active_recipe_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "catalog_adaptation_recipe_versions.id",
            name="fk_catalog_adaptation_projects_active_recipe_version_id",
            use_alter=True,
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(128))

    source_document: Mapped["SourceDocument"] = relationship()
    analysis_snapshot: Mapped["DocumentAnalysisSnapshot | None"] = relationship()
    recipe_versions: Mapped[list["CatalogAdaptationRecipeVersion"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="CatalogAdaptationRecipeVersion.project_id",
    )
    exports: Mapped[list["CatalogAdaptationExport"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class CatalogAdaptationRecipeVersion(Base):
    __tablename__ = "catalog_adaptation_recipe_versions"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_catalog_adaptation_recipe_project_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_adaptation_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    recipe_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    recipe_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["CatalogAdaptationProject"] = relationship(
        back_populates="recipe_versions",
        foreign_keys=[project_id],
    )


class CatalogAdaptationExport(Base):
    __tablename__ = "catalog_adaptation_exports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_adaptation_projects.id"),
        nullable=False,
        index=True,
    )
    recipe_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_adaptation_recipe_versions.id"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("background_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    export_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="preview")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="stub_completed")
    manifest_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(1024))
    pdf_artifact_path: Mapped[str | None] = mapped_column(String(1024))
    output_profile: Mapped[str] = mapped_column(String(32), nullable=False, default="email_optimized")
    delivery_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="persist")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["CatalogAdaptationProject"] = relationship(back_populates="exports")
    recipe_version: Mapped["CatalogAdaptationRecipeVersion"] = relationship()


class CatalogAdaptationApproval(Base):
    __tablename__ = "catalog_adaptation_approvals"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_catalog_adaptation_approvals_project"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_adaptation_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipe_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_adaptation_recipe_versions.id"),
        nullable=False,
    )
    export_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_adaptation_exports.id", ondelete="CASCADE"),
        nullable=False,
    )
    manifest_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    output_profile: Mapped[str] = mapped_column(String(32), nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(32), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(128))
    approval_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["CatalogAdaptationProject"] = relationship()
    export: Mapped["CatalogAdaptationExport"] = relationship()
