"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-04-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("registration_mode", sa.String(length=32), nullable=False),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=False),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_snippet_html", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", name="uq_events_title"),
    )
    op.create_index(op.f("ix_events_title"), "events", ["title"], unique=False)

    op.create_table(
        "user_profiles",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("contact", sa.String(length=256), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("telegram_user_id"),
    )

    op.create_table(
        "reminder_sent",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=512), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(op.f("ix_reminder_sent_idempotency_key"), "reminder_sent", ["idempotency_key"], unique=True)

    op.create_table(
        "event_dates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "event_date", name="uq_event_dates_event_date"),
    )
    op.create_index(op.f("ix_event_dates_event_id"), "event_dates", ["event_id"], unique=False)

    op.create_table(
        "registrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=256), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("contact", sa.String(length=256), nullable=False),
        sa.Column("reg_code", sa.String(length=64), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reg_code"),
    )
    op.create_index(op.f("ix_registrations_event_id"), "registrations", ["event_id"], unique=False)
    op.create_index(op.f("ix_registrations_reg_code"), "registrations", ["reg_code"], unique=True)
    op.create_index(op.f("ix_registrations_user_id"), "registrations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_registrations_user_id"), table_name="registrations")
    op.drop_index(op.f("ix_registrations_reg_code"), table_name="registrations")
    op.drop_index(op.f("ix_registrations_event_id"), table_name="registrations")
    op.drop_table("registrations")
    op.drop_index(op.f("ix_event_dates_event_id"), table_name="event_dates")
    op.drop_table("event_dates")
    op.drop_index(op.f("ix_reminder_sent_idempotency_key"), table_name="reminder_sent")
    op.drop_table("reminder_sent")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_events_title"), table_name="events")
    op.drop_table("events")
