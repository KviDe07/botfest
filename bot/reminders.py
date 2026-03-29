import asyncio
import html
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError

from .config import (
    EVENT_REMINDER_SNIPPETS,
    EVENT_START_DATES,
    REMINDER_EVENTS,
    REMINDER_HOUR_MSK,
)
from .storage import add_reminder_key, load_registrations, load_reminder_keys

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


def _collect_recipients_tomorrow(tomorrow: date) -> list[tuple[int, str]]:
    reminder_set = frozenset(REMINDER_EVENTS)
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str]] = []
    for r in load_registrations():
        ev = r.get("event")
        if ev not in reminder_set:
            continue
        dates = EVENT_START_DATES.get(ev)
        if not dates or tomorrow not in dates:
            continue
        uid = r.get("user_id")
        if uid is None:
            continue
        pair = (int(uid), ev)
        if pair in seen:
            continue
        seen.add(pair)
        out.append(pair)
    return out


async def _send_tomorrow_reminders(bot: Bot) -> None:
    tomorrow = datetime.now(MSK).date() + timedelta(days=1)
    sent_keys = load_reminder_keys()
    recipients = _collect_recipients_tomorrow(tomorrow)
    date_label = _format_ru_date(tomorrow)
    for user_id, event in recipients:
        idem = f"{user_id}:{event}:{tomorrow.isoformat()}"
        if idem in sent_keys:
            continue
        snippet = EVENT_REMINDER_SNIPPETS.get(event, "").strip()
        body = (
            "Здравствуйте! Завтра, "
            f"<b>{html.escape(date_label)}</b>, состоится мероприятие "
            f"«<b>{html.escape(event)}</b>»."
        )
        if snippet:
            body += f"\n\n{snippet}"
        body += "\n\nЖдём вас на фестивале!"
        try:
            await bot.send_message(user_id, body, parse_mode="HTML")
            add_reminder_key(idem)
            sent_keys.add(idem)
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            logger.warning("Reminder skipped: user %s blocked the bot", user_id)
        except (TelegramBadRequest, TelegramAPIError) as e:
            logger.warning("Reminder failed for user %s: %s", user_id, e)


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
