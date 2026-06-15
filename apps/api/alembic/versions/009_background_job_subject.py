"""Add generic subject_type and subject_id to background_jobs.

Revision ID: 009_background_job_subject
Revises: 008_source_documents
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_background_job_subject"
down_revision: Union[str, None] = "008_source_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("background_jobs", sa.Column("subject_type", sa.String(length=64), nullable=True))
    op.add_column(
        "background_jobs",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_background_jobs_subject_type", "background_jobs", ["subject_type"])
    op.create_index("ix_background_jobs_subject_id", "background_jobs", ["subject_id"])
    op.create_index(
        "ix_background_jobs_subject_job_status",
        "background_jobs",
        ["subject_type", "subject_id", "job_type", "status"],
    )
    op.execute(
        """
        UPDATE background_jobs
        SET subject_type = 'catalog', subject_id = catalog_id
        WHERE catalog_id IS NOT NULL
          AND subject_type IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_background_jobs_subject_job_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_subject_id", table_name="background_jobs")
    op.drop_index("ix_background_jobs_subject_type", table_name="background_jobs")
    op.drop_column("background_jobs", "subject_id")
    op.drop_column("background_jobs", "subject_type")
