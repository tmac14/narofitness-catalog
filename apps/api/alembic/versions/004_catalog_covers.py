"""Add catalog cover fields and catalog_section_covers table.

Revision ID: 004_catalog_covers
Revises: 003_catalog_show_desc_column
Create Date: 2026-06-08
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_catalog_covers"
down_revision: Union[str, None] = "003_catalog_show_desc_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    catalog_columns = {col["name"] for col in inspector.get_columns("catalogs")}
    if "cover_image_path" not in catalog_columns:
        op.add_column("catalogs", sa.Column("cover_image_path", sa.String(length=512), nullable=True))
    if "cover_subtitle" not in catalog_columns:
        op.add_column("catalogs", sa.Column("cover_subtitle", sa.String(length=255), nullable=True))

    if "catalog_section_covers" not in inspector.get_table_names():
        op.create_table(
            "catalog_section_covers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "catalog_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("catalogs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "category_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("categories.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("cover_image_path", sa.String(length=512), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("catalog_id", "category_id", name="uq_catalog_section_cover"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "catalog_section_covers" in inspector.get_table_names():
        op.drop_table("catalog_section_covers")

    catalog_columns = {col["name"] for col in inspector.get_columns("catalogs")}
    if "cover_subtitle" in catalog_columns:
        op.drop_column("catalogs", "cover_subtitle")
    if "cover_image_path" in catalog_columns:
        op.drop_column("catalogs", "cover_image_path")
