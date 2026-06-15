"""Revision ID: 015_adaptation_output_delivery

Add output delivery fields to exports and catalog_adaptation_approvals table.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_adaptation_output_delivery"
down_revision: Union[str, None] = "014_adaptation_export_pdf_path"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "catalog_adaptation_exports",
        sa.Column("output_profile", sa.String(length=32), nullable=False, server_default="email_optimized"),
    )
    op.add_column(
        "catalog_adaptation_exports",
        sa.Column("delivery_mode", sa.String(length=32), nullable=False, server_default="persist"),
    )
    op.add_column(
        "catalog_adaptation_exports",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "catalog_adaptation_approvals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("recipe_version_id", sa.UUID(), nullable=False),
        sa.Column("export_id", sa.UUID(), nullable=False),
        sa.Column("manifest_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("output_profile", sa.String(length=32), nullable=False),
        sa.Column("renderer_version", sa.String(length=32), nullable=False),
        sa.Column("approved_by", sa.String(length=128), nullable=True),
        sa.Column("approval_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["export_id"], ["catalog_adaptation_exports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["catalog_adaptation_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["catalog_adaptation_recipe_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_catalog_adaptation_approvals_project"),
    )
    op.create_index(
        "ix_catalog_adaptation_approvals_project_id",
        "catalog_adaptation_approvals",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_adaptation_approvals_project_id", table_name="catalog_adaptation_approvals")
    op.drop_table("catalog_adaptation_approvals")
    op.drop_column("catalog_adaptation_exports", "expires_at")
    op.drop_column("catalog_adaptation_exports", "delivery_mode")
    op.drop_column("catalog_adaptation_exports", "output_profile")
