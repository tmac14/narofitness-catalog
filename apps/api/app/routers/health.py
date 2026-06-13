import asyncio

from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthResponse
from app.services.pdf_export import (
    pdf_engine_fallback_name,
    pdf_engine_status,
    pdf_engines_available,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # Playwright probe launches Chromium (sync); must not run on the asyncio event loop.
    engine, error = await asyncio.to_thread(pdf_engine_status)
    available = await asyncio.to_thread(pdf_engines_available)

    return HealthResponse(
        status="ok" if engine else "degraded",
        version=settings.app_version,
        pdf_engine=engine,
        pdf_engine_error=error,
        pdf_engine_fallback=pdf_engine_fallback_name(engine),
        pdf_engines_available=available,
    )
