"""Shim — re-export Ordia config from pip ordia-core."""

from __future__ import annotations

from _ordia_bootstrap import ensure_ordia_core

ensure_ordia_core()

from ordia.config import *  # noqa: F403,E402,F401
