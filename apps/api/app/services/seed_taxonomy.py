"""Seed default categories and PDF-derived brands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database import async_session
from app.services.seed_brands import BrandSeedResult, seed_brands_from_pdf
from app.services.seed_categories import CategorySeedResult, seed_default_categories
from app.services.seed_paths import resolve_pdf_path


@dataclass
class TaxonomySeedResult:
    exit_code: int
    categories: CategorySeedResult | None = None
    brands: BrandSeedResult | None = None


async def run_taxonomy_seed(
    pdf_path: Path | None = None,
    *,
    skip_categories: bool = False,
    skip_brands: bool = False,
) -> TaxonomySeedResult:
    resolved_pdf = resolve_pdf_path(pdf_path)

    async with async_session() as session:
        categories_result = None
        brands_result = None

        if not skip_categories:
            categories_result = await seed_default_categories(session)

        if not skip_brands:
            if not resolved_pdf.is_file():
                return TaxonomySeedResult(exit_code=1)
            brands_result = await seed_brands_from_pdf(session, resolved_pdf)

    return TaxonomySeedResult(
        exit_code=0,
        categories=categories_result,
        brands=brands_result,
    )
