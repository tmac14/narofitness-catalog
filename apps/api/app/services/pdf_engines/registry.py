"""PDF engine registry and selection."""

from __future__ import annotations

from app.config import settings
from app.services.pdf_engines.base import PdfEngineError, PdfExportEngine
from app.services.pdf_engines.docraptor_engine import DocRaptorEngine
from app.services.pdf_engines.playwright_engine import PlaywrightEngine
from app.services.pdf_engines.princexml_engine import PrinceXmlEngine
from app.services.pdf_engines.weasyprint_engine import WeasyPrintEngine

_AUTO_ORDER = ("playwright", "weasyprint")

_ENGINES: dict[str, PdfExportEngine] = {
    "playwright": PlaywrightEngine(),
    "weasyprint": WeasyPrintEngine(),
    "princexml": PrinceXmlEngine(),
    "docraptor": DocRaptorEngine(),
}


def list_pdf_engines() -> list[str]:
    return list(_ENGINES.keys())


def get_pdf_engine(name: str) -> PdfExportEngine:
    if name not in _ENGINES:
        raise KeyError(f"Unknown PDF engine: {name}")
    return _ENGINES[name]


def pdf_engines_available() -> list[str]:
    return [name for name in _ENGINES if _ENGINES[name].is_available()[0]]


def pdf_engine_fallback_name(active: str | None) -> str | None:
    for name in _AUTO_ORDER:
        if name == active:
            continue
        if _ENGINES[name].is_available()[0]:
            return name
    return None


def pdf_engine_status() -> tuple[str | None, str | None]:
    """Return (active engine name, error if none available)."""
    try:
        engine = resolve_pdf_export_engine()
        return engine.name, None
    except PdfEngineError as exc:
        return None, str(exc)


def resolve_pdf_export_engine() -> PdfExportEngine:
    preferred = (settings.pdf_export_engine or "auto").strip().lower()
    if preferred != "auto":
        engine = get_pdf_engine(preferred)
        ok, err = engine.is_available()
        if ok:
            return engine
        raise PdfEngineError(err or f"Motor PDF '{preferred}' no disponible")

    for name in _AUTO_ORDER:
        engine = get_pdf_engine(name)
        ok, _ = engine.is_available()
        if ok:
            return engine

    errors = []
    for name in _AUTO_ORDER:
        _, err = _ENGINES[name].is_available()
        if err:
            errors.append(f"{name}: {err}")
    raise PdfEngineError(
        "Ningún motor PDF disponible. " + "; ".join(errors)
        if errors
        else "Ningún motor PDF disponible."
    )
