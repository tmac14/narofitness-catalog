"""Background job status and type constants (PRES-5)."""

from __future__ import annotations

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

JOB_TYPE_CATALOG_EXPORT_PDF = "catalog_export_pdf"

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
    }
)
