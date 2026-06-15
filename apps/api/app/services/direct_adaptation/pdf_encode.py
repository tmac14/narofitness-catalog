"""Profile-specific PDF encode passes after the shared semantic pipeline."""

from __future__ import annotations

from typing import Any

import fitz

from app.services.direct_adaptation.output_delivery import (
    ENCODE_PASS_ARCHIVE,
    ENCODE_PASS_EMAIL,
    OUTPUT_PROFILE_ARCHIVE,
    OUTPUT_PROFILE_EMAIL,
    SizeBudgetExceededError,
)


def _light_deflate(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.tobytes(deflate=True, garbage=4, clean=True)
    finally:
        doc.close()


def _encode_email_optimized(pdf_bytes: bytes, *, budget_bytes: int) -> tuple[bytes, dict[str, Any]]:
    if len(pdf_bytes) <= budget_bytes:
        return pdf_bytes, {
            "encode_pass": ENCODE_PASS_EMAIL,
            "byte_length": len(pdf_bytes),
            "budget_bytes": budget_bytes,
            "within_budget": True,
            "note": "passthrough_under_budget",
        }
    output = _light_deflate(pdf_bytes)
    within_budget = len(output) <= budget_bytes
    metrics = {
        "encode_pass": ENCODE_PASS_EMAIL,
        "byte_length": len(output),
        "budget_bytes": budget_bytes,
        "within_budget": within_budget,
        "note": "light_deflate_v1",
    }
    if not within_budget:
        raise SizeBudgetExceededError(observed_bytes=len(output), budget_bytes=budget_bytes)
    return output, metrics


def _encode_archive_quality(pdf_bytes: bytes, *, soft_warn_bytes: int) -> tuple[bytes, dict[str, Any]]:
    output = _light_deflate(pdf_bytes)
    byte_length = len(output)
    return output, {
        "encode_pass": ENCODE_PASS_ARCHIVE,
        "byte_length": byte_length,
        "soft_warn_bytes": soft_warn_bytes,
        "size_warn": byte_length >= soft_warn_bytes,
        "within_budget": True,
        "note": "lossless_embed_v1",
    }


def apply_output_profile_encode(
    pdf_bytes: bytes,
    *,
    output_profile: str,
    email_budget_bytes: int,
    archive_soft_warn_bytes: int,
) -> tuple[bytes, dict[str, Any]]:
    if output_profile == OUTPUT_PROFILE_ARCHIVE:
        return _encode_archive_quality(pdf_bytes, soft_warn_bytes=archive_soft_warn_bytes)
    if output_profile == OUTPUT_PROFILE_EMAIL:
        return _encode_email_optimized(pdf_bytes, budget_bytes=email_budget_bytes)
    raise ValueError(f"Unsupported output profile: {output_profile}")
