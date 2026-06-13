"""Playwright/Chromium PDF export engine (Phase 1 default)."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

from app.services.pdf_engines.base import PdfEngineError, PdfRenderRequest

logger = logging.getLogger(__name__)

_availability_error: str | None = None


def _probe() -> None:
    global _availability_error
    try:
        importlib.import_module("playwright.sync_api")
    except Exception as exc:
        _availability_error = (
            f"Playwright no está disponible: {exc}. "
            "Instale con: pip install playwright && playwright install chromium"
        )
        logger.error(_availability_error)
    else:
        _availability_error = None


def _margin_dict(margins_mm: dict[str, float]) -> dict[str, str]:
    return {key: f"{value}mm" for key, value in margins_mm.items()}


class PlaywrightEngine:
    name = "playwright"

    def is_available(self) -> tuple[bool, str | None]:
        # Re-probe on each check: uvicorn can cache a failed import from first boot
        # (e.g. Playwright installed after the worker started).
        _probe()
        if _availability_error:
            return False, _availability_error
        try:
            sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
        except Exception as exc:
            return False, f"Playwright/Chromium no disponible: {exc}"
        return True, None

    def render_pdf(self, request: PdfRenderRequest, out_path: Path) -> bytes:
        available, error = self.is_available()
        if not available:
            raise PdfEngineError(error or "Playwright no disponible")

        sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                if request.preview_url:
                    page.goto(request.preview_url, wait_until="networkidle", timeout=120_000)
                else:
                    page.set_content(request.html, wait_until="networkidle", timeout=120_000)
                page.pdf(
                    path=str(out_path),
                    format=request.page_format,
                    margin=_margin_dict(request.margins_mm),
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
        return out_path.read_bytes()
