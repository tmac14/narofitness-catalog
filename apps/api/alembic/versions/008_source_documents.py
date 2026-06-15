"""Add source_documents table for immutable private PDF intake.

Revision ID: 008_source_documents
Revises: 007_product_image_source
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_source_documents"
down_revision: Union[str, None] = "007_product_image_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("validation_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_source_documents_sha256", "source_documents", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_source_documents_sha256", table_name="source_documents")
    op.drop_table("source_documents")
