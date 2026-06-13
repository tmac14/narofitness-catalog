"""Tests for commercial brand resolution."""

from __future__ import annotations

import pytest
from app.database import async_session
from app.models import Brand
from app.services.import_brand_resolution import (
    FALLBACK_BRAND_SLUG,
    FALLBACK_COMMERCIAL_BRAND,
    extract_explicit_commercial_brand,
    resolve_commercial_brand,
)
from app.services.seed_brands import ensure_fallback_commercial_brand
from sqlalchemy import select


def test_resolve_brand_from_family_header():
    result = resolve_commercial_brand(
        family_header_raw="Disco Bumper Negro NEXO - Goma Maciza Negro (casquillo de acero)",
    )
    assert result.brand == "NEXO"
    assert result.brand_source == "family_header"
    assert result.brand_confidence >= 0.9


def test_resolve_brand_fallback_sin_marca_without_evidence():
    result = resolve_commercial_brand(
        family_header_raw="Disco Bumper Negro 3.0 - Goma Maciza Negro (Casquillo de Acero)",
        variant_name_raw="Disco Bumper Negro 3.0 - 5 kgs",
    )
    assert result.brand == FALLBACK_COMMERCIAL_BRAND
    assert result.brand_source == "fallback_unbranded"
    assert result.brand_confidence == 0.0


def test_resolve_brand_section_fdl_only_is_sin_marca():
    result = resolve_commercial_brand(section_brand="FDL")
    assert result.brand == FALLBACK_COMMERCIAL_BRAND
    assert result.brand_source == "fallback_unbranded"


def test_resolve_brand_fdl_from_family_header():
    result = resolve_commercial_brand(
        family_header_raw="Wall Balls Doble Costura Negro FDL",
    )
    assert result.brand == "FDL"
    assert result.brand_source == "family_header"


def test_resolve_brand_nexo_from_family_header():
    result = resolve_commercial_brand(
        family_header_raw="Wall Balls Doble Costura Negro NEXO",
    )
    assert result.brand == "NEXO"
    assert result.brand_source == "family_header"


def test_extract_explicit_commercial_brand_word_boundary():
    assert extract_explicit_commercial_brand("Wall Ball 3 kgs Negro FDL") == "FDL"
    assert extract_explicit_commercial_brand("DOBNEXO05N") is None
    assert extract_explicit_commercial_brand("Disco Olimpico Premium 5 kgs") is None


def test_resolve_brand_never_uses_fdl_as_commercial():
    """Legacy name: section-only FDL must not become product brand."""
    result = resolve_commercial_brand(section_brand="FDL")
    assert result.brand == FALLBACK_COMMERCIAL_BRAND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ensure_single_sin_marca_brand(integration_db):
    async with async_session() as session:
        first = await ensure_fallback_commercial_brand(session)
        second = await ensure_fallback_commercial_brand(session)
        brands = (
            (await session.execute(select(Brand).where(Brand.slug == FALLBACK_BRAND_SLUG)))
            .scalars()
            .all()
        )

    assert first.slug == FALLBACK_BRAND_SLUG
    assert second.id == first.id
    assert len(brands) == 1
    assert brands[0].name == FALLBACK_COMMERCIAL_BRAND
