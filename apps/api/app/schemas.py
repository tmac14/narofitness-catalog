from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.pdf.layouts.validation import normalize_layout_mode


class HealthResponse(BaseModel):
    status: str
    version: str
    pdf_engine: str | None = None
    pdf_engine_error: str | None = None
    pdf_engine_fallback: str | None = None
    pdf_engines_available: list[str] = Field(default_factory=list)


class ParsedRowSchema(BaseModel):
    """Legacy preview row shape; prefer ImportRowOut for batch-based import."""

    row_index: int
    status: str
    sku: str | None
    name: str
    brand: str | None
    ean: str | None
    category_path: str
    price_amount: str | None
    currency: str = "EUR"
    page_number: int = 0
    master_key: str | None = None
    master_name: str | None = None
    display_name: str | None = None
    parsed_variant_specs_raw: dict[str, Any] = Field(default_factory=dict)
    parsed_common_specs_raw: dict[str, Any] = Field(default_factory=dict)
    import_action: str = "new_variant"
    review_reasons: list[str] = Field(default_factory=list)
    grouping_locked: bool = False


class ImportPreviewResponse(BaseModel):
    batch_id: UUID
    filename: str
    supplier_id: UUID
    import_profile_id: UUID
    source_document_id: UUID | None = None
    analysis_snapshot_id: UUID | None = None
    total_rows: int
    stats: dict[str, int]
    action_stats: dict[str, int] = Field(default_factory=dict)
    rows: list["ImportRowOut"]


class ImportConfirmRequest(BaseModel):
    batch_id: UUID
    supplier_id: UUID
    import_profile_id: UUID
    row_ids: list[UUID] | None = None
    effective_date: date | None = None
    allow_needs_review: bool = False


class ImportConfirmResponse(BaseModel):
    price_list_id: UUID
    batch_id: UUID | None = None
    masters_created: int
    variants_created: int
    variants_updated: int
    entries_created: int
    rows_skipped: int = 0
    rows_blocked: int = 0


class ImportBatchOut(BaseModel):
    id: UUID
    supplier_id: UUID
    import_profile_id: UUID | None
    source_filename: str
    parser_key: str
    parser_version: str
    effective_date: date | None
    status: str
    row_counts: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime | None = None
    created_by: str | None = None
    notes: str | None = None
    source_document_id: UUID | None = None
    analysis_snapshot_id: UUID | None = None

    model_config = {"from_attributes": True}


class ImportRowOut(BaseModel):
    id: UUID
    batch_id: UUID
    source_page: int | None = None
    source_row_index: int
    status: str | None = None
    sku: str | None = None
    name: str | None = None
    raw_name: str | None = None
    normalized_name: str | None = None
    brand: str | None = None
    ean: str | None = None
    category_path: str | None = None
    detected_category_path_raw: str | None = None
    mapped_category_id: UUID | None = None
    mapped_category_slug: str | None = None
    mapped_category_confidence: float | None = None
    price_amount: str | None = None
    currency: str = "EUR"
    master_key: str | None = None
    master_name: str | None = None
    display_name: str | None = None
    reference_label: str | None = None
    grouping_confidence: float | None = None
    grouping_reason: str | None = None
    parsed_variant_specs_raw: dict[str, Any] = Field(default_factory=dict)
    parsed_common_specs_raw: dict[str, Any] = Field(default_factory=dict)
    import_action: str | None = None
    review_reasons: list[Any] = Field(default_factory=list)
    review_status: str
    grouping_locked: bool = False
    confirmed_product_master_id: UUID | None = None
    confirmed_product_variant_id: UUID | None = None

    model_config = {"from_attributes": True}


class SpecValueOut(BaseModel):
    id: UUID | None = None
    spec_definition_id: UUID
    key: str
    label: str
    data_type: str
    role: str | None = None
    value: str | None = None
    sort_order: int = 0


class SupplierOut(BaseModel):
    id: UUID
    code: str
    name: str
    notes: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class SupplierCreate(BaseModel):
    code: str
    name: str
    notes: str | None = None


class ImportProfileOut(BaseModel):
    id: UUID
    supplier_id: UUID
    slug: str
    name: str
    parser_key: str
    config: dict[str, Any] = Field(default_factory=dict)
    is_default: bool
    is_active: bool

    model_config = {"from_attributes": True}


class ImportProfileCreate(BaseModel):
    slug: str
    name: str
    parser_key: str
    config: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False


class CategoryCreate(BaseModel):
    name: str
    slug: str | None = None
    parent_id: UUID | None = None


class CategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str
    parent_id: UUID | None
    children: list["CategoryOut"] = []

    model_config = {"from_attributes": True}


class CategoryPatch(BaseModel):
    name: str | None = None
    slug: str | None = None
    parent_id: UUID | None = None


class VariantAttributeColumnOut(BaseModel):
    key: str
    label: str


BrandMode = Literal["none", "uniform", "mixed"]


class ProductMasterListVariantOut(BaseModel):
    id: UUID
    sku: str
    display_name: str | None = None
    reference_label: str | None = None
    price: str | None = None
    image_url: str | None = None
    brand: str | None = None
    brand_display: str | None = None
    variant_label: str | None = None
    attributes: dict[str, str | None] = Field(default_factory=dict)
    source_page: int | None = None
    source_pages: list[int] = Field(default_factory=list)


class ProductMasterOut(BaseModel):
    id: UUID
    name: str
    brand: str | None
    brand_mode: BrandMode = "none"
    brand_display: str | None = None
    show_brand_column: bool = False
    show_variant_name_column: bool = False
    category_id: UUID | None
    category_name: str | None = None
    category_parent_name: str | None = None
    category_sub_name: str | None = None
    image_url: str | None = None
    master_key: str | None
    notes: str | None
    variant_count: int = 0
    references: list[str] = Field(default_factory=list)
    price: str | None = None
    variant_columns: list[VariantAttributeColumnOut] = Field(default_factory=list)
    variants: list[ProductMasterListVariantOut] = Field(default_factory=list)
    source_page: int | None = None
    source_pages: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductMasterCreate(BaseModel):
    name: str
    brand: str | None = None
    category_id: UUID | None = None
    notes: str | None = None
    master_key: str | None = None


class ProductMasterPatch(BaseModel):
    name: str | None = None
    brand: str | None = None
    category_id: UUID | None = None
    notes: str | None = None


class ProductImageFromUrlCreate(BaseModel):
    url: str


class ProductImageOut(BaseModel):
    id: UUID
    url: str
    is_primary: bool
    status: str
    variant_id: UUID | None = None
    source_type: Literal["upload", "external_url"] = "upload"
    external_url: str | None = None


class ProductVariantOut(BaseModel):
    id: UUID
    product_master_id: UUID
    supplier_id: UUID
    supplier_code: str | None = None
    sku: str
    ean: str | None
    display_name: str | None
    brand: str | None = None
    brand_display: str | None = None
    variant_label: str | None = None
    specs: list[SpecValueOut] = Field(default_factory=list)
    latest_price: str | None = None
    master_name: str | None = None
    images: list[ProductImageOut] = Field(default_factory=list)
    source_page: int | None = None
    source_pages: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductVariantCreate(BaseModel):
    product_master_id: UUID
    supplier_id: UUID
    sku: str
    ean: str | None = None
    display_name: str | None = None
    base_price: Decimal | None = None


class ProductVariantPatch(BaseModel):
    ean: str | None = None
    display_name: str | None = None
    sort_order: int | None = None


class ProductMasterDetailOut(ProductMasterOut):
    images: list[ProductImageOut] = []
    specs: list[SpecValueOut] = []
    variants: list[ProductVariantOut] = []  # pyright: ignore[reportIncompatibleVariableOverride]


class SpecValueWrite(BaseModel):
    key: str
    value: str | None = None


class MasterSpecsPut(BaseModel):
    specs: list[SpecValueWrite]


class ProductMasterListResponse(BaseModel):
    items: list[ProductMasterOut]
    total: int
    page: int
    page_size: int


class PriceHistoryItem(BaseModel):
    list_id: UUID
    imported_at: datetime
    effective_date: date | None
    price_amount: str
    source_filename: str | None = None
    delta_pct_vs_previous: str | None = None


class CatalogCreate(BaseModel):
    name: str
    default_markup_percent: Decimal = Field(default=Decimal("0"))
    show_iva_column: bool = False
    show_description_column: bool = True
    layout_mode: Literal["automatic", "uniform", "manual"] = "automatic"
    uniform_layout_id: str | None = None

    @field_validator("layout_mode", mode="before")
    @classmethod
    def _validate_layout_mode(cls, value: str | None) -> str:
        return normalize_layout_mode(value)


class CatalogPatch(BaseModel):
    name: str | None = None
    default_markup_percent: Decimal | None = None
    show_iva_column: bool | None = None
    show_description_column: bool | None = None
    cover_subtitle: str | None = Field(default=None, max_length=255)
    layout_mode: Literal["automatic", "uniform", "manual"] | None = None
    uniform_layout_id: str | None = None

    @field_validator("layout_mode", mode="before")
    @classmethod
    def _validate_layout_mode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_layout_mode(value)


class CatalogItemCreate(BaseModel):
    variant_id: UUID
    markup_percent: Decimal | None = None
    final_price_override: Decimal | None = None
    sort_order: int = 0


class CatalogItemPatch(BaseModel):
    markup_percent: Decimal | None = None
    final_price_override: Decimal | None = None
    sort_order: int | None = None


class CatalogItemReorderEntry(BaseModel):
    id: UUID
    sort_order: int


class CatalogItemReorder(BaseModel):
    items: list[CatalogItemReorderEntry] = Field(default_factory=list)


class CatalogItemReorderResult(BaseModel):
    updated: int


class ResolvedCatalogItem(BaseModel):
    id: UUID
    variant_id: UUID
    master_id: UUID
    sku: str
    name: str
    brand: str | None
    base_price: str | None
    markup_percent: Decimal | None
    final_price_override: Decimal | None
    final_price: str | None
    sort_order: int


class CatalogSectionCoverOut(BaseModel):
    category_id: UUID
    category_name: str
    cover_image_url: str | None = None
    description: str | None = None


class CatalogCoverImageOut(BaseModel):
    cover_image_path: str
    cover_image_url: str


class CatalogDetail(BaseModel):
    id: UUID
    name: str
    default_markup_percent: Decimal
    show_iva_column: bool
    show_description_column: bool
    cover_image_url: str | None = None
    cover_subtitle: str | None = None
    layout_mode: str
    uniform_layout_id: str | None
    items: list[ResolvedCatalogItem]
    product_layouts: list["CatalogProductLayoutOut"] = Field(default_factory=list)
    section_covers: list[CatalogSectionCoverOut] = Field(default_factory=list)


class CatalogProductLayoutOut(BaseModel):
    master_id: UUID
    layout_id: str


class CatalogProductLayoutPut(BaseModel):
    layout_id: str


class CatalogProductLayoutBulk(BaseModel):
    layout_id: str | None = None
    master_ids: list[UUID] = Field(default_factory=list)


class PriceListOut(BaseModel):
    id: UUID
    supplier_id: UUID
    source_filename: str
    effective_date: date | None
    imported_at: datetime

    model_config = {"from_attributes": True}


class CatalogBulkItems(BaseModel):
    variant_ids: list[UUID] = Field(default_factory=list)
    category_id: UUID | None = None


class DiffItem(BaseModel):
    sku: str
    name: str
    price_a: str | None
    price_b: str | None
    delta_abs: str | None
    delta_pct: str | None
    change_type: str = "both"  # both | only_a | only_b | changed


class SettingsOut(BaseModel):
    iva_disclaimer: str = "Los precios indicados no incluyen el IVA"
    catalog_logo_url: str | None = None
    iva_rate_percent: str = "21"
    catalog_template: str = "branded"
    show_iva_column: bool = True


class SettingsPatch(BaseModel):
    iva_disclaimer: str | None = None
    iva_rate_percent: str | None = None
    catalog_template: str | None = None
    show_iva_column: bool | None = None


class CanonicalCategoryNodeOut(BaseModel):
    id: UUID
    name: str
    slug: str
    parent_id: UUID | None
    full_path: str
    level: int
    children: list["CanonicalCategoryNodeOut"] = Field(default_factory=list)


class SourceCategoryExampleRowOut(BaseModel):
    sku: str | None = None
    normalized_name: str | None = None
    source_row_index: int


class SourceCategoryDiscoveryOut(BaseModel):
    source_category_path_raw: str
    normalized_source_category_key: str
    row_count: int
    example_rows: list[SourceCategoryExampleRowOut] = Field(default_factory=list)
    currently_mapped_category_id: UUID | None = None
    currently_mapped_category_slug: str | None = None
    mapped_category_confidence: float | None = None
    mapping_rule_id: UUID | None = None
    mapping_status: Literal["mapped", "unmapped", "ambiguous", "ignored"]
    requires_review: bool
    notes: str | None = None
    proposed_category_id: UUID | None = None
    proposed_category_slug: str | None = None
    proposal_confidence: float = 0.0
    proposal_reason: str = ""
    proposal_source: str = "none"


class SourceCategoryDiscoveryResponse(BaseModel):
    batch_id: UUID
    supplier_id: UUID
    import_profile_id: UUID | None
    source_categories: list[SourceCategoryDiscoveryOut]


class TaxonomyMappingConfirmRequest(BaseModel):
    supplier_id: UUID | None = None
    import_profile_id: UUID | None = None
    source_category_path_raw: str | None = None
    normalized_source_category_key: str | None = None
    target_category_id: UUID
    confidence: float = 1.0
    requires_review: bool = False
    priority: int = 100
    notes: str | None = None


class TaxonomyMappingIgnoreRequest(BaseModel):
    supplier_id: UUID | None = None
    import_profile_id: UUID | None = None
    source_category_path_raw: str | None = None
    normalized_source_category_key: str | None = None
    notes: str | None = None
    priority: int = 200


class TaxonomyMappingRuleOut(BaseModel):
    id: UUID
    match_type: str
    match_value: str
    supplier_id: UUID | None = None
    import_profile_id: UUID | None = None
    target_category_id: UUID | None = None
    target_subcategory_id: UUID | None = None
    confidence: float
    requires_review: bool
    priority: int
    notes: str | None = None
    is_active: bool = True


class RemapTaxonomyResponse(BaseModel):
    batch_id: UUID
    rows_updated: int
    mapped_count: int
    unmapped_count: int
    ignored_count: int = 0
    rows: list[ImportRowOut] = Field(default_factory=list)


JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class JobOut(BaseModel):
    id: UUID
    job_type: str
    status: JobStatus
    progress_percent: int | None = None
    message: str | None = None
    error_message: str | None = None
    catalog_id: UUID | None = None
    catalog_name: str | None = None
    subject_type: str | None = None
    subject_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    download_available: bool = False
    can_cancel: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobListResponse(BaseModel):
    items: list[JobOut]
    total: int


class JobCancelResponse(BaseModel):
    job: JobOut
    cancelled: bool


class SourceDocumentOut(BaseModel):
    id: UUID
    sha256: str
    original_filename: str
    mime_type: str
    byte_size: int
    page_count: int
    validation_status: str
    validation_error: str | None
    created_at: datetime
    created_by: str | None


class SourceDocumentWorkflowCapabilities(BaseModel):
    direct_adaptation: bool
    pim_import: bool
    analysis: bool


class SourceDocumentCapabilitiesOut(BaseModel):
    source_document_id: str
    sha256: str
    page_count: int
    validation_status: str
    profile_match_status: str | None = None
    workflows: SourceDocumentWorkflowCapabilities
    cover_pages: dict[str, Any] | None = None
    note: str


class DocumentAnalysisSnapshotOut(BaseModel):
    id: UUID
    source_document_id: UUID
    snapshot_fingerprint: str
    analyzer_key: str
    analyzer_version: str
    profile_key: str
    profile_version: str
    profile_match_status: str
    created_at: datetime
    snapshot: dict[str, Any]


class CatalogAdaptationCreateRequest(BaseModel):
    name: str | None = None


class CatalogAdaptationRecipeVersionOut(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    schema_version: str
    recipe_fingerprint: str
    recipe: dict[str, Any]
    created_at: datetime


class CatalogAdaptationProjectOut(BaseModel):
    id: UUID
    source_document_id: UUID
    analysis_snapshot_id: UUID | None
    name: str
    status: str
    profile_key: str
    profile_version: str
    active_recipe_version_id: UUID | None
    active_recipe: CatalogAdaptationRecipeVersionOut | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None


class CatalogAdaptationExportOut(BaseModel):
    id: UUID
    project_id: UUID
    recipe_version_id: UUID
    job_id: UUID | None
    export_kind: str
    status: str
    manifest_fingerprint: str
    manifest: dict[str, Any]
    artifact_path: str | None
    pdf_artifact_path: str | None
    output_profile: str
    delivery_mode: str
    expires_at: datetime | None = None
    created_at: datetime


class AdaptationJobRequest(BaseModel):
    output_profile: str | None = None
    delivery_mode: str | None = None
    ephemeral_ttl_seconds: int | None = None


class CatalogAdaptationApprovalCreateRequest(BaseModel):
    export_id: UUID
    approved_by: str | None = None
    approval_note: str | None = None


class CatalogAdaptationApprovalOut(BaseModel):
    id: UUID
    project_id: UUID
    recipe_version_id: UUID
    export_id: UUID
    manifest_fingerprint: str
    output_profile: str
    renderer_version: str
    approved_by: str | None
    approval_note: str | None
    created_at: datetime


class CatalogAdaptationExportListResponse(BaseModel):
    items: list[CatalogAdaptationExportOut]
    total: int


class AdaptationCoverSlotOut(BaseModel):
    slot_id: str
    role: str
    cover_type: str | None = None
    role_label: str | None = None
    source_page_number: int
    target_page_number: int
    prepend_page: bool = False
    section_key: str | None = None
    section_label: str | None = None
    confidence: float | None = None
    detection_note: str | None = None
    asset_path: str | None = None
    asset_sha256: str | None = None
    asset_url: str | None = None
    asset_status: str


class AdaptationCoverSlotsOut(BaseModel):
    project_id: str
    page_offset: int
    prepend_main_cover: bool
    detection_method: str | None = None
    slots: list[AdaptationCoverSlotOut]


class AdaptationCoverLibraryAssignRequest(BaseModel):
    relative_path: str


class MediaLibraryImageOut(BaseModel):
    relative_path: str
    url: str
    filename: str


class MediaLibraryImagesOut(BaseModel):
    items: list[MediaLibraryImageOut]
    total: int
