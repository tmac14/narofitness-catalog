import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    catalogs,
    categories,
    health,
    import_pdf,
    jobs,
    masters,
    price_lists,
    product_images,
    suppliers,
    system,
    taxonomy_mapping,
    variants,
)
from app.routers import settings as settings_router
from app.services.app_assets import assets_root
from app.services.job_constants import JOB_TYPE_CATALOG_EXPORT_PDF
from app.services.job_handlers import handle_catalog_export_pdf
from app.services.job_runner import get_job_runner
from app.services.pdf_export import pdf_engine_status, pdf_engines_available

_media_root = Path(settings.data_dir)
_media_root.mkdir(parents=True, exist_ok=True)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    data = Path(settings.data_dir)
    data.mkdir(parents=True, exist_ok=True)
    (data / "images").mkdir(exist_ok=True)
    (data / "exports").mkdir(exist_ok=True)
    engine, error = await asyncio.to_thread(pdf_engine_status)
    available = await asyncio.to_thread(pdf_engines_available)
    if engine:
        logger.info("PDF export engine: %s (available: %s)", engine, ", ".join(available))
    else:
        logger.error("PDF export unavailable: %s", error)
    runner = get_job_runner()
    runner.register_handler(JOB_TYPE_CATALOG_EXPORT_PDF, handle_catalog_export_pdf)
    await runner.start()
    try:
        yield
    finally:
        await runner.stop()


app = FastAPI(title="NaroCatalog API", version=settings.app_version, lifespan=lifespan)

app.mount("/api/v1/media", StaticFiles(directory=str(_media_root)), name="media")
app.mount("/api/v1/assets", StaticFiles(directory=str(assets_root())), name="assets")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = "/api/v1"
app.include_router(health.router, prefix=prefix)
app.include_router(suppliers.router, prefix=prefix)
app.include_router(import_pdf.router, prefix=prefix)
app.include_router(masters.router, prefix=prefix)
app.include_router(variants.router, prefix=prefix)
app.include_router(product_images.router, prefix=prefix)
app.include_router(categories.router, prefix=prefix)
app.include_router(taxonomy_mapping.router, prefix=prefix)
app.include_router(catalogs.router, prefix=prefix)
app.include_router(jobs.router, prefix=prefix)
app.include_router(price_lists.router, prefix=prefix)
app.include_router(settings_router.router, prefix=prefix)
app.include_router(system.router, prefix=prefix)
