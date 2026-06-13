"""Tests for enriched canonical category tree."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.database import async_session
from app.services.canonical_taxonomy import build_canonical_category_tree, flatten_canonical_nodes
from app.services.seed_categories import seed_default_categories

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_canonical_tree_has_full_path_and_level(integration_db):
    expected = json.loads(
        (FIXTURES / "canonical_category_tree_sample.json").read_text(encoding="utf-8")
    )

    async with async_session() as session:
        await seed_default_categories(session)
        tree = await build_canonical_category_tree(session)

    flat = flatten_canonical_nodes(tree)
    by_slug = {node.slug: node for node in flat}

    for root in expected["expected_roots"]:
        node = by_slug[root["slug"]]
        assert node.level == root["level"]
        assert node.full_path == node.name

    for sub in expected["expected_subcategories"]:
        node = by_slug[sub["slug"]]
        parent = by_slug[sub["parent_slug"]]
        assert node.level == sub["level"]
        assert node.full_path == f"{parent.name} > {node.name}"
        assert node.parent_id == parent.id
