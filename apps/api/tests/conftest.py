import os
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[1]


def _reference_pdf() -> Path:
    name = "FDL .. Tarifa Mayorista 01-Febr-2026.pdf"
    candidates = [Path("/temp") / name]
    if len(API_ROOT.parents) > 2:
        candidates.insert(0, API_ROOT.parents[2] / "temp" / name)
    for p in candidates:
        if p.is_file():
            return p
    return candidates[-1]


REFERENCE_PDF = _reference_pdf()


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: needs PostgreSQL")


@pytest.fixture
def reference_pdf() -> Path | None:
    if REFERENCE_PDF.is_file():
        return REFERENCE_PDF
    return None


@pytest.fixture
def integration_db():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run DB integration tests")
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://narocatalog:narocatalog@localhost:5433/narocatalog",
    )


@pytest.fixture(autouse=True)
async def _dispose_engine_after_integration(request):
    yield
    if request.node.get_closest_marker("integration"):
        from app.database import engine

        await engine.dispose()
