"""Entry point for PyInstaller-bundled API server."""

import os
import subprocess
import sys
from pathlib import Path

import uvicorn


def _migrate() -> None:
    api_dir = Path(__file__).resolve().parent
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(api_dir),
        env=os.environ.copy(),
        check=False,
    )


if __name__ == "__main__":
    if os.environ.get("NAROCATALOG_RUNTIME"):
        _migrate()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")
