"""Catalog adaptation export records (preview/final manifests).

Revision ID: 013_catalog_adaptation_exports
Revises: 012_catalog_adaptation_projects
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_catalog_adaptation_exports"
down_revision: Union[str, None] = "012_catalog_adaptation_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "catalog_adaptation_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("export_kind", sa.String(length=32), nullable=False, server_default="preview"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="stub_completed"),
        sa.Column("manifest_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("artifact_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["catalog_adaptation_projects.id"]),
        sa.ForeignKeyConstraint(
            ["recipe_version_id"], ["catalog_adaptation_recipe_versions.id"]
        ),
        sa.ForeignKeyConstraint(["job_id"], ["background_jobs.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_catalog_adaptation_exports_project_id",
        "catalog_adaptation_exports",
        ["project_id"],
    )
    op.create_index(
        "ix_catalog_adaptation_exports_job_id",
        "catalog_adaptation_exports",
        ["job_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_adaptation_exports_job_id", table_name="catalog_adaptation_exports")
    op.drop_index(
        "ix_catalog_adaptation_exports_project_id", table_name="catalog_adaptation_exports"
    )
    op.drop_table("catalog_adaptation_exports")
