"""Async data access for the Telegram bot."""

from __future__ import annotations

import datetime as dt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from persistence.models import Event, EventDate, Registration, RegistrationMode, ReminderSent, UserProfile


async def list_active_events_ordered(session: AsyncSession) -> list[Event]:
    q = (
        select(Event)
        .where(Event.archived.is_(False))
        .options(selectinload(Event.dates))
        .order_by(Event.sort_order, Event.id)
    )
    res = await session.execute(q)
    return list(res.scalars().unique().all())


async def list_active_for_info(session: AsyncSession) -> list[Event]:
    return await list_active_events_ordered(session)


async def list_active_for_registration(session: AsyncSession) -> list[Event]:
    all_e = await list_active_events_ordered(session)
    return [e for e in all_e if e.registration_mode != RegistrationMode.none]


async def get_event_by_id(session: AsyncSession, event_id: int) -> Event | None:
    q = select(Event).where(Event.id == event_id).options(selectinload(Event.dates))
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def get_event_by_title_active(session: AsyncSession, title: str) -> Event | None:
    q = select(Event).where(Event.title == title, Event.archived.is_(False))
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def get_registrations_for_user(session: AsyncSession, user_id: int) -> list[Registration]:
    q = (
        select(Registration)
        .where(Registration.user_id == user_id)
        .options(selectinload(Registration.event))
        .order_by(Registration.registered_at)
    )
    res = await session.execute(q)
    return list(res.scalars().all())


async def append_registration(
    session: AsyncSession,
    *,
    user_id: int,
    username: str | None,
    event_id: int,
    name: str,
    contact: str,
    reg_code: str,
    registered_at: dt.datetime,
) -> None:
    session.add(
        Registration(
            user_id=user_id,
            username=username,
            event_id=event_id,
            name=name,
            contact=contact,
            reg_code=reg_code,
            registered_at=registered_at,
        )
    )


async def save_user_profile(session: AsyncSession, user_id: int, name: str, contact: str) -> None:
    up = await session.get(UserProfile, user_id)
    if up is None:
        session.add(UserProfile(telegram_user_id=user_id, name=name, contact=contact))
    else:
        up.name = name
        up.contact = contact


async def get_user_profile(session: AsyncSession, user_id: int) -> UserProfile | None:
    return await session.get(UserProfile, user_id)


async def load_all_registrations_with_events(session: AsyncSession) -> list[Registration]:
    q = select(Registration).options(selectinload(Registration.event))
    res = await session.execute(q)
    return list(res.scalars().all())


async def reminder_events_for_date(session: AsyncSession, target: dt.date) -> list[tuple[Event, dt.date]]:
    """Events that should fire reminders for `target` (tomorrow from scheduler POV)."""
    q = (
        select(Event, EventDate.event_date)
        .join(EventDate, EventDate.event_id == Event.id)
        .where(
            Event.archived.is_(False),
            Event.reminder_enabled.is_(True),
            EventDate.event_date == target,
        )
    )
    res = await session.execute(q)
    out: list[tuple[Event, dt.date]] = []
    for ev, d in res.all():
        out.append((ev, d))
    return out


async def load_registrations_for_reminder(
    session: AsyncSession, event_id: int
) -> list[Registration]:
    q = select(Registration).where(Registration.event_id == event_id)
    res = await session.execute(q)
    return list(res.scalars().all())


async def load_reminder_keys(session: AsyncSession) -> set[str]:
    q = select(ReminderSent.idempotency_key)
    res = await session.execute(q)
    return set(res.scalars().all())


async def add_reminder_key(session: AsyncSession, key: str) -> None:
    session.add(ReminderSent(idempotency_key=key))
