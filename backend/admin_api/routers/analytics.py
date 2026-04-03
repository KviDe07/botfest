from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_current_user, get_db
from admin_api.schemas import AnalyticsSummary
from persistence.models import Event, Registration

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> AnalyticsSummary:
    total = await session.scalar(select(func.count()).select_from(Registration)) or 0
    unique_users = await session.scalar(
        select(func.count(func.distinct(Registration.user_id))).select_from(Registration)
    ) or 0

    name_norm = func.lower(func.trim(Registration.name))
    unique_names = await session.scalar(
        select(func.count(func.distinct(name_norm)))
        .select_from(Registration)
        .where(name_norm != "")
    ) or 0

    q_ev = (
        select(Event.title, func.count(Registration.id))
        .join(Registration, Registration.event_id == Event.id)
        .group_by(Event.id, Event.title)
        .order_by(Event.title)
    )
    res_ev = await session.execute(q_ev)
    by_event = [{"event_title": row[0], "count": int(row[1])} for row in res_ev.all()]

    day_col = func.date_trunc("day", Registration.registered_at)
    q_day = select(day_col, func.count(Registration.id)).group_by(day_col).order_by(day_col)
    res_day = await session.execute(q_day)
    by_day = []
    for row in res_day.all():
        d, c = row[0], row[1]
        day_str = d.date().isoformat() if d is not None else ""
        by_day.append({"day": day_str, "count": int(c)})

    return AnalyticsSummary(
        total_registrations=int(total),
        unique_users=int(unique_users),
        unique_names=int(unique_names),
        by_event=by_event,
        by_day=by_day,
    )
