"""Export catalog to PDF via HTML/CSS templates and swappable PdfExportEngine."""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings
from app.services.pdf_engines import PdfEngineError, PdfRenderRequest, resolve_pdf_export_engine
from app.services.pdf_engines.registry import (
    pdf_engine_fallback_name,
    pdf_engine_status,
    pdf_engines_available,
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "pdf" / "templates"

# Re-export for backward compatibility
__all__ = [
    "PdfEngineError",
    "TEMPLATES_DIR",
    "export_catalog_pdf",
    "pdf_engine_status",
    "pdf_engines_available",
    "pdf_engine_fallback_name",
    "render_catalog_html",
    "require_pdf_engine",
]


def require_pdf_engine() -> None:
    resolve_pdf_export_engine()


def _shell_template(context: dict[str, Any]) -> str:
    if context.get("catalog_shell") == "supplier_table":
        return "catalog_supplier_table.html"
    name = context.get("catalog_template") or "branded"
    return "catalog_branded.html" if name == "branded" else "catalog_default.html"


def _render_html(context: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = _shell_template(context)
    template = env.get_template(tpl)
    return template.render(**context)


def render_catalog_html(context: dict[str, Any]) -> str:
    return _render_html(context)


def _preview_url(context: dict[str, Any]) -> str | None:
    catalog_id = context.get("catalog_id")
    if not catalog_id:
        return None
    api_base = context.get("api_base") or "http://127.0.0.1:8000"
    return (
        f"{api_base.rstrip('/')}/api/v1/catalogs/{catalog_id}/preview/html"
        f"?api_base={quote(api_base, safe='')}&render_density=print"
    )


def export_catalog_pdf_to_path(
    context: dict[str, Any],
    out_path: Path | None,
) -> tuple[str, bytes]:
    """Render context to PDF using the active PdfExportEngine (shared by export and preview)."""
    if "generated_at" not in context:
        context["generated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    engine = resolve_pdf_export_engine()
    html = _render_html(context)
    base_url = context.get("data_dir") or str(TEMPLATES_DIR)

    request = PdfRenderRequest(
        html=html,
        base_url=base_url,
        preview_url=_preview_url(context) if engine.name == "playwright" else None,
    )

    target = out_path or Path(settings.data_dir) / "exports" / "_render_buffer.pdf"
    if out_path is None:
        target.parent.mkdir(parents=True, exist_ok=True)

    try:
        pdf_bytes = engine.render_pdf(request, target)
    except PdfEngineError:
        raise
    except Exception as exc:
        raise PdfEngineError(f"Error al generar PDF con {engine.name}: {exc}") from exc
    finally:
        if out_path is None and target.is_file():
            with contextlib.suppress(OSError):
                target.unlink()

    return engine.name, pdf_bytes


def export_catalog_pdf(
    context: dict[str, Any],
    out_path: Path,
) -> tuple[str, bytes]:
    """Render context to PDF using the active PdfExportEngine."""
    return export_catalog_pdf_to_path(context, out_path)
