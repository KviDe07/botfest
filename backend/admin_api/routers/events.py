from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin_api.deps import get_current_user, get_db
from admin_api.schemas import EventCreate, EventOut, EventUpdate, RegistrationModeEnum
from persistence.models import Event, EventDate, Registration, RegistrationMode

router = APIRouter(prefix="/events", tags=["events"])


def _event_to_out(ev: Event) -> EventOut:
    dates = sorted(d.event_date for d in (ev.dates or []))
    return EventOut(
        id=ev.id,
        title=ev.title,
        sort_order=ev.sort_order,
        archived=ev.archived,
        registration_mode=RegistrationModeEnum(ev.registration_mode.value),
        external_url=ev.external_url,
        description_html=ev.description_html,
        reminder_enabled=ev.reminder_enabled,
        reminder_snippet_html=ev.reminder_snippet_html,
        dates=dates,
    )


@router.get("", response_model=list[EventOut])
async def list_events(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
    include_archived: bool = Query(True),
) -> list[EventOut]:
    q = select(Event).options(selectinload(Event.dates)).order_by(Event.sort_order, Event.id)
    if not include_archived:
        q = q.where(Event.archived.is_(False))
    res = await session.execute(q)
    rows = list(res.scalars().unique().all())
    return [_event_to_out(e) for e in rows]


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> EventOut:
    q = select(Event).where(Event.id == event_id).options(selectinload(Event.dates))
    res = await session.execute(q)
    ev = res.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _event_to_out(ev)


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> EventOut:
    exists = await session.execute(select(Event.id).where(Event.title == body.title))
    if exists.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title already exists")
    ev = Event(
        title=body.title,
        sort_order=body.sort_order,
        archived=body.archived,
        registration_mode=RegistrationMode(body.registration_mode.value),
        external_url=body.external_url,
        description_html=body.description_html,
        reminder_enabled=body.reminder_enabled,
        reminder_snippet_html=body.reminder_snippet_html,
    )
    session.add(ev)
    await session.flush()
    for d in body.dates:
        session.add(EventDate(event_id=ev.id, event_date=d))
    q = select(Event).where(Event.id == ev.id).options(selectinload(Event.dates))
    res = await session.execute(q)
    ev2 = res.scalar_one()
    return _event_to_out(ev2)


@router.patch("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    body: EventUpdate,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> EventOut:
    q0 = select(Event).where(Event.id == event_id).options(selectinload(Event.dates))
    res0 = await session.execute(q0)
    ev = res0.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if body.title is not None and body.title != ev.title:
        exists = await session.execute(select(Event.id).where(Event.title == body.title))
        if exists.first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title already exists")
        ev.title = body.title
    if body.sort_order is not None:
        ev.sort_order = body.sort_order
    if body.archived is not None:
        ev.archived = body.archived
    if body.registration_mode is not None:
        ev.registration_mode = RegistrationMode(body.registration_mode.value)
    if body.external_url is not None:
        ev.external_url = body.external_url
    if body.description_html is not None:
        ev.description_html = body.description_html
    if body.reminder_enabled is not None:
        ev.reminder_enabled = body.reminder_enabled
    if body.reminder_snippet_html is not None:
        ev.reminder_snippet_html = body.reminder_snippet_html
    if body.dates is not None:
        await session.execute(delete(EventDate).where(EventDate.event_id == ev.id))
        for d in body.dates:
            session.add(EventDate(event_id=ev.id, event_date=d))
    await session.flush()
    q = select(Event).where(Event.id == ev.id).options(selectinload(Event.dates))
    res = await session.execute(q)
    ev2 = res.scalar_one()
    return _event_to_out(ev2)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> None:
    ev = await session.get(Event, event_id)
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    n = await session.scalar(
        select(func.count()).select_from(Registration).where(Registration.event_id == event_id)
    )
    if n and n > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete event with registrations; archive it instead",
        )
    await session.delete(ev)
