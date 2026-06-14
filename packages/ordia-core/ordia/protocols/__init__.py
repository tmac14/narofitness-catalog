"""Portable Ordia protocol templates for greenfield projects."""

from pathlib import Path


def protocols_root() -> Path:
    return Path(__file__).resolve().parent
