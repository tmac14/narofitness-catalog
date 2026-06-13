from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import (
    DEFAULT_IVA,
    DEFAULT_IVA_RATE,
    DEFAULT_TEMPLATE,
    IVA_KEY,
    IVA_RATE_KEY,
    LOGO_KEY,
    TEMPLATE_KEY,
)
from app.database import get_db
from app.models import AppSetting
from app.schemas import SettingsOut, SettingsPatch
from app.services.media import media_url

router = APIRouter(prefix="/settings", tags=["settings"])


async def _get_setting(db: AsyncSession, key: str, default: str) -> str:
    row = await db.get(AppSetting, key)
    return row.value if row else default


async def _set_setting(db: AsyncSession, key: str, value: str) -> None:
    row = await db.get(AppSetting, key)
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))


async def _build_settings_out(db: AsyncSession) -> SettingsOut:
    iva = await _get_setting(db, IVA_KEY, DEFAULT_IVA)
    rate = await _get_setting(db, IVA_RATE_KEY, DEFAULT_IVA_RATE)
    template = await _get_setting(db, TEMPLATE_KEY, DEFAULT_TEMPLATE)
    logo_path = await _get_setting(db, LOGO_KEY, "")
    logo_url = media_url(logo_path) if logo_path else None
    show_iva = await _get_setting(db, "show_iva_column", "true")
    return SettingsOut(
        iva_disclaimer=iva,
        catalog_logo_url=logo_url,
        iva_rate_percent=rate,
        catalog_template=template,
        show_iva_column=show_iva.lower() == "true",
    )


@router.get("", response_model=SettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)) -> SettingsOut:
    return await _build_settings_out(db)


@router.patch("", response_model=SettingsOut)
async def patch_settings(body: SettingsPatch, db: AsyncSession = Depends(get_db)) -> SettingsOut:
    if body.iva_disclaimer is not None:
        await _set_setting(db, IVA_KEY, body.iva_disclaimer)
    if body.iva_rate_percent is not None:
        await _set_setting(db, IVA_RATE_KEY, body.iva_rate_percent)
    if body.catalog_template is not None:
        await _set_setting(db, TEMPLATE_KEY, body.catalog_template)
    if body.show_iva_column is not None:
        await _set_setting(db, "show_iva_column", "true" if body.show_iva_column else "false")
    await db.commit()
    return await _build_settings_out(db)


@router.post("/logo", response_model=SettingsOut)
async def upload_logo(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> SettingsOut:
    branding = Path(settings.data_dir) / "branding"
    branding.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "logo.png").suffix.lower() or ".png"
    dest = branding / f"logo{ext}"
    content = await file.read()
    dest.write_bytes(content)
    rel = f"branding/logo{ext}"
    await _set_setting(db, LOGO_KEY, rel)
    await db.commit()
    return await _build_settings_out(db)
