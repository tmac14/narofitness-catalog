"""Link import_batches to source documents and analysis snapshots.

Revision ID: 011_import_batch_source_link
Revises: 010_document_analysis_snapshots
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_import_batch_source_link"
down_revision: Union[str, None] = "010_document_analysis_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "import_batches",
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "import_batches",
        sa.Column("analysis_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_import_batches_source_document_id",
        "import_batches",
        "source_documents",
        ["source_document_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_import_batches_analysis_snapshot_id",
        "import_batches",
        "document_analysis_snapshots",
        ["analysis_snapshot_id"],
        ["id"],
    )
    op.create_index(
        "ix_import_batches_source_document_id",
        "import_batches",
        ["source_document_id"],
    )
    op.create_index(
        "ix_import_batches_analysis_snapshot_id",
        "import_batches",
        ["analysis_snapshot_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_import_batches_analysis_snapshot_id", table_name="import_batches")
    op.drop_index("ix_import_batches_source_document_id", table_name="import_batches")
    op.drop_constraint(
        "fk_import_batches_analysis_snapshot_id", "import_batches", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_import_batches_source_document_id", "import_batches", type_="foreignkey"
    )
    op.drop_column("import_batches", "analysis_snapshot_id")
    op.drop_column("import_batches", "source_document_id")
