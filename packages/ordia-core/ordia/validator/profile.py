"""Profile header vs manifest enforcement."""

from __future__ import annotations

from ordia.config import OrdiaConfig


def validate_profile_match(
    config: OrdiaConfig,
    declared_profile: str | None,
    errors: list[str],
    warnings: list[str],
    *,
    strict: bool = False,
) -> None:
    if not declared_profile:
        return
    if declared_profile == config.profile:
        return
    message = (
        f"Ordia profile header {declared_profile!r} does not match "
        f"ordia.yaml profile {config.profile!r}"
    )
    if strict:
        errors.append(message)
    else:
        warnings.append(message)
