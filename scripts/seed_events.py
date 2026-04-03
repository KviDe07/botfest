"""
Fill events and event_dates from bot/config.py (idempotent upsert by title).

Run after: alembic upgrade head
Requires: DATABASE_URL
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("BOT_TOKEN", "dummy_for_scripts")

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import delete, select

from bot import config as cfg
from persistence.models import Event, EventDate, RegistrationMode
from persistence.sync_session import sync_session


def _mode_for_title(title: str) -> RegistrationMode:
    if title in cfg._REGISTRATION_EXCLUDE:
        return RegistrationMode.none
    if title in cfg.EXTERNAL_REGISTRATIONS:
        return RegistrationMode.external
    return RegistrationMode.internal


def _reminder_for_title(title: str) -> tuple[bool, str | None]:
    if title not in cfg.REMINDER_EVENTS:
        return False, None
    if title not in cfg.EVENT_START_DATES:
        return False, None
    snippet = cfg.EVENT_REMINDER_SNIPPETS.get(title)
    return True, snippet


def main() -> None:
    with sync_session() as session:
        for sort_order, title in enumerate(cfg.EVENTS):
            mode = _mode_for_title(title)
            ext = cfg.EXTERNAL_REGISTRATIONS.get(title)
            desc = cfg.EVENT_DESCRIPTIONS.get(title, "")
            rem_en, rem_snip = _reminder_for_title(title)

            ev = session.execute(select(Event).where(Event.title == title)).scalar_one_or_none()
            if ev is None:
                ev = Event(
                    title=title,
                    sort_order=sort_order,
                    archived=False,
                    registration_mode=mode,
                    external_url=ext,
                    description_html=desc,
                    reminder_enabled=rem_en,
                    reminder_snippet_html=rem_snip,
                )
                session.add(ev)
                session.flush()
            else:
                ev.sort_order = sort_order
                ev.archived = False
                ev.registration_mode = mode
                ev.external_url = ext
                ev.description_html = desc
                ev.reminder_enabled = rem_en
                ev.reminder_snippet_html = rem_snip

            session.execute(delete(EventDate).where(EventDate.event_id == ev.id))
            for d in cfg.EVENT_START_DATES.get(title, []):
                session.add(EventDate(event_id=ev.id, event_date=d))

        session.commit()
    print("seed_events: OK")


if __name__ == "__main__":
    main()
