# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent.parent
API = ROOT / "apps" / "api"
TEMPLATES = API / "app" / "pdf" / "templates"
ASSETS = API / "app" / "assets"

a = Analysis(
    [str(API / "run_engine.py")],
    pathex=[str(API)],
    binaries=[],
    datas=[
        (str(TEMPLATES), "app/pdf/templates"),
        (str(ASSETS), "app/assets"),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "weasyprint",
        "weasyprint.css",
        "weasyprint.html",
        "weasyprint.pdf",
        "playwright",
        "playwright.sync_api",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="catalog-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
