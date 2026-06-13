"""Commercial brand resolution for import rows (supplier vs product brand)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.services.seed_brands import KNOWN_BRAND_TOKENS
from app.services.text_utils import normalize_brand_name

FALLBACK_COMMERCIAL_BRAND = "Sin marca"
FALLBACK_BRAND_SLUG = "sin-marca"
FALLBACK_BRAND_SOURCE = "fallback_unbranded"

# Supplier/tariff tokens: valid in PDF section headers, not as default product brand.
_SECTION_BRAND_SKIP = frozenset({"FDL", "VARIOS"})
# Never assign as commercial product brand.
_NEVER_PRODUCT_BRAND = frozenset({"VARIOS"})

_PRODUCT_BRAND_TOKENS: tuple[str, ...] = tuple(
    sorted(
        (t for t in KNOWN_BRAND_TOKENS if t not in _NEVER_PRODUCT_BRAND),
        key=len,
        reverse=True,
    )
)


@dataclass(frozen=True)
class BrandResolution:
    brand: str
    brand_source: str
    brand_confidence: float


def extract_explicit_commercial_brand(text: str) -> str | None:
    """Detect explicit commercial brand tokens in product/family text (word-boundary)."""
    if not text or not text.strip():
        return None
    upper = text.upper()
    for token in _PRODUCT_BRAND_TOKENS:
        if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", upper):
            return normalize_brand_name(token)
    return None


def infer_brand_from_product_text(text: str) -> str | None:
    """Detect commercial brand tokens embedded in product name lines (not SKU)."""
    return extract_explicit_commercial_brand(text)


def _normalize_section_brand_commercial(name: str | None) -> str | None:
    """Section/subheader brand: skip supplier-only tokens (FDL from tariff header)."""
    if not name or not name.strip():
        return None
    normalized = normalize_brand_name(name)
    if normalized.upper() in _SECTION_BRAND_SKIP:
        return None
    if normalized.upper() in {
        normalize_brand_name(t) for t in KNOWN_BRAND_TOKENS if t not in _SECTION_BRAND_SKIP
    }:
        return normalized
    return None


def resolve_commercial_brand(
    *,
    section_brand: str | None = None,
    family_header_raw: str | None = None,
    variant_name_raw: str | None = None,
    raw_name: str = "",
    inline_brand: str | None = None,
) -> BrandResolution:
    """Resolve commercial brand; FDL/NEXO only when explicit in product/family text."""
    for source, text, confidence in (
        ("section_header", section_brand, 1.0),
        ("family_header", family_header_raw, 0.95),
        ("inline_line", inline_brand, 0.9),
        ("variant_rows", variant_name_raw, 0.8),
        ("product_name", raw_name, 0.7),
    ):
        if not text:
            continue
        if source in {"section_header", "inline_line"}:
            brand = _normalize_section_brand_commercial(text)
        else:
            brand = infer_brand_from_product_text(text)
        if brand:
            return BrandResolution(brand=brand, brand_source=source, brand_confidence=confidence)

    return BrandResolution(
        brand=FALLBACK_COMMERCIAL_BRAND,
        brand_source=FALLBACK_BRAND_SOURCE,
        brand_confidence=0.0,
    )


_LOGO_NEXO_RE = re.compile(r"LOGO\s+NEXO", re.I)
_NEXO_DASH_HEADER_RE = re.compile(r"-\s*NEXO\b", re.I)
_BARRAS_NEXO_HEADER_RE = re.compile(r"BARRAS\s+CROSSFIT\s*-\s*NEXO", re.I)


def _collect_nexo_signal_texts(row: Any) -> list[str]:
    texts: list[str] = []
    for attr in (
        "family_header_raw",
        "variant_name_raw",
        "name",
        "raw_name",
        "taxonomy_name",
        "category_path",
        "detected_category_path_raw",
    ):
        value = getattr(row, attr, None)
        if value and str(value).strip():
            texts.append(str(value))
    raw_lines = getattr(row, "raw_lines", None) or []
    texts.extend(str(line) for line in raw_lines if line and str(line).strip())
    return texts


def nexo_commercially_explicit(row: Any) -> bool:
    """True when NEXO is an explicit commercial line/brand signal, not a regex artifact alone."""
    sku = getattr(row, "sku", None)
    sku_upper = str(sku).upper() if sku else ""
    texts = _collect_nexo_signal_texts(row)
    if not texts:
        return False

    combined = " ".join(texts).upper()
    if _LOGO_NEXO_RE.search(combined):
        return True

    for text in texts:
        upper = text.upper()
        if _BARRAS_NEXO_HEADER_RE.search(upper):
            return True
        if _NEXO_DASH_HEADER_RE.search(upper):
            return True

    header = getattr(row, "family_header_raw", None)
    if header and _NEXO_DASH_HEADER_RE.search(str(header)):
        return True

    return bool(
        sku_upper.endswith("NEXO")
        and "LOGO" in combined
        and re.search(r"SACO\s+GUSANO|BARRAS\s+CROSSFIT", combined)
    )
