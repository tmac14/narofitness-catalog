"""Integration: legacy PDF confirm path replaced by staged confirm."""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_legacy_direct_confirm_removed():
    pytest.skip("Direct ParsedRowSchema confirm removed; use tests/test_import_confirm_specs.py")
