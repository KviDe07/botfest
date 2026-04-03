import enum
import datetime as dt
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RegistrationMode(str, enum.Enum):
    none = "none"
    internal = "internal"
    external = "external"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registration_mode: Mapped[RegistrationMode] = mapped_column(
        Enum(RegistrationMode, name="registration_mode_enum", native_enum=False),
        nullable=False,
    )
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reminder_snippet_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    dates: Mapped[list["EventDate"]] = relationship(
        "EventDate", back_populates="event", cascade="all, delete-orphan"
    )
    registrations: Mapped[list["Registration"]] = relationship(
        "Registration", back_populates="event"
    )

    __table_args__ = (UniqueConstraint("title", name="uq_events_title"),)


class EventDate(Base):
    __tablename__ = "event_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    event_date: Mapped[dt.date] = mapped_column("event_date", Date, nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="dates")

    __table_args__ = (UniqueConstraint("event_id", "event_date", name="uq_event_dates_event_date"),)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    contact: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(256), nullable=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    contact: Mapped[str] = mapped_column(String(256), nullable=False)
    reg_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    registered_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="registrations")


class ReminderSent(Base):
    __tablename__ = "reminder_sent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    sent_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
