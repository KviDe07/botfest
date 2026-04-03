"""
Import data/registrations.json, users.json, reminders_sent.json into PostgreSQL.

Run after: seed_events
Requires: DATABASE_URL
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("BOT_TOKEN", "dummy_for_scripts")

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import select

from bot.config import DATA_FILE, REMINDERS_SENT_FILE, USERS_FILE
from persistence.models import Event, Registration, ReminderSent, UserProfile
from persistence.sync_session import sync_session


def _parse_dt(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()

    data_dir = args.data_dir
    reg_path = Path(os.getenv("DATA_FILE", data_dir / "registrations.json"))
    users_path = Path(os.getenv("USERS_FILE", data_dir / "users.json"))
    rem_path = Path(os.getenv("REMINDERS_SENT_FILE", data_dir / "reminders_sent.json"))

    regs_raw: list[dict] = []
    if reg_path.exists():
        with open(reg_path, encoding="utf-8") as f:
            regs_raw = json.load(f)
    users_raw: dict = {}
    if users_path.exists():
        with open(users_path, encoding="utf-8") as f:
            users_raw = json.load(f)
    rem_keys: list[str] = []
    if rem_path.exists():
        with open(rem_path, encoding="utf-8") as f:
            rem_raw = json.load(f)
            rem_keys = list(rem_raw.get("keys", []))

    with sync_session() as session:
        title_to_id = {e.title: e.id for e in session.execute(select(Event)).scalars().all()}

        imported_regs = 0
        skipped_regs = 0
        orphans: list[str] = []

        for row in regs_raw:
            title = str(row.get("event", ""))
            eid = title_to_id.get(title)
            if eid is None:
                orphans.append(title)
                continue
            code = str(row.get("reg_code", ""))
            exists = session.execute(select(Registration.id).where(Registration.reg_code == code)).first()
            if exists:
                skipped_regs += 1
                continue
            uid = int(row["user_id"])
            r = Registration(
                user_id=uid,
                username=row.get("username"),
                event_id=eid,
                name=str(row.get("name", "")),
                contact=str(row.get("contact", "")),
                reg_code=code,
                registered_at=_parse_dt(str(row["registered_at"])),
            )
            session.add(r)
            imported_regs += 1

        for uid_str, prof in users_raw.items():
            uid = int(uid_str)
            up = session.get(UserProfile, uid)
            if up is None:
                session.add(
                    UserProfile(
                        telegram_user_id=uid,
                        name=str(prof.get("name", "")),
                        contact=str(prof.get("contact", "")),
                    )
                )
            else:
                up.name = str(prof.get("name", ""))
                up.contact = str(prof.get("contact", ""))

        for key in rem_keys:
            existing = session.execute(select(ReminderSent.id).where(ReminderSent.idempotency_key == key)).first()
            if existing:
                continue
            session.add(ReminderSent(idempotency_key=key))

        session.commit()

    print(f"migrate_json_to_pg: registrations imported={imported_regs} skipped={skipped_regs}")
    if orphans:
        unique = sorted(set(orphans))
        print(f"migrate_json_to_pg: ORPHAN event titles (not in DB): {len(orphans)} rows, unique titles: {unique}")
    print("migrate_json_to_pg: OK")


if __name__ == "__main__":
    main()
