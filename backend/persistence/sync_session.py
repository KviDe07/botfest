"""Synchronous engine for Alembic and CLI scripts."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_sync_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    if "+asyncpg" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_sync_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(get_sync_database_url(), echo=os.getenv("SQL_ECHO", "").lower() in ("1", "true"))
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def sync_session() -> Session:
    if _SessionLocal is None:
        get_sync_engine()
    assert _SessionLocal is not None
    return _SessionLocal()
