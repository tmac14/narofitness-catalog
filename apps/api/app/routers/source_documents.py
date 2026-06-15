from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ImportProfile
from app.schemas import (
    CatalogAdaptationCreateRequest,
    CatalogAdaptationProjectOut,
    DocumentAnalysisSnapshotOut,
    ImportPreviewResponse,
    JobOut,
    SourceDocumentCapabilitiesOut,
    SourceDocumentOut,
)
from app.services.background_jobs import create_job, find_active_subject_job, get_job
from app.services.job_constants import (
    JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
    SUBJECT_TYPE_SOURCE_DOCUMENT,
)
from app.services.job_presenter import job_to_out
from app.services.import_pipeline import run_preview_pipeline
from app.services.catalog_adaptations import (
    AdaptationProfileNotSupportedError,
    create_adaptation_project,
)
from app.services.source_document_analysis import get_latest_snapshot
from app.services.source_documents import (
    SourceDocumentValidationError,
    create_or_get_source_document,
    get_source_document_by_id,
    read_source_document_bytes,
    sanitize_original_filename,
    source_document_capabilities,
)

router = APIRouter(prefix="/source-documents", tags=["source-documents"])


async def _get_import_profile(
    db: AsyncSession, supplier_id: UUID, import_profile_id: UUID
) -> ImportProfile:
    profile = await db.get(ImportProfile, import_profile_id)
    if not profile or profile.supplier_id != supplier_id:
        raise HTTPException(404, "Import profile not found for this supplier")
    if not profile.is_active:
        raise HTTPException(400, "Import profile is inactive")
    return profile


def _to_out(doc) -> SourceDocumentOut:
    return SourceDocumentOut(
        id=doc.id,
        sha256=doc.sha256,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        byte_size=doc.byte_size,
        page_count=doc.page_count,
        validation_status=doc.validation_status,
        validation_error=doc.validation_error,
        created_at=doc.created_at,
        created_by=doc.created_by,
    )


@router.post("", response_model=SourceDocumentOut, status_code=201)
async def upload_source_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> SourceDocumentOut:
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(400, "Only application/pdf uploads are supported")
    content = await file.read()
    try:
        doc, _created = await create_or_get_source_document(
            db,
            content=content,
            original_filename=sanitize_original_filename(file.filename),
        )
    except SourceDocumentValidationError as exc:
        raise HTTPException(400, str(exc)) from exc

    return _to_out(doc)


@router.get("/{source_document_id}", response_model=SourceDocumentOut)
async def get_source_document(
    source_document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceDocumentOut:
    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    return _to_out(doc)


@router.get("/{source_document_id}/capabilities", response_model=SourceDocumentCapabilitiesOut)
async def get_source_document_capabilities(
    source_document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceDocumentCapabilitiesOut:
    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    snapshot = await get_latest_snapshot(db, source_document_id)
    payload = source_document_capabilities(doc, snapshot)
    return SourceDocumentCapabilitiesOut.model_validate(payload)


@router.post(
    "/{source_document_id}/analysis-jobs",
    status_code=202,
    response_model=JobOut,
)
async def create_source_document_analysis_job(
    source_document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    if doc.validation_status != "valid":
        raise HTTPException(400, "Source document is not valid")

    active = await find_active_subject_job(
        db,
        subject_type=SUBJECT_TYPE_SOURCE_DOCUMENT,
        subject_id=source_document_id,
        job_type=JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
    )
    if active is not None:
        raise HTTPException(409, "An analysis job is already active for this source document")

    job = await create_job(
        db,
        job_type=JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
        subject_type=SUBJECT_TYPE_SOURCE_DOCUMENT,
        subject_id=source_document_id,
        progress_percent=0,
        message="Análisis en cola",
        metadata={"source_sha256": doc.sha256},
    )
    await db.commit()
    loaded = await get_job(db, job.id)
    assert loaded is not None
    return job_to_out(loaded)


@router.post(
    "/{source_document_id}/adaptations",
    status_code=201,
    response_model=CatalogAdaptationProjectOut,
)
async def create_catalog_adaptation_from_source(
    source_document_id: UUID,
    body: CatalogAdaptationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> CatalogAdaptationProjectOut:
    from app.services.catalog_adaptation_presenter import project_to_out

    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    if doc.validation_status != "valid":
        raise HTTPException(400, "Source document is not valid")
    try:
        project = await create_adaptation_project(
            db,
            source_document_id=source_document_id,
            name=body.name,
        )
    except AdaptationProfileNotSupportedError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    return project_to_out(project)


@router.post("/{source_document_id}/import-preview", response_model=ImportPreviewResponse)
async def preview_import_from_source_document(
    source_document_id: UUID,
    supplier_id: UUID = Form(...),
    import_profile_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
) -> ImportPreviewResponse:
    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    if doc.validation_status != "valid":
        raise HTTPException(400, "Source document is not valid")

    profile = await _get_import_profile(db, supplier_id, import_profile_id)
    try:
        content = read_source_document_bytes(doc)
    except SourceDocumentValidationError as exc:
        raise HTTPException(400, str(exc)) from exc

    snapshot = await get_latest_snapshot(db, source_document_id)
    snapshot_id = snapshot.id if snapshot is not None else None

    batch, rows, stats, action_stats = await run_preview_pipeline(
        db,
        content=content,
        profile=profile,
        supplier_id=supplier_id,
        filename=doc.original_filename,
        source_document_id=source_document_id,
        analysis_snapshot_id=snapshot_id,
    )

    return ImportPreviewResponse(
        batch_id=batch.id,
        filename=doc.original_filename,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
        source_document_id=source_document_id,
        analysis_snapshot_id=snapshot_id,
        total_rows=len(rows),
        stats=stats,
        action_stats=action_stats,
        rows=rows,
    )


@router.get(
    "/{source_document_id}/analysis-snapshots/latest",
    response_model=DocumentAnalysisSnapshotOut,
)
async def get_latest_analysis_snapshot(
    source_document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentAnalysisSnapshotOut:
    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    snapshot = await get_latest_snapshot(db, source_document_id)
    if snapshot is None:
        raise HTTPException(404, "No analysis snapshot for this source document")
    return DocumentAnalysisSnapshotOut(
        id=snapshot.id,
        source_document_id=snapshot.source_document_id,
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        analyzer_key=snapshot.analyzer_key,
        analyzer_version=snapshot.analyzer_version,
        profile_key=snapshot.profile_key,
        profile_version=snapshot.profile_version,
        profile_match_status=snapshot.profile_match_status,
        created_at=snapshot.created_at,
        snapshot=snapshot.snapshot_json,
    )


@router.get("/{source_document_id}/download")
async def download_source_document(
    source_document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    doc = await get_source_document_by_id(db, source_document_id)
    if not doc:
        raise HTTPException(404, "Source document not found")
    try:
        content = read_source_document_bytes(doc)
    except SourceDocumentValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.original_filename}"',
            "X-Source-Sha256": doc.sha256,
        },
    )
