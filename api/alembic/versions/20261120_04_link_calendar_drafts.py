"""Link local calendar entries to drafts and enforce one schedule per draft.

Revision ID: 20261120_04
Revises: 20261120_03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261120_04"
down_revision: Union[str, None] = "20261120_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("calendar_entries", sa.Column("draft_id", sa.String(length=36), nullable=True))
    op.create_index("ix_calendar_entries_draft_id", "calendar_entries", ["draft_id"])
    op.create_index("uq_calendar_entries_draft_id", "calendar_entries", ["draft_id"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_calendar_entries_draft_id", table_name="calendar_entries")
    op.drop_index("ix_calendar_entries_draft_id", table_name="calendar_entries")
    op.drop_column("calendar_entries", "draft_id")
