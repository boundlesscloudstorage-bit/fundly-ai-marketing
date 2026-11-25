"""Create persistent local calendar entries.

Revision ID: 20261120_03
Revises: 20261120_02
"""

from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261120_03"
down_revision: Union[str, None] = "20261120_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("brand_id", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.CheckConstraint("status = 'Scheduled'", name="ck_calendar_entries_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calendar_entries_brand_id", "calendar_entries", ["brand_id"])
    op.create_index("ix_calendar_entries_scheduled_for", "calendar_entries", ["scheduled_for"])

    entries = sa.table(
        "calendar_entries",
        sa.column("id", sa.String), sa.column("brand_id", sa.String), sa.column("channel", sa.String),
        sa.column("title", sa.String), sa.column("body", sa.Text), sa.column("status", sa.String),
        sa.column("scheduled_for", sa.DateTime), sa.column("is_demo", sa.Boolean),
    )
    op.bulk_insert(entries, [
        {"id": "calendar-001", "brand_id": "fundly", "channel": "Instagram", "title": "Small steps. Big plans.", "body": "Big plans do not need big leaps. Sometimes it is one small step, a little breathing room, and the confidence to keep going.", "status": "Scheduled", "scheduled_for": datetime(2026, 10, 24, 15, 30, tzinfo=timezone.utc), "is_demo": True},
        {"id": "calendar-002", "brand_id": "fundly", "channel": "LinkedIn", "title": "A fresh start, on your terms", "body": "Financial confidence is built in everyday choices that move you closer to what matters.", "status": "Scheduled", "scheduled_for": datetime(2026, 10, 27, 18, 0, tzinfo=timezone.utc), "is_demo": True},
    ])


def downgrade() -> None:
    op.drop_index("ix_calendar_entries_scheduled_for", table_name="calendar_entries")
    op.drop_index("ix_calendar_entries_brand_id", table_name="calendar_entries")
    op.drop_table("calendar_entries")
