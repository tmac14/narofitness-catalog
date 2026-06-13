"""Shared types for import parsers."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class RowStatus(StrEnum):
    OK = "ok"

    REVISAR = "revisar"

    DUPLICADO = "duplicado"


@dataclass
class ImportRow:
    row_index: int

    status: RowStatus

    sku: str | None

    name: str

    brand: str | None

    ean: str | None

    category_path: str

    price_amount: Decimal | None

    currency: str = "EUR"

    page_number: int = 0

    raw_lines: list[str] = field(default_factory=list)

    raw_name: str = ""

    normalized_name: str = ""

    # Grouping (filled after parse)

    master_key: str | None = None

    master_name: str | None = None

    display_name: str | None = None

    reference_label: str | None = None

    parsed_variant_specs_raw: dict = field(default_factory=dict)

    parsed_common_specs_raw: dict = field(default_factory=dict)

    grouping_confidence: float | None = None

    grouping_reason: str | None = None

    mapped_category_id: UUID | None = None

    mapped_category_slug: str | None = None

    mapped_category_confidence: float | None = None

    # Preview diff vs DB

    import_action: str = "new_variant"  # new_variant | price_update | revisar

    review_reasons: list[str] = field(default_factory=list)

    review_status: str = "pending"

    grouping_locked: bool = False

    # FDL family block context (parser)
    family_header_raw: str | None = None
    family_header_line_index: int | None = None
    family_block_id: str | None = None
    variant_name_raw: str | None = None
    taxonomy_name: str = ""
    brand_source: str | None = None
    brand_confidence: float | None = None
    variant_primary_name_raw: str | None = None
    product_note_raw: str | None = None
    product_capacity_raw: str | None = None
    product_capacity_count: float | None = None
    color_candidate_raw: str | None = None
    color_extraction_source: str | None = None

    def to_dict(self) -> dict:
        return {
            "row_index": self.row_index,
            "status": self.status.value,
            "sku": self.sku,
            "name": self.name,
            "brand": self.brand,
            "ean": self.ean,
            "category_path": self.category_path,
            "price_amount": str(self.price_amount) if self.price_amount is not None else None,
            "currency": self.currency,
            "page_number": self.page_number,
            "raw_name": self.raw_name,
            "normalized_name": self.normalized_name,
            "master_key": self.master_key,
            "master_name": self.master_name,
            "display_name": self.display_name,
            "reference_label": self.reference_label,
            "parsed_variant_specs_raw": self.parsed_variant_specs_raw,
            "parsed_common_specs_raw": self.parsed_common_specs_raw,
            "grouping_confidence": self.grouping_confidence,
            "grouping_reason": self.grouping_reason,
            "mapped_category_id": str(self.mapped_category_id) if self.mapped_category_id else None,
            "mapped_category_slug": self.mapped_category_slug,
            "mapped_category_confidence": self.mapped_category_confidence,
            "import_action": self.import_action,
            "review_reasons": self.review_reasons,
            "review_status": self.review_status,
            "grouping_locked": self.grouping_locked,
        }
