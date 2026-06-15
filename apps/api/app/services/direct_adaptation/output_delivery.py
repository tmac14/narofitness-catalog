"""Output profile and delivery mode resolution for direct adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings

OUTPUT_PROFILE_EMAIL = "email_optimized"
OUTPUT_PROFILE_ARCHIVE = "archive_quality"
OUTPUT_PROFILES = frozenset({OUTPUT_PROFILE_EMAIL, OUTPUT_PROFILE_ARCHIVE})

DELIVERY_PERSIST = "persist"
DELIVERY_EPHEMERAL = "ephemeral"
DELIVERY_MODES = frozenset({DELIVERY_PERSIST, DELIVERY_EPHEMERAL})

EXPORT_KIND_PREVIEW = "preview"
EXPORT_KIND_FINAL = "final"

ENCODE_PASS_EMAIL = "jpeg_dedup_v1"
ENCODE_PASS_ARCHIVE = "lossless_embed_v1"

EPHEMERAL_TTL_MIN_SECONDS = 300
EPHEMERAL_TTL_MAX_SECONDS = 86400

DEFAULT_OUTPUT_DELIVERY: dict[str, Any] = {
    "profile": OUTPUT_PROFILE_EMAIL,
    "delivery_mode": DELIVERY_PERSIST,
    "ephemeral_ttl_seconds": settings.adaptation_ephemeral_ttl_default_seconds,
    "email_budget_bytes": settings.adaptation_email_budget_bytes,
    "archive_soft_warn_bytes": settings.adaptation_archive_soft_warn_bytes,
}


class OutputDeliveryValidationError(ValueError):
    pass


class SizeBudgetExceededError(OutputDeliveryValidationError):
    def __init__(self, *, observed_bytes: int, budget_bytes: int) -> None:
        self.observed_bytes = observed_bytes
        self.budget_bytes = budget_bytes
        super().__init__(
            f"size_budget_exceeded: output {observed_bytes} bytes exceeds budget {budget_bytes}"
        )


@dataclass(frozen=True)
class ResolvedOutputDelivery:
    output_profile: str
    delivery_mode: str
    ephemeral_ttl_seconds: int
    email_budget_bytes: int
    archive_soft_warn_bytes: int
    export_kind: str

    @property
    def encode_pass(self) -> str:
        if self.output_profile == OUTPUT_PROFILE_ARCHIVE:
            return ENCODE_PASS_ARCHIVE
        return ENCODE_PASS_EMAIL


def build_output_delivery_manifest(
    resolved: ResolvedOutputDelivery,
    *,
    byte_length: int,
    within_budget: bool,
    size_warn: bool = False,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "profile": resolved.output_profile,
        "delivery_mode": resolved.delivery_mode,
        "byte_length": byte_length,
        "encode_pass": resolved.encode_pass,
        "within_budget": within_budget,
    }
    if resolved.output_profile == OUTPUT_PROFILE_EMAIL:
        body["budget_bytes"] = resolved.email_budget_bytes
    else:
        body["soft_warn_bytes"] = resolved.archive_soft_warn_bytes
        body["size_warn"] = size_warn
    if resolved.delivery_mode == DELIVERY_EPHEMERAL:
        body["ephemeral_ttl_seconds"] = resolved.ephemeral_ttl_seconds
    return body


def _clamp_ttl(raw: Any) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = settings.adaptation_ephemeral_ttl_default_seconds
    return max(EPHEMERAL_TTL_MIN_SECONDS, min(EPHEMERAL_TTL_MAX_SECONDS, value))


def resolve_output_delivery(
    recipe_json: dict[str, Any],
    *,
    job_request: dict[str, Any] | None = None,
    export_kind: str = EXPORT_KIND_PREVIEW,
) -> ResolvedOutputDelivery:
    recipe_cfg = dict(DEFAULT_OUTPUT_DELIVERY)
    recipe_cfg.update(recipe_json.get("output_delivery") or {})

    req = job_request or {}
    output_profile = str(req.get("output_profile") or recipe_cfg.get("profile") or OUTPUT_PROFILE_EMAIL)
    delivery_mode = str(req.get("delivery_mode") or recipe_cfg.get("delivery_mode") or DELIVERY_PERSIST)

    if output_profile not in OUTPUT_PROFILES:
        raise OutputDeliveryValidationError(f"profile_not_supported: {output_profile!r}")
    if delivery_mode not in DELIVERY_MODES:
        raise OutputDeliveryValidationError(f"delivery_mode_not_supported: {delivery_mode!r}")
    if export_kind == EXPORT_KIND_FINAL and delivery_mode != DELIVERY_PERSIST:
        raise OutputDeliveryValidationError("final export requires delivery_mode persist")

    return ResolvedOutputDelivery(
        output_profile=output_profile,
        delivery_mode=delivery_mode,
        ephemeral_ttl_seconds=_clamp_ttl(
            req.get("ephemeral_ttl_seconds", recipe_cfg.get("ephemeral_ttl_seconds"))
        ),
        email_budget_bytes=int(
            recipe_cfg.get("email_budget_bytes", settings.adaptation_email_budget_bytes)
        ),
        archive_soft_warn_bytes=int(
            recipe_cfg.get("archive_soft_warn_bytes", settings.adaptation_archive_soft_warn_bytes)
        ),
        export_kind=export_kind,
    )
