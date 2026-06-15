"""Catalog adaptation projects and immutable recipe versions.

Revision ID: 012_catalog_adaptation_projects
Revises: 011_import_batch_source_link
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_catalog_adaptation_projects"
down_revision: Union[str, None] = "011_import_batch_source_link"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "catalog_adaptation_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("profile_key", sa.String(length=128), nullable=False),
        sa.Column("profile_version", sa.String(length=32), nullable=False),
        sa.Column(
            "active_recipe_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"]),
        sa.ForeignKeyConstraint(
            ["analysis_snapshot_id"], ["document_analysis_snapshots.id"]
        ),
    )
    op.create_index(
        "ix_catalog_adaptation_projects_source_document_id",
        "catalog_adaptation_projects",
        ["source_document_id"],
    )

    op.create_table(
        "catalog_adaptation_recipe_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("recipe_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("recipe_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["catalog_adaptation_projects.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_catalog_adaptation_recipe_project_version",
        ),
    )
    op.create_index(
        "ix_catalog_adaptation_recipe_versions_project_id",
        "catalog_adaptation_recipe_versions",
        ["project_id"],
    )

    op.create_foreign_key(
        "fk_catalog_adaptation_projects_active_recipe_version_id",
        "catalog_adaptation_projects",
        "catalog_adaptation_recipe_versions",
        ["active_recipe_version_id"],
        ["id"],
        use_alter=True,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_catalog_adaptation_projects_active_recipe_version_id",
        "catalog_adaptation_projects",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_catalog_adaptation_recipe_versions_project_id",
        table_name="catalog_adaptation_recipe_versions",
    )
    op.drop_table("catalog_adaptation_recipe_versions")
    op.drop_index(
        "ix_catalog_adaptation_projects_source_document_id",
        table_name="catalog_adaptation_projects",
    )
    op.drop_table("catalog_adaptation_projects")
