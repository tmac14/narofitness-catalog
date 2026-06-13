from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, get_db
from app.models import ImportProfile
from app.schemas import ImportConfirmRequest, ImportConfirmResponse, ImportPreviewResponse
from app.services.import_confirm import confirm_import
from app.services.import_pipeline import run_preview_pipeline

router = APIRouter(prefix="/import/pdf", tags=["import"])


async def _get_profile(
    db: AsyncSession, supplier_id: UUID, import_profile_id: UUID
) -> ImportProfile:
    profile = await db.get(ImportProfile, import_profile_id)
    if not profile or profile.supplier_id != supplier_id:
        raise HTTPException(404, "Import profile not found for this supplier")
    if not profile.is_active:
        raise HTTPException(400, "Import profile is inactive")
    return profile


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_pdf(
    supplier_id: UUID = Form(...),
    import_profile_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImportPreviewResponse:
    profile = await _get_profile(db, supplier_id, import_profile_id)
    content = await file.read()
    batch, rows, stats, action_stats = await run_preview_pipeline(
        db,
        content=content,
        profile=profile,
        supplier_id=supplier_id,
        filename=file.filename or "upload.pdf",
    )

    return ImportPreviewResponse(
        batch_id=batch.id,
        filename=file.filename or "upload.pdf",
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
        total_rows=len(rows),
        stats=stats,
        action_stats=action_stats,
        rows=rows,
    )


@router.post("/confirm", response_model=ImportConfirmResponse, status_code=201)
async def confirm_pdf(body: ImportConfirmRequest) -> ImportConfirmResponse:
    async with async_session() as session:
        profile = await _get_profile(session, body.supplier_id, body.import_profile_id)
        result = await confirm_import(
            session,
            batch_id=body.batch_id,
            row_ids=body.row_ids,
            profile=profile,
            effective_date=body.effective_date,
            allow_needs_review=body.allow_needs_review,
        )
    return ImportConfirmResponse(
        price_list_id=result.price_list.id,
        batch_id=body.batch_id,
        masters_created=result.masters_created,
        variants_created=result.variants_created,
        variants_updated=result.variants_updated,
        entries_created=result.entries_created,
        rows_skipped=result.rows_skipped,
        rows_blocked=result.rows_blocked,
    )
