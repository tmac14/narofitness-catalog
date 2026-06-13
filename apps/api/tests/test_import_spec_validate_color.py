"""Preview validation for unknown color enum (COLOR-1d)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services.import_spec_validate import validate_parsed_specs


@pytest.mark.asyncio
async def test_validate_parsed_specs_adds_unknown_color_warning(integration_db):
    from app.database import async_session
    from app.services.seed_spec_definitions import seed_spec_definitions

    async with async_session() as session:
        await seed_spec_definitions(session)
        row = SimpleNamespace(
            parsed_common_specs_raw={},
            parsed_variant_specs_raw={"color": "Azul Petróleo", "peso_kg": 5},
            review_reasons=[],
            review_status="pending",
        )
        errors = await validate_parsed_specs(session, row)
        assert errors == []
        assert "unknown_color_value:Azul Petróleo" in row.review_reasons
        assert "unknown_spec_key" not in row.review_reasons
