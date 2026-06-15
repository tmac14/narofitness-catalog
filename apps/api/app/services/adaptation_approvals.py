"""Catalog adaptation approval workflow."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CatalogAdaptationApproval, CatalogAdaptationExport, CatalogAdaptationProject
from app.services.direct_adaptation.output_delivery import DELIVERY_EPHEMERAL, DELIVERY_PERSIST


class AdaptationApprovalRequiredError(ValueError):
    pass


class AdaptationApprovalInvalidError(ValueError):
    pass


async def get_project_approval(
    db: AsyncSession, project_id: UUID
) -> CatalogAdaptationApproval | None:
    result = await db.execute(
        select(CatalogAdaptationApproval).where(CatalogAdaptationApproval.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def require_project_approved(db: AsyncSession, project_id: UUID) -> CatalogAdaptationApproval:
    approval = await get_project_approval(db, project_id)
    if approval is None:
        raise AdaptationApprovalRequiredError("Project must be approved before final export")
    return approval


async def create_project_approval(
    db: AsyncSession,
    *,
    project_id: UUID,
    export_id: UUID,
    approved_by: str | None = None,
    approval_note: str | None = None,
) -> CatalogAdaptationApproval:
    project = await db.get(CatalogAdaptationProject, project_id)
    if project is None:
        raise ValueError("Catalog adaptation project not found")
    if project.active_recipe_version_id is None:
        raise AdaptationApprovalInvalidError("Project has no active recipe version")

    export_row = await db.get(CatalogAdaptationExport, export_id)
    if export_row is None or export_row.project_id != project_id:
        raise AdaptationApprovalInvalidError("Export not found for this project")
    if export_row.export_kind != "preview":
        raise AdaptationApprovalInvalidError("Only preview exports can be approved")
    if export_row.delivery_mode != DELIVERY_PERSIST:
        raise AdaptationApprovalInvalidError("Ephemeral previews cannot be approved; rerun with persist delivery")
    if export_row.recipe_version_id != project.active_recipe_version_id:
        raise AdaptationApprovalInvalidError("Export recipe version does not match active recipe")

    manifest = export_row.manifest_json or {}
    renderer_version = str(manifest.get("renderer_version") or "")

    existing = await get_project_approval(db, project_id)
    if existing is not None:
        await db.delete(existing)
        await db.flush()

    approval = CatalogAdaptationApproval(
        project_id=project_id,
        recipe_version_id=export_row.recipe_version_id,
        export_id=export_row.id,
        manifest_fingerprint=export_row.manifest_fingerprint,
        output_profile=export_row.output_profile,
        renderer_version=renderer_version,
        approved_by=approved_by,
        approval_note=approval_note,
    )
    db.add(approval)
    project.status = "approved"
    await db.flush()
    return approval
