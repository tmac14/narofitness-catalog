"""Tests for generic background job subject fields (SOURCE-CATALOG Phase 1B)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.database import async_session
from app.models import Catalog
from app.services.background_jobs import create_job, list_jobs
from app.services.job_constants import (
    JOB_TYPE_CATALOG_EXPORT_PDF,
    JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
    SUBJECT_TYPE_CATALOG,
    SUBJECT_TYPE_SOURCE_DOCUMENT,
)


@pytest.mark.integration
async def test_create_job_sets_catalog_subject_from_catalog_id(integration_db):
    async with async_session() as db:
        catalog = Catalog(name=f"Subject test {uuid4().hex[:8]}")
        db.add(catalog)
        await db.flush()
        job = await create_job(
            db,
            job_type=JOB_TYPE_CATALOG_EXPORT_PDF,
            catalog_id=catalog.id,
            message="export",
        )
        await db.commit()
        assert job.catalog_id == catalog.id
        assert job.subject_type == SUBJECT_TYPE_CATALOG
        assert job.subject_id == catalog.id


@pytest.mark.integration
async def test_create_job_accepts_source_document_subject(integration_db):
    source_id = uuid4()
    async with async_session() as db:
        job = await create_job(
            db,
            job_type=JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
            subject_type=SUBJECT_TYPE_SOURCE_DOCUMENT,
            subject_id=source_id,
            message="analyze",
        )
        await db.commit()
        assert job.catalog_id is None
        assert job.subject_type == SUBJECT_TYPE_SOURCE_DOCUMENT
        assert job.subject_id == source_id


@pytest.mark.integration
async def test_list_jobs_filters_by_subject(integration_db):
    source_id = uuid4()
    other_id = uuid4()
    async with async_session() as db:
        await create_job(
            db,
            job_type=JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
            subject_type=SUBJECT_TYPE_SOURCE_DOCUMENT,
            subject_id=source_id,
        )
        await create_job(
            db,
            job_type=JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
            subject_type=SUBJECT_TYPE_SOURCE_DOCUMENT,
            subject_id=other_id,
        )
        await db.commit()

    async with async_session() as db:
        matches = await list_jobs(
            db,
            subject_type=SUBJECT_TYPE_SOURCE_DOCUMENT,
            subject_id=source_id,
            limit=10,
        )
    assert len(matches) == 1
    assert matches[0].subject_id == source_id


def test_migration_009_background_job_subject_revision():
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "009_background_job_subject.py"
    )
    namespace: dict = {}
    exec(path.read_text(encoding="utf-8"), namespace)
    assert namespace["revision"] == "009_background_job_subject"
    assert namespace["down_revision"] == "008_source_documents"
