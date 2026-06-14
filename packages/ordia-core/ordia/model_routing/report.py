"""Canonical Model usage report for prompt/task deliverables (ORDIA-D022)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_ECONOMIC_BY_BAND: dict[str, dict[str, str]] = {
    "minimal": {"en": "light", "es": "leve"},
    "low": {"en": "light", "es": "leve"},
    "medium": {"en": "medium", "es": "mediana"},
    "high": {"en": "heavy", "es": "pesada"},
    "unknown": {"en": "unknown", "es": "desconocida"},
}


def economic_rating(registry: dict[str, Any], tier: str, *, cost_band: str | None = None) -> dict[str, str]:
    by_tier = registry.get("economic_ratings", {})
    if isinstance(by_tier, dict) and tier in by_tier:
        entry = by_tier[tier]
        if isinstance(entry, dict):
            return {
                "en": str(entry.get("en", "unknown")),
                "es": str(entry.get("es", "desconocida")),
            }
    band = (cost_band or "unknown").lower()
    by_band = registry.get("economic_rating_by_band", DEFAULT_ECONOMIC_BY_BAND)
    if isinstance(by_band, dict) and band in by_band:
        entry = by_band[band]
        if isinstance(entry, dict):
            return {
                "en": str(entry.get("en", "unknown")),
                "es": str(entry.get("es", "desconocida")),
            }
    return DEFAULT_ECONOMIC_BY_BAND.get(band, DEFAULT_ECONOMIC_BY_BAND["unknown"])


def format_economic_rating_label(rating: dict[str, str]) -> str:
    return f"{rating['en']} ({rating['es']})"


MODEL_USAGE_SECTION_TEMPLATE = """## Model usage
- **Model used:** <model slug + runtime> — required in every prompt/task deliverable
- **Approved tier:** T2
- **Tokens — prompt:** <n> (est.) | **completion:** <n> (est.) | **total:** <n> (est.)
- **Context peak:** <n>% (hook) / unknown (Codex)
- **Economic rating:** medium (mediana) — scale: light/leve · medium/mediana · heavy/pesada
- **Tier escalation:** none | T1->T2 (reason)
- **Cost note:** within band | exceeded (justify)"""


@dataclass
class ModelUsageReport:
    model_used: str
    approved_tier: str
    prompt_tokens: str = "unknown (est.)"
    completion_tokens: str = "unknown (est.)"
    total_tokens: str = "unknown (est.)"
    context_peak: str = "unknown"
    economic_rating_en: str = "unknown"
    economic_rating_es: str = "desconocida"
    tier_escalation: str = "none"
    cost_note: str = "within band"

    def render(self) -> str:
        economic = format_economic_rating_label(
            {"en": self.economic_rating_en, "es": self.economic_rating_es}
        )
        return "\n".join(
            [
                "## Model usage",
                f"- **Model used:** {self.model_used}",
                f"- **Approved tier:** {self.approved_tier}",
                (
                    f"- **Tokens — prompt:** {self.prompt_tokens} | "
                    f"**completion:** {self.completion_tokens} | **total:** {self.total_tokens}"
                ),
                f"- **Context peak:** {self.context_peak}",
                f"- **Economic rating:** {economic} — scale: light/leve · medium/mediana · heavy/pesada",
                f"- **Tier escalation:** {self.tier_escalation}",
                f"- **Cost note:** {self.cost_note}",
            ]
        )


def usage_section_template() -> str:
    return MODEL_USAGE_SECTION_TEMPLATE
