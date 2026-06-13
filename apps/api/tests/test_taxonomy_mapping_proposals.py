"""Tests for taxonomy mapping proposals."""

from __future__ import annotations

import pytest
from app.database import async_session
from app.services.canonical_taxonomy import build_canonical_category_tree, flatten_canonical_nodes
from app.services.seed_categories import seed_default_categories
from app.services.taxonomy_mapper import load_mapping_rules
from app.services.taxonomy_mapping_proposals import propose_mapping
from tests.taxonomy_test_utils import reset_taxonomy_rules_to_seed


@pytest.mark.integration
@pytest.mark.asyncio
async def test_existing_rule_proposal_for_cardio_remo(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await reset_taxonomy_rules_to_seed(session)
        rules = await load_mapping_rules(session)
        tree = await build_canonical_category_tree(session)
        flat = flatten_canonical_nodes(tree)
        slug_by_id = {n.id: n.slug for n in flat}

        proposal = propose_mapping("CARDIO > REMO", rules, tree, slug_by_id)

    assert proposal.proposal_source == "existing_rule"
    assert proposal.proposed_category_slug == "remos"
    assert proposal.proposal_confidence == 1.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crosstraining_proposal_uses_existing_section_path_rule(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await reset_taxonomy_rules_to_seed(session)
        rules = await load_mapping_rules(session)
        tree = await build_canonical_category_tree(session)
        flat = flatten_canonical_nodes(tree)
        slug_by_id = {n.id: n.slug for n in flat}

        proposal = propose_mapping(
            "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            rules,
            tree,
            slug_by_id,
        )

    assert proposal.proposal_source == "existing_rule"
    assert proposal.proposed_category_slug == "cross-training"
    assert proposal.requires_review is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_keyword_proposal_does_not_auto_apply_to_rows(integration_db):
    """Keyword proposals are suggestions only; unmapped rows stay unmapped without confirmed rule."""
    from decimal import Decimal

    from app.models import ImportBatch, ImportProfile, ImportRow, Supplier
    from sqlalchemy import select

    async with async_session() as session:
        await seed_default_categories(session)
        await reset_taxonomy_rules_to_seed(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()
        batch = ImportBatch(
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="test.pdf",
            parser_key="fdl_pdf_v1",
            parser_version="1",
            status="preview",
        )
        session.add(batch)
        await session.flush()
        row = ImportRow(
            batch_id=batch.id,
            source_row_index=0,
            raw_name="Product",
            normalized_name="Product",
            detected_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            sku="CRO110",
            price_amount=Decimal("10.00"),
            review_reasons=["unmapped_category"],
            review_status="needs_review",
        )
        session.add(row)
        await session.commit()

        rules = await load_mapping_rules(session)
        tree = await build_canonical_category_tree(session)
        flat = flatten_canonical_nodes(tree)
        slug_by_id = {n.id: n.slug for n in flat}
        assert row.detected_category_path_raw is not None
        proposal = propose_mapping(row.detected_category_path_raw, rules, tree, slug_by_id)

    assert proposal.proposal_source == "existing_rule"
    assert proposal.proposed_category_slug == "cross-training"
    assert row.mapped_category_slug is None
    assert "unmapped_category" in row.review_reasons
