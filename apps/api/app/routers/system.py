from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.backup import create_backup_zip, restore_backup_zip

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/backup")
async def backup() -> dict:
    try:
        path = create_backup_zip()
        return {"path": str(path), "filename": path.name}
    except Exception as e:
        raise HTTPException(500, f"Backup failed: {e}") from e


@router.get("/backup/latest")
async def download_latest_backup() -> FileResponse:
    from app.config import settings

    backups = Path(settings.data_dir) / "backups"
    files = sorted(backups.glob("narocatalog_backup_*.zip"), reverse=True)
    if not files:
        raise HTTPException(404, "No backups found")
    return FileResponse(files[0], filename=files[0].name, media_type="application/zip")


@router.post("/restore")
async def restore(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> dict:

    from app.config import settings

    tmp = Path(settings.data_dir) / "backups" / f"_upload_{file.filename}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    tmp.write_bytes(content)
    try:
        restore_backup_zip(tmp)
    except Exception as e:
        raise HTTPException(500, f"Restore failed: {e}") from e
    finally:
        tmp.unlink(missing_ok=True)
    return {"status": "restored"}
