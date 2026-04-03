from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin_api.deps import get_current_user, get_db
from admin_api.schemas import RegistrationOut
from persistence.models import Registration

router = APIRouter(prefix="/registrations", tags=["registrations"])


def _to_out(r: Registration) -> RegistrationOut:
    return RegistrationOut(
        id=r.id,
        user_id=r.user_id,
        username=r.username,
        event_id=r.event_id,
        event_title=r.event.title if r.event else "?",
        name=r.name,
        contact=r.contact,
        reg_code=r.reg_code,
        registered_at=r.registered_at,
    )


@router.get("", response_model=list[RegistrationOut])
async def list_registrations(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
    event_id: int | None = None,
) -> list[RegistrationOut]:
    q = select(Registration).options(selectinload(Registration.event)).order_by(Registration.registered_at.desc())
    if event_id is not None:
        q = q.where(Registration.event_id == event_id)
    res = await session.execute(q)
    rows = list(res.scalars().unique().all())
    return [_to_out(r) for r in rows]
