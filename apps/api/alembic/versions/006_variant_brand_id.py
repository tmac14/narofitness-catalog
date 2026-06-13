"""Add brand_id to product_variants for per-variant commercial brand.

Revision ID: 006_variant_brand_id
Revises: 005_background_jobs
Create Date: 2026-06-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_variant_brand_id"
down_revision: Union[str, None] = "005_background_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_variants",
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_product_variants_brand_id",
        "product_variants",
        "brands",
        ["brand_id"],
        ["id"],
    )
    op.create_index("ix_product_variants_brand_id", "product_variants", ["brand_id"])


def downgrade() -> None:
    op.drop_index("ix_product_variants_brand_id", table_name="product_variants")
    op.drop_constraint("fk_product_variants_brand_id", "product_variants", type_="foreignkey")
    op.drop_column("product_variants", "brand_id")
