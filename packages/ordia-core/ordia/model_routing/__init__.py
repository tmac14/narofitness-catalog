"""Ordia model tier routing."""

from ordia.model_routing.recommend import ModelRecommendation, recommend_for_task
from ordia.model_routing.registry import default_registry_path, load_registry, model_slug_to_tier
from ordia.model_routing.report import ModelUsageReport, usage_section_template
from ordia.model_routing.tiers import VALID_TIERS, normalize_tier, tier_at_least

__all__ = [
    "VALID_TIERS",
    "ModelRecommendation",
    "ModelUsageReport",
    "default_registry_path",
    "load_registry",
    "model_slug_to_tier",
    "normalize_tier",
    "recommend_for_task",
    "tier_at_least",
    "usage_section_template",
]
