"""Add document_analysis_snapshots for immutable source analysis.

Revision ID: 010_document_analysis_snapshots
Revises: 009_background_job_subject
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_document_analysis_snapshots"
down_revision: Union[str, None] = "009_background_job_subject"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_analysis_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("analyzer_key", sa.String(length=128), nullable=False),
        sa.Column("analyzer_version", sa.String(length=32), nullable=False),
        sa.Column("config_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("profile_key", sa.String(length=128), nullable=False),
        sa.Column("profile_version", sa.String(length=32), nullable=False),
        sa.Column("profile_match_status", sa.String(length=64), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id",
            "analyzer_key",
            "analyzer_version",
            "config_fingerprint",
            name="uq_document_analysis_snapshot_contract",
        ),
    )
    op.create_index(
        "ix_document_analysis_snapshots_source_document_id",
        "document_analysis_snapshots",
        ["source_document_id"],
    )
    op.create_index(
        "ix_document_analysis_snapshots_snapshot_fingerprint",
        "document_analysis_snapshots",
        ["snapshot_fingerprint"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_analysis_snapshots_snapshot_fingerprint",
        table_name="document_analysis_snapshots",
    )
    op.drop_index(
        "ix_document_analysis_snapshots_source_document_id",
        table_name="document_analysis_snapshots",
    )
    op.drop_table("document_analysis_snapshots")
