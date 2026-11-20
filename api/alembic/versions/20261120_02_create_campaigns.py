"""Create persistent campaigns table and demo seed records.

Revision ID: 20261120_02
Revises: 20261026_01
"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261120_02"
down_revision: Union[str, None] = "20261026_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("brand_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("objective", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.String(length=10), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "channel IN ('Instagram', 'LinkedIn', 'X', 'Facebook', 'Email')",
            name="ck_campaigns_channel",
        ),
        sa.CheckConstraint("status IN ('Planning', 'In progress')", name="ck_campaigns_status"),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_campaigns_progress"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaigns_brand_id", "campaigns", ["brand_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_created_at", "campaigns", ["created_at"])

    campaigns = sa.table(
        "campaigns",
        sa.column("id", sa.String),
        sa.column("brand_id", sa.String),
        sa.column("name", sa.String),
        sa.column("channel", sa.String),
        sa.column("objective", sa.String),
        sa.column("status", sa.String),
        sa.column("progress", sa.Integer),
        sa.column("target_date", sa.String),
        sa.column("is_demo", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    seed = [
        ("camp-001", "A little more room to grow", "Instagram", "awareness", "In progress", 72, "2026-10-28"),
        ("camp-002", "Make payday feel lighter", "LinkedIn", "education", "In progress", 48, "2026-10-30"),
        ("camp-003", "Your next chapter starts here", "Email", "consideration", "Planning", 26, "2026-11-04"),
    ]
    op.bulk_insert(
        campaigns,
        [
            {
                "id": campaign_id,
                "brand_id": "fundly",
                "name": name,
                "channel": channel,
                "objective": objective,
                "status": status,
                "progress": progress,
                "target_date": target_date,
                "is_demo": True,
                "created_at": datetime(2026, 1, 1, 0, 3 - index),
                "updated_at": datetime(2026, 1, 1, 0, 3 - index),
            }
            for index, (campaign_id, name, channel, objective, status, progress, target_date) in enumerate(seed)
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_campaigns_created_at", table_name="campaigns")
    op.drop_index("ix_campaigns_status", table_name="campaigns")
    op.drop_index("ix_campaigns_brand_id", table_name="campaigns")
    op.drop_table("campaigns")
