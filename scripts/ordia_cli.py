#!/usr/bin/env python3
"""Shim entrypoint for Ordia CLI (pip ordia-core)."""

from __future__ import annotations

from _ordia_bootstrap import ensure_ordia_core

ensure_ordia_core()

from ordia.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
