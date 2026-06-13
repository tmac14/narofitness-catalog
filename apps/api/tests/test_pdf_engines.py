"""Tests for PdfExportEngine registry and adapters."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.pdf_engines import PdfEngineError, PdfRenderRequest, resolve_pdf_export_engine
from app.services.pdf_engines.docraptor_engine import DocRaptorEngine
from app.services.pdf_engines.princexml_engine import PrinceXmlEngine
from app.services.pdf_engines.registry import (
    get_pdf_engine,
    list_pdf_engines,
    pdf_engine_fallback_name,
    pdf_engine_status,
    pdf_engines_available,
)

_engine, _ = pdf_engine_status()
_has_engine = pytest.mark.skipif(not _engine, reason="No PDF engine available in this environment")


def test_list_pdf_engines_includes_phase1_and_stubs():
    names = list_pdf_engines()
    assert "playwright" in names
    assert "weasyprint" in names
    assert "princexml" in names
    assert "docraptor" in names


def test_stub_engines_unavailable():
    assert PrinceXmlEngine().is_available()[0] is False
    assert DocRaptorEngine().is_available()[0] is False


@_has_engine
def test_resolve_pdf_export_engine_returns_available_engine():
    engine = resolve_pdf_export_engine()
    assert engine.name in pdf_engines_available()


@_has_engine
def test_pdf_engine_status_returns_active_engine():
    name, error = pdf_engine_status()
    assert name is not None
    assert error is None


def test_pdf_engine_status_none_when_all_fail(monkeypatch):
    def _blocked():
        return False, "blocked"

    for name in list_pdf_engines():
        engine = get_pdf_engine(name)
        monkeypatch.setattr(engine, "is_available", _blocked)

    name, error = pdf_engine_status()
    assert name is None
    assert error is not None


@_has_engine
def test_pdf_engine_fallback_name():
    active, _ = pdf_engine_status()
    fallback = pdf_engine_fallback_name(active)
    if fallback:
        assert fallback in list_pdf_engines()
        assert fallback != active


@_has_engine
def test_weasyprint_engine_renders_minimal_html(tmp_path: Path):
    engine = get_pdf_engine("weasyprint")
    ok, _ = engine.is_available()
    if not ok:
        pytest.skip("WeasyPrint not available")

    out = tmp_path / "test.pdf"
    html = "<html><body><h1>Engine test</h1></body></html>"
    data = engine.render_pdf(PdfRenderRequest(html=html, base_url=str(tmp_path)), out)
    assert data[:4] == b"%PDF"


def test_playwright_engine_pdf_uses_a4_print_settings(tmp_path: Path, monkeypatch):
    import importlib.util

    if importlib.util.find_spec("playwright.sync_api") is None:
        pytest.skip("Playwright not installed")

    pdf_calls: list[dict] = []

    class FakePage:
        def goto(self, *_args, **_kwargs):
            return None

        def pdf(self, **kwargs):
            pdf_calls.append(kwargs)
            Path(kwargs["path"]).write_bytes(b"%PDF-fake")

    class FakeBrowser:
        def new_page(self):
            return FakePage()

        def close(self):
            return None

    class FakeChromium:
        def launch(self, **_kwargs):
            return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()

    class FakeCtx:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr("playwright.sync_api.sync_playwright", lambda: FakeCtx())
    monkeypatch.setattr(
        "app.services.pdf_engines.playwright_engine.PlaywrightEngine.is_available",
        lambda self: (True, None),
    )

    engine = get_pdf_engine("playwright")
    out = tmp_path / "pw.pdf"
    engine.render_pdf(
        PdfRenderRequest(
            html="<html></html>",
            base_url=str(tmp_path),
            preview_url="http://127.0.0.1:8000/api/v1/catalogs/x/preview/html?render_density=print",
        ),
        out,
    )
    assert pdf_calls
    assert pdf_calls[0]["format"] == "A4"
    assert pdf_calls[0]["print_background"] is True
    assert pdf_calls[0]["prefer_css_page_size"] is True


def test_resolve_forced_unavailable_engine_raises(monkeypatch):
    monkeypatch.setattr("app.config.settings.pdf_export_engine", "princexml")
    with pytest.raises(PdfEngineError, match="PrinceXML"):
        resolve_pdf_export_engine()
