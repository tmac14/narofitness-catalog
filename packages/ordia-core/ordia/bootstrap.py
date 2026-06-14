"""Locate and import ordia-core from consumer repositories."""

from __future__ import annotations

import sys
from pathlib import Path


def ordia_core_src() -> Path | None:
    start = Path.cwd().resolve()
    for directory in (start, *start.parents):
        candidate = directory / "packages" / "ordia-core"
        if (candidate / "ordia" / "config.py").is_file():
            return candidate
    return None


def ensure_ordia_core() -> Path | None:
    core = ordia_core_src()
    if core is None:
        return None
    core_str = str(core)
    if core_str not in sys.path:
        sys.path.insert(0, core_str)
    return core


def repo_root_from_core() -> Path | None:
    core = ordia_core_src()
    return core.parent.parent if core else None
