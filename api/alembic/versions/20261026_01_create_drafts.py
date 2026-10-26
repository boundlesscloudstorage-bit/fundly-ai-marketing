"""Create persistent drafts table.

Revision ID: 20261026_01
Revises:
Create Date: 2026-10-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261026_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("brand_id", sa.String(length=80), nullable=False),
        sa.Column("topic", sa.String(length=160), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.JSON(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("objective", sa.String(length=40), nullable=False),
        sa.Column("tone", sa.String(length=30), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_demo_generated", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'approved')", name="ck_drafts_status"),
        sa.CheckConstraint(
            "platform IN ('x', 'linkedin', 'instagram', 'facebook')",
            name="ck_drafts_platform",
        ),
        sa.CheckConstraint("character_count >= 0", name="ck_drafts_character_count"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drafts_brand_id", "drafts", ["brand_id"])
    op.create_index("ix_drafts_status", "drafts", ["status"])
    op.create_index("ix_drafts_updated_at", "drafts", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_drafts_updated_at", table_name="drafts")
    op.drop_index("ix_drafts_status", table_name="drafts")
    op.drop_index("ix_drafts_brand_id", table_name="drafts")
    op.drop_table("drafts")
