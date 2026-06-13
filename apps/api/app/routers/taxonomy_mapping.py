"""Source taxonomy discovery and mapping review API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ImportBatch, TaxonomyMappingRule
from app.schemas import (
    CanonicalCategoryNodeOut,
    RemapTaxonomyResponse,
    SourceCategoryDiscoveryOut,
    SourceCategoryDiscoveryResponse,
    SourceCategoryExampleRowOut,
    TaxonomyMappingConfirmRequest,
    TaxonomyMappingIgnoreRequest,
    TaxonomyMappingRuleOut,
)
from app.services.canonical_taxonomy import CanonicalCategoryNode, build_canonical_category_tree
from app.services.source_taxonomy import SourceCategoryDiscovery, discover_source_categories
from app.services.taxonomy_batch_remap import remap_batch_taxonomy
from app.services.taxonomy_mapping_confirm import (
    confirm_source_category_mapping,
    ignore_source_category,
)

router = APIRouter(tags=["taxonomy-mapping"])


def _canonical_node_to_out(node: CanonicalCategoryNode) -> CanonicalCategoryNodeOut:
    return CanonicalCategoryNodeOut(
        id=node.id,
        name=node.name,
        slug=node.slug,
        parent_id=node.parent_id,
        full_path=node.full_path,
        level=node.level,
        children=[_canonical_node_to_out(child) for child in node.children],
    )


def _discovery_to_out(item: SourceCategoryDiscovery) -> SourceCategoryDiscoveryOut:
    return SourceCategoryDiscoveryOut(
        source_category_path_raw=item.source_category_path_raw,
        normalized_source_category_key=item.normalized_source_category_key,
        row_count=item.row_count,
        example_rows=[
            SourceCategoryExampleRowOut(
                sku=example.sku,
                normalized_name=example.normalized_name,
                source_row_index=example.source_row_index,
            )
            for example in item.example_rows
        ],
        currently_mapped_category_id=item.currently_mapped_category_id,
        currently_mapped_category_slug=item.currently_mapped_category_slug,
        mapped_category_confidence=item.mapped_category_confidence,
        mapping_rule_id=item.mapping_rule_id,
        mapping_status=item.mapping_status,
        requires_review=item.requires_review,
        notes=item.notes,
        proposed_category_id=item.proposed_category_id,
        proposed_category_slug=item.proposed_category_slug,
        proposal_confidence=item.proposal_confidence,
        proposal_reason=item.proposal_reason,
        proposal_source=item.proposal_source,
    )


async def _get_batch_or_404(db: AsyncSession, batch_id: UUID) -> ImportBatch:
    batch = await db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Import batch not found")
    return batch


@router.get("/categories/canonical-tree", response_model=list[CanonicalCategoryNodeOut])
async def get_canonical_category_tree(
    db: AsyncSession = Depends(get_db),
) -> list[CanonicalCategoryNodeOut]:
    tree = await build_canonical_category_tree(db)
    return [_canonical_node_to_out(node) for node in tree]


@router.get(
    "/import/batches/{batch_id}/source-categories", response_model=SourceCategoryDiscoveryResponse
)
async def get_batch_source_categories(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceCategoryDiscoveryResponse:
    batch = await _get_batch_or_404(db, batch_id)
    discoveries = await discover_source_categories(
        db,
        batch_id,
        supplier_id=batch.supplier_id,
        import_profile_id=batch.import_profile_id,
    )
    return SourceCategoryDiscoveryResponse(
        batch_id=batch_id,
        supplier_id=batch.supplier_id,
        import_profile_id=batch.import_profile_id,
        source_categories=[_discovery_to_out(item) for item in discoveries],
    )


@router.post("/taxonomy-mapping-rules/confirm", response_model=TaxonomyMappingRuleOut)
async def confirm_taxonomy_mapping(
    body: TaxonomyMappingConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> TaxonomyMappingRuleOut:
    result = await confirm_source_category_mapping(
        db,
        supplier_id=body.supplier_id,
        import_profile_id=body.import_profile_id,
        source_category_path_raw=body.source_category_path_raw,
        normalized_source_category_key=body.normalized_source_category_key,
        target_category_id=body.target_category_id,
        confidence=body.confidence,
        requires_review=body.requires_review,
        priority=body.priority,
        notes=body.notes,
    )
    rule = await db.get(TaxonomyMappingRule, result.rule_id)
    if not rule:
        raise HTTPException(500, "Failed to load confirmed mapping rule")
    return TaxonomyMappingRuleOut(
        id=rule.id,
        match_type=rule.match_type,
        match_value=rule.match_value,
        supplier_id=rule.supplier_id,
        import_profile_id=rule.import_profile_id,
        target_category_id=rule.target_category_id,
        target_subcategory_id=rule.target_subcategory_id,
        confidence=float(rule.confidence),
        requires_review=rule.requires_review,
        priority=rule.priority,
        notes=rule.notes,
        is_active=rule.is_active,
    )


@router.post("/taxonomy-mapping-rules/ignore", response_model=TaxonomyMappingRuleOut)
async def ignore_taxonomy_mapping(
    body: TaxonomyMappingIgnoreRequest,
    db: AsyncSession = Depends(get_db),
) -> TaxonomyMappingRuleOut:
    result = await ignore_source_category(
        db,
        supplier_id=body.supplier_id,
        import_profile_id=body.import_profile_id,
        source_category_path_raw=body.source_category_path_raw,
        normalized_source_category_key=body.normalized_source_category_key,
        notes=body.notes,
        priority=body.priority,
    )
    rule = await db.get(TaxonomyMappingRule, result.rule_id)
    if not rule:
        raise HTTPException(500, "Failed to load ignored mapping rule")
    return TaxonomyMappingRuleOut(
        id=rule.id,
        match_type=rule.match_type,
        match_value=rule.match_value,
        supplier_id=rule.supplier_id,
        import_profile_id=rule.import_profile_id,
        target_category_id=rule.target_category_id,
        target_subcategory_id=rule.target_subcategory_id,
        confidence=float(rule.confidence),
        requires_review=rule.requires_review,
        priority=rule.priority,
        notes=rule.notes,
        is_active=rule.is_active,
    )


@router.post("/import/batches/{batch_id}/remap-taxonomy", response_model=RemapTaxonomyResponse)
async def remap_batch_taxonomy_endpoint(
    batch_id: UUID,
    include_rows: bool = Query(default=True),
    row_limit: int = Query(default=500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
) -> RemapTaxonomyResponse:
    await _get_batch_or_404(db, batch_id)
    result = await remap_batch_taxonomy(
        db,
        batch_id,
        include_rows=include_rows,
        row_limit=row_limit,
    )
    return RemapTaxonomyResponse(
        batch_id=batch_id,
        rows_updated=result.rows_updated,
        mapped_count=result.mapped_count,
        unmapped_count=result.unmapped_count,
        ignored_count=result.ignored_count,
        rows=result.rows,
    )
