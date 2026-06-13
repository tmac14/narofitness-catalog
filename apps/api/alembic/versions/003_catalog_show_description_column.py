"""Add show_description_column to catalogs.

Revision ID: 003_catalog_show_desc_column
Revises: 002_taxonomy_mapping_notes
Create Date: 2026-06-08
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_catalog_show_desc_column"
down_revision: Union[str, None] = "002_taxonomy_mapping_notes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("catalogs")}
    if "show_description_column" not in columns:
        op.add_column(
            "catalogs",
            sa.Column(
                "show_description_column",
                sa.Boolean(),
                server_default="true",
                nullable=False,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("catalogs")}
    if "show_description_column" in columns:
        op.drop_column("catalogs", "show_description_column")
