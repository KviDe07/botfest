import asyncio
import html
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.config import REMINDER_HOUR_MSK
from persistence.models import Event, EventDate, Registration
from persistence.repos import add_reminder_key, load_reminder_keys
from persistence.session import get_session_factory

logger = logging.getLogger(__name__)
MSK = ZoneInfo("Europe/Moscow")

_RU_MONTHS_GEN = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def _format_ru_date(d: date) -> str:
    return f"{d.day} {_RU_MONTHS_GEN[d.month]} {d.year} г."


def _seconds_until_next_reminder_slot() -> float:
    now = datetime.now(MSK)
    run_today = now.replace(hour=REMINDER_HOUR_MSK, minute=0, second=0, microsecond=0)
    if now < run_today:
        next_run = run_today
    else:
        next_run = run_today + timedelta(days=1)
    return max(1.0, (next_run - now).total_seconds())


async def _send_tomorrow_reminders(bot: Bot) -> None:
    tomorrow = datetime.now(MSK).date() + timedelta(days=1)
    factory = get_session_factory()

    async with factory() as session:
        sent_keys = await load_reminder_keys(session)

    q = (
        select(Event)
        .join(EventDate, EventDate.event_id == Event.id)
        .where(
            Event.archived.is_(False),
            Event.reminder_enabled.is_(True),
            EventDate.event_date == tomorrow,
        )
        .options(selectinload(Event.dates))
    )
    async with factory() as session:
        res = await session.execute(q)
        events = list(res.scalars().unique().all())

    date_label = _format_ru_date(tomorrow)

    for ev in events:
        async with factory() as session:
            rres = await session.execute(select(Registration).where(Registration.event_id == ev.id))
            regs = list(rres.scalars().all())

        seen: set[tuple[int, str]] = set()
        for r in regs:
            uid = int(r.user_id)
            pair = (uid, ev.title)
            if pair in seen:
                continue
            seen.add(pair)

            idem = f"{uid}:{ev.title}:{tomorrow.isoformat()}"
            if idem in sent_keys:
                continue

            snippet = (ev.reminder_snippet_html or "").strip()
            body = (
                "Здравствуйте! Завтра, "
                f"<b>{html.escape(date_label)}</b>, состоится мероприятие "
                f"«<b>{html.escape(ev.title)}</b>»."
            )
            if snippet:
                body += f"\n\n{snippet}"
            body += "\n\nЖдём вас на фестивале!"
            try:
                await bot.send_message(uid, body, parse_mode="HTML")
            except TelegramForbiddenError:
                logger.warning("Reminder skipped: user %s blocked the bot", uid)
                continue
            except (TelegramBadRequest, TelegramAPIError) as e:
                logger.warning("Reminder failed for user %s: %s", uid, e)
                continue

            async with factory() as s2:
                await add_reminder_key(s2, idem)
                await s2.commit()
            sent_keys.add(idem)
            await asyncio.sleep(0.05)


async def reminder_scheduler_loop(bot: Bot) -> None:
    logger.info("Reminder scheduler started (MSK hour=%s)", REMINDER_HOUR_MSK)
    while True:
        try:
            delay = _seconds_until_next_reminder_slot()
            await asyncio.sleep(delay)
            await _send_tomorrow_reminders(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Reminder scheduler tick failed")
            await asyncio.sleep(60)
