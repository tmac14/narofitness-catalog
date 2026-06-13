"""Display helpers for hierarchical product categories."""

from __future__ import annotations

from app.models import Category


def master_category_labels(category: Category | None) -> tuple[str | None, str | None]:
    """Return (parent_name, subcategory_name) for stacked list display."""
    if category is None:
        return None, None
    if category.parent_id is not None:
        parent_name = category.parent.name if category.parent else None
        sub_name = category.name or None
        if (
            parent_name
            and sub_name
            and parent_name.strip().casefold() == sub_name.strip().casefold()
        ):
            return parent_name, None
        return parent_name, sub_name
    return category.name or None, None


def master_category_display_name(category: Category | None) -> str | None:
    """Return a single category label (subcategory when assigned, else parent)."""
    parent, sub = master_category_labels(category)
    return sub or parent
