"""Cleanup expired ephemeral adaptation export artifacts."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session
from app.models import CatalogAdaptationExport
from app.services.adaptation_export_storage import delete_artifact_files
from app.services.direct_adaptation.output_delivery import DELIVERY_EPHEMERAL

logger = logging.getLogger(__name__)


async def cleanup_expired_ephemeral_exports() -> int:
    now = datetime.now(timezone.utc)
    removed = 0
    async with async_session() as db:
        result = await db.execute(
            select(CatalogAdaptationExport).where(
                CatalogAdaptationExport.delivery_mode == DELIVERY_EPHEMERAL,
                CatalogAdaptationExport.expires_at.is_not(None),
                CatalogAdaptationExport.expires_at < now,
            )
        )
        rows = list(result.scalars().all())
        for row in rows:
            delete_artifact_files(
                artifact_path=row.artifact_path,
                pdf_artifact_path=row.pdf_artifact_path,
            )
            await db.delete(row)
            removed += 1
            logger.info(
                "artifact_expired project_id=%s export_id=%s profile=%s",
                row.project_id,
                row.id,
                row.output_profile,
            )
        if removed:
            await db.commit()
    return removed
