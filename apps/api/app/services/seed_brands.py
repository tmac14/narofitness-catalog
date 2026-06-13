"""Extract and seed brands from FDL tariff PDFs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Brand
from app.services.text_utils import brand_slug, normalize_brand_name

HEADER_FONT_SIZE = 20.76
SUBHEADER_MIN_SIZE = 8.0
SUBHEADER_MAX_SIZE = 10.0
FALLBACK_COMMERCIAL_BRAND = "Sin marca"
FALLBACK_BRAND_SLUG = "sin-marca"
KNOWN_BRAND_TOKENS = frozenset({"XEBEX", "REEBOK", "ADIDAS", "HORIZON", "NEXO", "FDL", "VARIOS"})


@dataclass
class BrandSeedResult:
    created: int = 0
    updated: int = 0
    total: int = 0
    slugs: list[str] | None = None


def _lines_with_size(page: fitz.Page) -> list[tuple[str, float]]:
    lines: list[tuple[str, float]] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(span["text"] for span in spans).strip()
            if text:
                lines.append((text, float(spans[0].get("size", 7.32))))
    return lines


def extract_brands_from_pdf(source: str | Path | bytes) -> list[str]:
    """Detect brand names from section headers in the FDL catalogue PDF."""
    if isinstance(source, bytes):
        doc = fitz.open(stream=source, filetype="pdf")
    else:
        doc = fitz.open(str(source))

    brands: set[str] = set()
    try:
        for page in doc:
            for text, size in _lines_with_size(page):
                if size >= HEADER_FONT_SIZE - 0.5:
                    for token in text.split():
                        upper = token.upper()
                        if upper in KNOWN_BRAND_TOKENS:
                            brands.add(normalize_brand_name(upper))
                    continue

                if SUBHEADER_MIN_SIZE <= size <= SUBHEADER_MAX_SIZE:
                    for token in re.findall(r"\b([A-Z]{2,})\b", text):
                        if token in KNOWN_BRAND_TOKENS:
                            brands.add(normalize_brand_name(token))
    finally:
        doc.close()

    return sorted(brands, key=str.lower)


async def get_or_create_brand(session: AsyncSession, name: str | None) -> Brand | None:
    if not name or not name.strip():
        return None

    normalized = normalize_brand_name(name)
    slug = brand_slug(normalized)
    if not slug:
        return None

    display_name = FALLBACK_COMMERCIAL_BRAND if slug == FALLBACK_BRAND_SLUG else normalized

    result = await session.execute(select(Brand).where(Brand.slug == slug))
    brand = result.scalar_one_or_none()
    if brand:
        if brand.name != display_name:
            brand.name = display_name
        return brand

    brand = Brand(name=display_name, slug=slug)
    session.add(brand)
    await session.flush()
    return brand


async def ensure_fallback_commercial_brand(session: AsyncSession) -> Brand:
    """Ensure canonical unbranded commercial brand exists (idempotent)."""
    result = await session.execute(select(Brand).where(Brand.slug == FALLBACK_BRAND_SLUG))
    brand = result.scalar_one_or_none()
    if brand:
        if brand.name != FALLBACK_COMMERCIAL_BRAND:
            brand.name = FALLBACK_COMMERCIAL_BRAND
        return brand

    brand = Brand(name=FALLBACK_COMMERCIAL_BRAND, slug=FALLBACK_BRAND_SLUG)
    session.add(brand)
    await session.flush()
    return brand


async def seed_brands(
    session: AsyncSession,
    brand_names: list[str],
) -> BrandSeedResult:
    result = BrandSeedResult()
    slugs: list[str] = []

    for raw_name in brand_names:
        normalized = normalize_brand_name(raw_name)
        slug = brand_slug(normalized)
        if not slug:
            continue

        existing = (
            await session.execute(select(Brand).where(Brand.slug == slug))
        ).scalar_one_or_none()
        if existing:
            if existing.name != normalized:
                existing.name = normalized
                result.updated += 1
            slugs.append(slug)
            continue

        session.add(Brand(name=normalized, slug=slug))
        result.created += 1
        slugs.append(slug)

    await session.commit()
    result.total = len(slugs)
    result.slugs = sorted(slugs)
    return result


async def seed_brands_from_pdf(session: AsyncSession, pdf_path: Path) -> BrandSeedResult:
    names = extract_brands_from_pdf(pdf_path)
    return await seed_brands(session, names)
