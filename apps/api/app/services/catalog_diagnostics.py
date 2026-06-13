"""Catalogue layout diagnostics for builder UI."""

from __future__ import annotations

from typing import Any

DiagnosticSeverity = str  # "critical" | "warning" | "info"


def build_product_diagnostics(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build deduplicated diagnostics per product, one entry per type.
    Severity: fallback/incomplete_variants -> warning; no_image/no_category -> info.
    """
    diagnostics: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(item: dict[str, Any]) -> None:
        key = (item["master_id"], item["type"])
        if key in seen:
            return
        seen.add(key)
        diagnostics.append(item)

    for product in products:
        master_id = product["master_id"]
        master_name = product["master_name"]
        selection = product.get("layout_selection") or {}

        if selection.get("fallback_used"):
            add(
                {
                    "type": "fallback",
                    "severity": "warning",
                    "master_id": master_id,
                    "master_name": master_name,
                    "message": selection.get("fallback_reason") or "Se aplicó fallback automático",
                }
            )

        if product.get("has_variants") and product.get("variant_attribute_count", 0) == 0:
            add(
                {
                    "type": "incomplete_variants",
                    "severity": "warning",
                    "master_id": master_id,
                    "master_name": master_name,
                    "message": "Variantes sin atributos de variación visibles",
                }
            )

        if not product.get("image_url"):
            add(
                {
                    "type": "no_image",
                    "severity": "info",
                    "master_id": master_id,
                    "master_name": master_name,
                    "message": "Producto sin imagen",
                }
            )

        if product.get("section_name") == "General":
            add(
                {
                    "type": "no_category",
                    "severity": "info",
                    "master_id": master_id,
                    "master_name": master_name,
                    "message": "Sin categoría asignada (sección General)",
                }
            )

    return diagnostics


def summarize_diagnostics(diagnostics: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "warning": 0, "info": 0}
    for item in diagnostics:
        severity = item.get("severity", "info")
        if severity in counts:
            counts[severity] += 1
    return counts


def group_diagnostics_by_severity(
    diagnostics: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {"critical": [], "warning": [], "info": []}
    for item in diagnostics:
        severity = item.get("severity", "info")
        if severity not in grouped:
            grouped[severity] = []
        grouped[severity].append(item)
    return grouped
