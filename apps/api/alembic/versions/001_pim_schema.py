"""PIM catalog schema — single squashed migration.

Revision ID: 001_pim_schema
Revises:
Create Date: 2026-06-07
"""

from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_pim_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FDL_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
        "non_weight_prefixes": ["CRONEXO", "VARJH"],
        "false_family_suffixes": ["NEXO"],
        "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
        "explicit_numeric_sku_regex": r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$",
        "explicit_one_per_sku_confidence": 0.85,
        "explicit_one_per_sku_min_category_confidence": 1.0,
        "numeric_suffix_family_regex": r"^(?P<prefix>DOP4A|DOPH|DNG|DOP|MPS|MU|MP)(?P<size>\d{3})$",
        "numeric_suffix_family_prefixes": ["DOP4A", "DOPH", "DOP", "DNG", "MPS", "MU", "MP"],
        "numeric_suffix_family_mancuerna_prefixes": ["MPS", "MU", "MP"],
        "numeric_suffix_family_mancuernas_slug": "mancuernas",
        "numeric_suffix_family_section": "DISCOS Y BARRAS",
        "numeric_suffix_family_confidence": 0.90,
        "cross_training_bumper_family_regex": r"^(?P<prefix>DOB3C|DOBC|DOBN|DOB)(?P<size>\d{3})$",
        "cross_training_bumper_prefixes": ["DOB3C", "DOBC", "DOBN", "DOB"],
        "cross_training_bumper_section_root": "CROSSTRAINING",
        "cross_training_bumper_name_tokens": ["disco", "bumper"],
        "cross_training_bumper_category_slug": "discos",
        "cross_training_bumper_confidence": 0.90,
        "attr_from_name": {
            "color": ["Negro", "Rojo", "Azul", "Verde", "Amarillo", "Rosa", "Gris", "Blanco"],
            "material": ["Goma maciza", "Hierro", "Acero", "Urethane", "Caucho"],
            "casquillo": ["Acero", "Latón"],
        },
    },
    "update_metadata_on_import": False,
}


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_brands_slug", "brands", ["slug"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table(
        "units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(16), nullable=False),
    )
    op.create_index("ix_units_code", "units", ["code"], unique=True)

    op.create_table(
        "spec_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("data_type", sa.String(16), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units.id")),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("is_filterable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_printable", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("description", sa.Text()),
    )
    op.create_index("ix_spec_definitions_key", "spec_definitions", ["key"], unique=True)

    op.create_table(
        "spec_allowed_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("spec_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spec_definitions.id")),
        sa.Column("value_key", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("spec_definition_id", "value_key", name="uq_spec_allowed_value"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_suppliers_code", "suppliers", ["code"], unique=True)

    op.create_table(
        "import_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id")),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parser_key", sa.String(64), nullable=False),
        sa.Column("config", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_default", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("supplier_id", "slug", name="uq_supplier_profile_slug"),
    )

    op.create_table(
        "product_masters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("raw_name", sa.Text()),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id")),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("description", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("master_key", sa.String(128)),
        sa.Column("catalog_slug", sa.String(128)),
        sa.Column("status", sa.String(32), server_default="confirmed", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_product_masters_master_key", "product_masters", ["master_key"], unique=True)
    op.create_index("ix_product_masters_catalog_slug", "product_masters", ["catalog_slug"], unique=True)

    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_masters.id")),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id")),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("ean", sa.String(20)),
        sa.Column("display_name", sa.String(255)),
        sa.Column("reference_label", sa.String(255)),
        sa.Column("raw_name", sa.Text()),
        sa.Column("status", sa.String(32), server_default="confirmed", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("supplier_id", "sku", name="uq_supplier_sku"),
    )
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"])

    op.create_table(
        "product_master_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_masters.id")),
        sa.Column("spec_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spec_definitions.id")),
        sa.Column("value_number", sa.Numeric(14, 4)),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_boolean", sa.Boolean()),
        sa.Column("allowed_value_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spec_allowed_values.id")),
        sa.Column("source", sa.String(32), server_default="import"),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.UniqueConstraint("master_id", "spec_definition_id", name="uq_master_spec"),
    )

    op.create_table(
        "product_variant_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")),
        sa.Column("spec_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spec_definitions.id")),
        sa.Column("value_number", sa.Numeric(14, 4)),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_boolean", sa.Boolean()),
        sa.Column("allowed_value_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spec_allowed_values.id")),
        sa.Column("source", sa.String(32), server_default="import"),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.UniqueConstraint("variant_id", "spec_definition_id", name="uq_variant_spec"),
    )

    op.create_table(
        "category_spec_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("spec_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spec_definitions.id")),
        sa.Column("is_required", sa.Boolean(), server_default="false"),
        sa.Column("is_variant_axis_candidate", sa.Boolean(), server_default="false"),
        sa.Column("is_highlight", sa.Boolean(), server_default="false"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("print_group", sa.String(64)),
        sa.UniqueConstraint("category_id", "spec_definition_id", name="uq_category_spec_profile"),
    )

    op.create_table(
        "supplier_product_family_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id")),
        sa.Column("source_master_key", sa.String(128), nullable=False),
        sa.Column("product_master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_masters.id")),
        sa.Column("import_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_profiles.id")),
        sa.Column("notes", sa.Text()),
        sa.UniqueConstraint("supplier_id", "source_master_key", name="uq_supplier_source_master_key"),
    )

    op.create_table(
        "taxonomy_mapping_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id")),
        sa.Column("import_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_profiles.id")),
        sa.Column("match_type", sa.String(32), nullable=False),
        sa.Column("match_value", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="100"),
        sa.Column("target_category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("target_subcategory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("confidence", sa.Numeric(4, 3), server_default="1.0"),
        sa.Column("requires_review", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id")),
        sa.Column("import_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_profiles.id")),
        sa.Column("source_filename", sa.String(512), nullable=False),
        sa.Column("parser_key", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(32), nullable=False),
        sa.Column("effective_date", sa.Date()),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("row_counts", postgresql.JSONB(), server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(128)),
        sa.Column("notes", sa.Text()),
    )

    op.create_table(
        "import_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batches.id")),
        sa.Column("source_page", sa.Integer()),
        sa.Column("source_row_index", sa.Integer(), nullable=False),
        sa.Column("raw_lines", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("raw_name", sa.Text()),
        sa.Column("normalized_name", sa.Text()),
        sa.Column("detected_category_path_raw", sa.Text()),
        sa.Column("mapped_category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("mapped_category_slug", sa.String(128)),
        sa.Column("mapped_category_confidence", sa.Numeric(4, 3)),
        sa.Column("brand_raw", sa.String(128)),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id")),
        sa.Column("sku", sa.String(64)),
        sa.Column("ean", sa.String(20)),
        sa.Column("price_amount", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("master_key", sa.String(128)),
        sa.Column("master_name", sa.Text()),
        sa.Column("reference_label", sa.String(255)),
        sa.Column("grouping_confidence", sa.Numeric(4, 3)),
        sa.Column("grouping_reason", sa.Text()),
        sa.Column("parsed_variant_specs_raw", postgresql.JSONB(), server_default="{}"),
        sa.Column("parsed_common_specs_raw", postgresql.JSONB(), server_default="{}"),
        sa.Column("parsed_payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("review_reasons", postgresql.JSONB(), server_default="[]"),
        sa.Column("review_status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("confirmed_product_master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_masters.id")),
        sa.Column("confirmed_product_variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("batch_id", "source_row_index", name="uq_import_row_batch_index"),
    )
    op.create_index("ix_import_rows_batch_status", "import_rows", ["batch_id", "review_status"])

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_masters.id")),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
        sa.Column("status", sa.String(32), server_default="confirmed"),
    )

    op.create_table(
        "supplier_price_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id")),
        sa.Column("import_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_profiles.id")),
        sa.Column("source_filename", sa.String(512), nullable=False),
        sa.Column("effective_date", sa.Date()),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "supplier_price_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("list_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_price_lists.id")),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.UniqueConstraint("list_id", "variant_id", name="uq_list_variant"),
    )

    op.create_table(
        "catalogs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_markup_percent", sa.Numeric(6, 2), server_default="0"),
        sa.Column("show_iva_column", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("layout_mode", sa.String(16), server_default="automatic", nullable=False),
        sa.Column("uniform_layout_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "catalog_product_layouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("catalog_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalogs.id")),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_masters.id")),
        sa.Column("layout_id", sa.String(64), nullable=False),
        sa.UniqueConstraint("catalog_id", "master_id", name="uq_catalog_master_layout"),
    )

    op.create_table(
        "catalog_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("catalog_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalogs.id")),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")),
        sa.Column("markup_percent", sa.Numeric(6, 2)),
        sa.Column("final_price_override", sa.Numeric(12, 2)),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.UniqueConstraint("catalog_id", "variant_id", name="uq_catalog_variant"),
    )

    op.create_table(
        "catalog_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("catalog_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalogs.id")),
        sa.Column("file_path", sa.String(512)),
        sa.Column("engine", sa.String(32)),
        sa.Column("exported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )

    conn = op.get_bind()
    fdl_id = str(uuid.uuid4())
    profile_id = str(uuid.uuid4())
    conn.execute(
        sa.text(
            "INSERT INTO suppliers (id, code, name, is_active) VALUES (:id, 'FDL', 'FDL Fitness', true)"
        ),
        {"id": fdl_id},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO import_profiles (id, supplier_id, slug, name, parser_key, config, is_default, is_active)
            VALUES (:pid, :sid, 'fdl-tarifa-pdf-v1', 'Tarifa mayorista PDF', 'fdl_pdf_v1', :config, true, true)
            """
        ).bindparams(sa.bindparam("config", type_=postgresql.JSONB)),
        {"pid": profile_id, "sid": fdl_id, "config": FDL_CONFIG},
    )


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for squashed PIM schema")
