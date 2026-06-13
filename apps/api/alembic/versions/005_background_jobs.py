"""Add background_jobs table for async process queue (PRES-5A).

Revision ID: 005_background_jobs
Revises: 004_catalog_covers
Create Date: 2026-06-08
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_background_jobs"
down_revision: Union[str, None] = "004_catalog_covers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "background_jobs" in inspector.get_table_names():
        return

    op.create_table(
        "background_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.SmallInteger(), nullable=True),
        sa.Column("message", sa.String(length=512), nullable=True),
        sa.Column("result_path", sa.String(length=512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "catalog_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("catalogs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_background_jobs_status_created_at",
        "background_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_background_jobs_catalog_job_status",
        "background_jobs",
        ["catalog_id", "job_type", "status"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "background_jobs" not in inspector.get_table_names():
        return
    op.drop_index("ix_background_jobs_catalog_job_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_status_created_at", table_name="background_jobs")
    op.drop_table("background_jobs")
