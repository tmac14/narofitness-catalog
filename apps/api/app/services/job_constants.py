"""Background job status and type constants (PRES-5)."""

from __future__ import annotations

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

JOB_TYPE_CATALOG_EXPORT_PDF = "catalog_export_pdf"
JOB_TYPE_SOURCE_DOCUMENT_ANALYZE = "source_document_analyze"
JOB_TYPE_CATALOG_ADAPTATION_PREVIEW = "catalog_adaptation_preview"
JOB_TYPE_CATALOG_ADAPTATION_EXPORT = "catalog_adaptation_export"

SUBJECT_TYPE_CATALOG = "catalog"
SUBJECT_TYPE_SOURCE_DOCUMENT = "source_document"
SUBJECT_TYPE_CATALOG_ADAPTATION = "catalog_adaptation"

TERMINAL_JOB_STATUSES = frozenset({JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED, JOB_STATUS_CANCELLED})
ACTIVE_JOB_STATUSES = frozenset({JOB_STATUS_QUEUED, JOB_STATUS_RUNNING})

# Reserved for PRES-5B+ validation at creation time.
KNOWN_JOB_TYPES = frozenset(
    {
        "catalog_export_pdf",
        "catalog_preview_pdf",
        "catalog_import_pdf",
        "media_processing",
        "bulk_import_confirm",
        "catalogue_rebuild",
        "catalog_adaptation_preview",
        "catalog_adaptation_export",
        JOB_TYPE_CATALOG_ADAPTATION_PREVIEW,
        JOB_TYPE_CATALOG_ADAPTATION_EXPORT,
        JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
    }
)
