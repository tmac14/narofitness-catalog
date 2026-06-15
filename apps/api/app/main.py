import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    catalogs,
    catalog_adaptations,
    categories,
    health,
    import_pdf,
    jobs,
    masters,
    price_lists,
    product_images,
    source_documents,
    suppliers,
    system,
    taxonomy_mapping,
    variants,
)
from app.routers import settings as settings_router
from app.services.app_assets import assets_root
from app.services.job_constants import (
    JOB_TYPE_CATALOG_ADAPTATION_EXPORT,
    JOB_TYPE_CATALOG_ADAPTATION_PREVIEW,
    JOB_TYPE_CATALOG_EXPORT_PDF,
    JOB_TYPE_SOURCE_DOCUMENT_ANALYZE,
)
from app.services.job_handlers import handle_catalog_export_pdf
from app.services.job_handlers.catalog_adaptation_export import handle_catalog_adaptation_export
from app.services.job_handlers.catalog_adaptation_preview import handle_catalog_adaptation_preview
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
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
    from app.services.source_document_storage import private_artifact_root

    private_artifact_root()
    engine, error = await asyncio.to_thread(pdf_engine_status)
    available = await asyncio.to_thread(pdf_engines_available)
    if engine:
        logger.info("PDF export engine: %s (available: %s)", engine, ", ".join(available))
    else:
        logger.error("PDF export unavailable: %s", error)
    runner = get_job_runner()
    runner.register_handler(JOB_TYPE_CATALOG_EXPORT_PDF, handle_catalog_export_pdf)
    runner.register_handler(JOB_TYPE_SOURCE_DOCUMENT_ANALYZE, handle_source_document_analyze)
    runner.register_handler(JOB_TYPE_CATALOG_ADAPTATION_PREVIEW, handle_catalog_adaptation_preview)
    runner.register_handler(JOB_TYPE_CATALOG_ADAPTATION_EXPORT, handle_catalog_adaptation_export)
    cleanup_task = asyncio.create_task(_ephemeral_cleanup_loop())
    await runner.start()
    try:
        yield
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        await runner.stop()


async def _ephemeral_cleanup_loop() -> None:
    from app.services.adaptation_ephemeral_cleanup import cleanup_expired_ephemeral_exports

    while True:
        try:
            await cleanup_expired_ephemeral_exports()
        except Exception:
            logger.exception("ephemeral adaptation cleanup failed")
        await asyncio.sleep(3600)


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
app.include_router(source_documents.router, prefix=prefix)
app.include_router(catalog_adaptations.router, prefix=prefix)
app.include_router(settings_router.router, prefix=prefix)
app.include_router(system.router, prefix=prefix)
