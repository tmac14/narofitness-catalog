"""Bootstrap import path for ordia-core (pip first, dev fallbacks)."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_ordia_core() -> Path | None:
    try:
        import ordia  # noqa: F401

        return Path(ordia.__file__).resolve().parent.parent
    except ImportError:
        pass

    root = Path(__file__).resolve().parents[1]
    for candidate in (
        root.parent / "ordia-package" / "packages" / "ordia-core",
        root / "packages" / "ordia-core",
    ):
        if (candidate / "ordia" / "config.py").is_file():
            core_str = str(candidate)
            if core_str not in sys.path:
                sys.path.insert(0, core_str)
            return candidate
    return None
