import csv
import io

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin_api.deps import get_current_user, get_db
from admin_api.schemas import RegistrationListOut, RegistrationOut
from persistence.models import Registration

router = APIRouter(prefix="/registrations", tags=["registrations"])


def _registration_conditions(event_id: int | None, q: str | None) -> list:
    conditions: list = []
    if event_id is not None:
        conditions.append(Registration.event_id == event_id)
    if q and (t := q.strip()):
        term = f"%{t}%"
        conditions.append(
            or_(
                Registration.name.ilike(term),
                Registration.contact.ilike(term),
                Registration.reg_code.ilike(term),
                Registration.username.ilike(term),
            )
        )
    return conditions


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


@router.get("/export")
async def export_registrations_csv(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
    event_id: int | None = None,
    q: str | None = None,
) -> Response:
    conditions = _registration_conditions(event_id, q)
    stmt = (
        select(Registration)
        .options(selectinload(Registration.event))
        .order_by(Registration.registered_at.desc())
    )
    for c in conditions:
        stmt = stmt.where(c)
    res = await session.execute(stmt)
    rows = list(res.scalars().unique().all())

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Мероприятие", "ФИО", "Контакт", "Username", "Код", "Дата"])
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.event.title if r.event else "?",
                r.name,
                r.contact,
                r.username or "",
                r.reg_code,
                r.registered_at.isoformat(),
            ]
        )
    body = "\ufeff" + buf.getvalue()
    return Response(
        content=body.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="registrations_export.csv"'},
    )


@router.get("", response_model=RegistrationListOut)
async def list_registrations(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
    event_id: int | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> RegistrationListOut:
    conditions = _registration_conditions(event_id, q)

    count_stmt = select(func.count(Registration.id))
    for c in conditions:
        count_stmt = count_stmt.where(c)
    total = int(await session.scalar(count_stmt) or 0)

    du_stmt = select(func.count(func.distinct(Registration.user_id)))
    for c in conditions:
        du_stmt = du_stmt.where(c)
    distinct_users = int(await session.scalar(du_stmt) or 0)

    de_stmt = select(func.count(func.distinct(Registration.event_id)))
    for c in conditions:
        de_stmt = de_stmt.where(c)
    distinct_events = int(await session.scalar(de_stmt) or 0)

    data_stmt = (
        select(Registration)
        .options(selectinload(Registration.event))
        .order_by(Registration.registered_at.desc())
        .limit(limit)
        .offset(offset)
    )
    for c in conditions:
        data_stmt = data_stmt.where(c)
    res = await session.execute(data_stmt)
    items = [_to_out(r) for r in res.scalars().unique().all()]

    return RegistrationListOut(
        items=items,
        total=total,
        distinct_users=distinct_users,
        distinct_events=distinct_events,
        limit=limit,
        offset=offset,
    )
