"""app_settings singleton

Revision ID: 002_app_settings
Revises: 001_initial
Create Date: 2026-04-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_app_settings"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reminder_hour_msk", sa.Integer(), nullable=False),
        sa.Column("schedule_caption", sa.Text(), nullable=False),
        sa.Column("schedule_image_path", sa.String(length=1024), nullable=False),
        sa.Column("schedule_missing_message", sa.Text(), nullable=False),
        sa.Column("admin_brand_title", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(
        sa.table(
            "app_settings",
            sa.column("id", sa.Integer),
            sa.column("reminder_hour_msk", sa.Integer),
            sa.column("schedule_caption", sa.Text),
            sa.column("schedule_image_path", sa.String),
            sa.column("schedule_missing_message", sa.Text),
            sa.column("admin_brand_title", sa.String),
        ),
        [
            {
                "id": 1,
                "reminder_hour_msk": 10,
                "schedule_caption": "Расписание мероприятий Фестиваля космонавтики",
                "schedule_image_path": "media/schedule.jpg",
                "schedule_missing_message": "Фото с расписанием пока не загружено.",
                "admin_brand_title": "Botfest Admin",
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("app_settings")
