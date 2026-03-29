import json
import os
from typing import Any

from .config import DATA_FILE, REMINDERS_SENT_FILE, USERS_FILE


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _load(path: str, default: Any) -> Any:
    _ensure_parent_dir(path)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save(data: Any, path: str) -> None:
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_registrations() -> list[dict]:
    return _load(DATA_FILE, [])


def get_registrations_for_user(user_id: int) -> list[dict]:
    return [r for r in load_registrations() if r.get("user_id") == user_id]


def save_registrations(data: list[dict]) -> None:
    _save(data, DATA_FILE)


def load_users() -> dict[str, dict]:
    return _load(USERS_FILE, {})


def save_users(data: dict[str, dict]) -> None:
    _save(data, USERS_FILE)


def get_user_profile(user_id: int) -> dict | None:
    return load_users().get(str(user_id))


def save_user_profile(user_id: int, name: str, contact: str) -> None:
    users = load_users()
    users[str(user_id)] = {"name": name, "contact": contact}
    save_users(users)


def load_reminder_keys() -> set[str]:
    raw = _load(REMINDERS_SENT_FILE, {"keys": []})
    return set(raw.get("keys", []))


def add_reminder_key(key: str) -> None:
    keys = load_reminder_keys()
    keys.add(key)
    _save({"keys": sorted(keys)}, REMINDERS_SENT_FILE)
