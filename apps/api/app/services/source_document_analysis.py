"""Persist and query immutable document analysis snapshots."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import DocumentAnalysisSnapshot, SourceDocument
from app.services.source_document_analyzer import (
    ANALYZER_KEY,
    ANALYZER_VERSION,
    analyzer_config_fingerprint,
    build_analysis_snapshot,
)
from app.services.source_documents import read_source_document_bytes


async def get_latest_snapshot(
    db: AsyncSession, source_document_id: UUID
) -> DocumentAnalysisSnapshot | None:
    result = await db.execute(
        select(DocumentAnalysisSnapshot)
        .where(DocumentAnalysisSnapshot.source_document_id == source_document_id)
        .order_by(DocumentAnalysisSnapshot.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_snapshot_by_analyzer_contract(
    db: AsyncSession, source_document_id: UUID
) -> DocumentAnalysisSnapshot | None:
    fingerprint = analyzer_config_fingerprint()
    result = await db.execute(
        select(DocumentAnalysisSnapshot).where(
            DocumentAnalysisSnapshot.source_document_id == source_document_id,
            DocumentAnalysisSnapshot.analyzer_key == ANALYZER_KEY,
            DocumentAnalysisSnapshot.analyzer_version == ANALYZER_VERSION,
            DocumentAnalysisSnapshot.config_fingerprint == fingerprint,
        )
    )
    return result.scalar_one_or_none()


async def analyze_source_document(
    db: AsyncSession, source: SourceDocument
) -> DocumentAnalysisSnapshot:
    existing = await get_snapshot_by_analyzer_contract(db, source.id)
    if existing is not None:
        return existing

    pdf_bytes = read_source_document_bytes(source)
    snapshot_json = build_analysis_snapshot(source, pdf_bytes)
    profile = snapshot_json["profile"]
    record = DocumentAnalysisSnapshot(
        source_document_id=source.id,
        snapshot_fingerprint=snapshot_json["snapshot_fingerprint"],
        analyzer_key=ANALYZER_KEY,
        analyzer_version=ANALYZER_VERSION,
        config_fingerprint=analyzer_config_fingerprint(),
        profile_key=profile["key"],
        profile_version=profile["version"],
        profile_match_status=profile["match_status"],
        snapshot_json=snapshot_json,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record
