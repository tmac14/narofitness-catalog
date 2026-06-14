"""Bootstrap import path for packages/ordia-core."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_ordia_core() -> Path | None:
    root = Path(__file__).resolve().parents[1]
    core = root / "packages" / "ordia-core"
    if not (core / "ordia" / "config.py").is_file():
        return None
    core_str = str(core)
    if core_str not in sys.path:
        sys.path.insert(0, core_str)
    return core
