"""Backup and restore application data."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings

APP_VERSION = "0.1.0"


def _pg_bin(name: str) -> str:
    custom = os.getenv("PG_BIN_DIR")
    if custom:
        p = Path(custom) / name
        if p.is_file():
            return str(p)
    return name


def _database_name_from_url(url: str) -> str:
    parsed = urlparse(url.replace("+asyncpg", ""))
    return (parsed.path or "/narocatalog").lstrip("/") or "narocatalog"


def create_backup_zip() -> Path:
    data = Path(settings.data_dir)
    backups = data / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_path = backups / f"narocatalog_backup_{ts}.zip"
    dump_path = backups / f"dump_{ts}.custom"

    db_url = settings.database_url.replace("+asyncpg", "")
    env = os.environ.copy()
    if "PGPASSWORD" not in env and "narocatalog:" in db_url:
        env["PGPASSWORD"] = "narocatalog"

    subprocess.run(
        [_pg_bin("pg_dump"), "-Fc", "-f", str(dump_path), db_url],
        check=True,
        env=env,
        capture_output=True,
    )

    manifest = {
        "app_version": APP_VERSION,
        "created_at": ts,
        "database": _database_name_from_url(settings.database_url),
    }

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(dump_path, "database.dump")
        dump_path.unlink(missing_ok=True)
        images = data / "images"
        if images.is_dir():
            for f in images.rglob("*"):
                if f.is_file():
                    zf.write(f, f"images/{f.relative_to(images).as_posix()}")
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return zip_path


def restore_backup_zip(zip_path: Path) -> None:
    data = Path(settings.data_dir)
    extract_dir = data / "backups" / "_restore_tmp"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    manifest_path = extract_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Invalid backup: missing manifest.json")

    dump_path = extract_dir / "database.dump"
    if dump_path.is_file():
        db_url = settings.database_url.replace("+asyncpg", "")
        env = os.environ.copy()
        if "PGPASSWORD" not in env:
            env["PGPASSWORD"] = "narocatalog"
        subprocess.run(
            [_pg_bin("pg_restore"), "--clean", "--if-exists", "-d", db_url, str(dump_path)],
            check=True,
            env=env,
            capture_output=True,
        )

    src_images = extract_dir / "images"
    if src_images.is_dir():
        dest = data / "images"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src_images, dest)

    shutil.rmtree(extract_dir, ignore_errors=True)
