"""Add source_type and external_url to product_images for external URL ingest.

Revision ID: 007_product_image_source
Revises: 006_variant_brand_id
Create Date: 2026-06-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_product_image_source"
down_revision: Union[str, None] = "006_variant_brand_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_images",
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="upload"),
    )
    op.add_column(
        "product_images",
        sa.Column("external_url", sa.String(length=2048), nullable=True),
    )
    op.create_check_constraint(
        "ck_product_images_source_type",
        "product_images",
        "source_type IN ('upload', 'external_url')",
    )
    op.create_check_constraint(
        "ck_product_images_external_url_consistency",
        "product_images",
        "(source_type = 'upload' AND external_url IS NULL) "
        "OR (source_type = 'external_url' AND external_url IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_product_images_external_url_consistency", "product_images", type_="check")
    op.drop_constraint("ck_product_images_source_type", "product_images", type_="check")
    op.drop_column("product_images", "external_url")
    op.drop_column("product_images", "source_type")
