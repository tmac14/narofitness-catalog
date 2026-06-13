"""Add notes column to taxonomy_mapping_rules.

Revision ID: 002_taxonomy_mapping_notes
Revises: 001_pim_schema
Create Date: 2026-06-07
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_taxonomy_mapping_notes"
down_revision: Union[str, None] = "001_pim_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("taxonomy_mapping_rules")}
    if "notes" not in columns:
        op.add_column("taxonomy_mapping_rules", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("taxonomy_mapping_rules")}
    if "notes" in columns:
        op.drop_column("taxonomy_mapping_rules", "notes")
