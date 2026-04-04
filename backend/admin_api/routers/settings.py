from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_current_user, get_db
from admin_api.schemas import AppSettingsOut, AppSettingsUpdate
from persistence.models import AppSettings

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_out(row: AppSettings) -> AppSettingsOut:
    return AppSettingsOut(
        reminder_hour_msk=row.reminder_hour_msk,
        schedule_caption=row.schedule_caption,
        schedule_image_path=row.schedule_image_path,
        schedule_missing_message=row.schedule_missing_message,
        admin_brand_title=row.admin_brand_title,
    )


@router.get("", response_model=AppSettingsOut)
async def get_settings(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> AppSettingsOut:
    row = await session.get(AppSettings, 1)
    if row is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Настройки не инициализированы (нет строки app_settings).")
    return _to_out(row)


@router.patch("", response_model=AppSettingsOut)
async def patch_settings(
    body: AppSettingsUpdate,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> AppSettingsOut:
    row = await session.get(AppSettings, 1)
    if row is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Настройки не инициализированы.")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await session.commit()
    await session.refresh(row)
    return _to_out(row)
