"""Rate-limit behavior notes for Cursor Auto Mode vs Codex quota exhaustion."""

from __future__ import annotations

CURSOR_RATE_LIMIT_NOTE = (
    "Cursor rate limit: only Auto Mode may be available. Ordia does not block Auto Mode — "
    "record the resolved model slug in the Model usage section when known."
)

CODEX_RATE_LIMIT_NOTE = (
    "Codex rate limit: Codex cannot continue until quota resets. "
    "Switch to Runtime: ONLY_CURSOR in Cursor, defer the task, or wait for quota reset."
)


def is_cursor_auto_model(model_slug: str | None) -> bool:
    if not model_slug or not str(model_slug).strip():
        return True
    slug = str(model_slug).strip().lower()
    return slug in {"auto", "default"} or slug.startswith("auto")


def rate_limit_guidance(runtime: str | None) -> str:
    runtime_key = str(runtime or "").upper()
    if runtime_key in {"ONLY_CODEX", "CODEX_PLUS_CURSOR"}:
        return CODEX_RATE_LIMIT_NOTE
    if runtime_key == "ONLY_CURSOR":
        return CURSOR_RATE_LIMIT_NOTE
    return f"{CURSOR_RATE_LIMIT_NOTE} {CODEX_RATE_LIMIT_NOTE}"
