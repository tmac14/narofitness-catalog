"""Add pdf_artifact_path to catalog adaptation exports.

Revision ID: 014_adaptation_export_pdf_path
Revises: 013_catalog_adaptation_exports
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_adaptation_export_pdf_path"
down_revision: Union[str, None] = "013_catalog_adaptation_exports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "catalog_adaptation_exports",
        sa.Column("pdf_artifact_path", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("catalog_adaptation_exports", "pdf_artifact_path")
