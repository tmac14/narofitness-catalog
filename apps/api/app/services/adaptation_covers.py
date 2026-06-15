"""Cover slot resolution and recipe updates for adaptation projects."""

from __future__ import annotations

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import CatalogAdaptationRecipeVersion, DocumentAnalysisSnapshot
from app.services.adaptation_cover_storage import (
    AdaptationCoverStorageError,
    copy_library_image_to_adaptation_cover,
    save_adaptation_cover_upload,
)
from app.services.adaptation_recipe import recipe_fingerprint
from app.services.catalog_adaptations import get_adaptation_project_by_id
from app.services.direct_adaptation.cover_plan import _asset_status
from app.services.media import media_url
from app.services.source_document_cover_pages import cover_slots_from_detection


class AdaptationCoverSlotError(ValueError):
    pass


def _find_slot_in_covers(covers: dict, slot_id: str) -> tuple[str, dict]:
    main = covers.get("main") if isinstance(covers.get("main"), dict) else {}
    if str(main.get("slot_id", "main")) == slot_id or slot_id == "main":
        return "main", main
    for index, section in enumerate(covers.get("sections") or []):
        if not isinstance(section, dict):
            continue
        if str(section.get("slot_id")) == slot_id:
            return f"sections.{index}", section
    raise AdaptationCoverSlotError(f"Unknown cover slot: {slot_id}")


async def get_adaptation_cover_slots(db: AsyncSession, project_id: UUID) -> dict:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise ValueError("Catalog adaptation project not found")
    if project.active_recipe_version_id is None:
        raise AdaptationCoverSlotError("Project has no active recipe version")
    recipe = await db.get(CatalogAdaptationRecipeVersion, project.active_recipe_version_id)
    if recipe is None:
        raise AdaptationCoverSlotError("Active recipe version not found")
    snapshot = None
    if project.analysis_snapshot_id is not None:
        snapshot = await db.get(DocumentAnalysisSnapshot, project.analysis_snapshot_id)

    detection = (snapshot.snapshot_json or {}).get("cover_pages") if snapshot else {}
    covers = recipe.recipe_json.get("covers") or {}
    slots = cover_slots_from_detection(detection or {}, assigned_covers=covers)
    for slot in slots:
        asset_path = slot.get("asset_path")
        slot["asset_url"] = media_url(str(asset_path)) if asset_path else None
        slot["asset_status"] = _asset_status(asset_path)

    main = detection.get("main") if isinstance(detection, dict) else {}
    return {
        "project_id": str(project.id),
        "page_offset": int((detection or {}).get("page_offset") or covers.get("page_offset") or 0),
        "prepend_main_cover": bool((main or {}).get("prepend_page") or (covers.get("main") or {}).get("prepend_page")),
        "detection_method": (detection or {}).get("method"),
        "slots": slots,
    }


async def _persist_cover_assignment(
    db: AsyncSession,
    *,
    project_id: UUID,
    slot_id: str,
    asset_path: str,
    asset_sha256: str,
) -> dict:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise ValueError("Catalog adaptation project not found")
    if project.status not in {"draft", "qa_required", "approved"}:
        raise AdaptationCoverSlotError("Cover assignment not allowed in current project status")
    if project.active_recipe_version_id is None:
        raise AdaptationCoverSlotError("Project has no active recipe version")
    recipe = await db.get(CatalogAdaptationRecipeVersion, project.active_recipe_version_id)
    if recipe is None:
        raise AdaptationCoverSlotError("Active recipe version not found")

    recipe_json = dict(recipe.recipe_json or {})
    covers = dict(recipe_json.get("covers") or {})
    target_key, target = _find_slot_in_covers(covers, slot_id)
    target = dict(target)
    target["asset_path"] = asset_path
    target["asset_sha256"] = asset_sha256
    if target_key == "main":
        covers["main"] = target
    else:
        index = int(target_key.split(".")[1])
        sections = list(covers.get("sections") or [])
        sections[index] = target
        covers["sections"] = sections
    recipe_json["covers"] = covers
    recipe.recipe_json = recipe_json
    recipe.recipe_fingerprint = recipe_fingerprint(recipe_json)
    await db.flush()
    return await get_adaptation_cover_slots(db, project_id)


async def upload_adaptation_cover_slot(
    db: AsyncSession,
    *,
    project_id: UUID,
    slot_id: str,
    upload: UploadFile,
) -> dict:
    try:
        rel, digest, _url = save_adaptation_cover_upload(project_id, slot_id=slot_id, upload=upload)
    except AdaptationCoverStorageError as exc:
        raise AdaptationCoverSlotError(str(exc)) from exc
    return await _persist_cover_assignment(
        db,
        project_id=project_id,
        slot_id=slot_id,
        asset_path=rel,
        asset_sha256=digest,
    )


async def assign_adaptation_cover_from_library(
    db: AsyncSession,
    *,
    project_id: UUID,
    slot_id: str,
    library_relative_path: str,
) -> dict:
    try:
        rel, digest, _url = copy_library_image_to_adaptation_cover(
            project_id,
            slot_id=slot_id,
            library_relative_path=library_relative_path,
        )
    except AdaptationCoverStorageError as exc:
        raise AdaptationCoverSlotError(str(exc)) from exc
    return await _persist_cover_assignment(
        db,
        project_id=project_id,
        slot_id=slot_id,
        asset_path=rel,
        asset_sha256=digest,
    )
