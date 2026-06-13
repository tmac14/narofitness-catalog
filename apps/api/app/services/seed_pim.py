"""Orchestrator for PIM reference data seeding."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.seed_brands import ensure_fallback_commercial_brand, seed_brands_from_pdf
from app.services.seed_categories import seed_default_categories
from app.services.seed_category_spec_profiles import seed_category_spec_profiles
from app.services.seed_paths import resolve_pdf_path
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules


async def seed_pim(
    session: AsyncSession,
    *,
    pdf_path: Path | None = None,
    skip_categories: bool = False,
    skip_brands: bool = False,
    skip_spec_definitions: bool = False,
    skip_category_spec_profiles: bool = False,
    skip_taxonomy_mapping_rules: bool = False,
) -> dict[str, Any]:
    """Seed categories, brands, specs, profiles, and taxonomy rules. Returns a summary dict."""
    summary: dict[str, Any] = {"exit_code": 0}

    if not skip_categories:
        categories_result = await seed_default_categories(session)
        summary["categories"] = asdict(categories_result)
    else:
        summary["categories"] = None

    if not skip_brands:
        resolved_pdf = resolve_pdf_path(pdf_path)
        if not resolved_pdf.is_file():
            summary["exit_code"] = 1
            summary["brands"] = None
            summary["error"] = f"PDF not found: {resolved_pdf}"
            return summary
        brands_result = await seed_brands_from_pdf(session, resolved_pdf)
        summary["brands"] = asdict(brands_result)
    else:
        summary["brands"] = None

    await ensure_fallback_commercial_brand(session)

    if not skip_spec_definitions:
        spec_result = await seed_spec_definitions(session)
        summary["spec_definitions"] = asdict(spec_result)
    else:
        summary["spec_definitions"] = None

    if not skip_category_spec_profiles:
        profiles_result = await seed_category_spec_profiles(session)
        summary["category_spec_profiles"] = asdict(profiles_result)
    else:
        summary["category_spec_profiles"] = None

    if not skip_taxonomy_mapping_rules:
        rules_result = await seed_taxonomy_mapping_rules(session)
        summary["taxonomy_mapping_rules"] = asdict(rules_result)
    else:
        summary["taxonomy_mapping_rules"] = None

    return summary


async def run_pim_seed(
    pdf_path: Path | None = None,
    *,
    skip_categories: bool = False,
    skip_brands: bool = False,
) -> dict[str, Any]:
    """Convenience entry point using a fresh async session from app.database."""
    from app.database import async_session

    async with async_session() as session:
        return await seed_pim(
            session,
            pdf_path=pdf_path,
            skip_categories=skip_categories,
            skip_brands=skip_brands,
        )
