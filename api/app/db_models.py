"""SQLAlchemy persistence models."""

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DraftRecord(Base):
    __tablename__ = "drafts"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'approved')", name="ck_drafts_status"),
        CheckConstraint(
            "platform IN ('x', 'linkedin', 'instagram', 'facebook')",
            name="ck_drafts_platform",
        ),
        CheckConstraint("character_count >= 0", name="ck_drafts_character_count"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brand_id: Mapped[str] = mapped_column(String(80), nullable=False, default="fundly", index=True)
    topic: Mapped[str] = mapped_column(String(160), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    objective: Mapped[str] = mapped_column(String(40), nullable=False)
    tone: Mapped[str] = mapped_column(String(30), nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_demo_generated: Mapped[bool] = mapped_column(nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CampaignRecord(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('Instagram', 'LinkedIn', 'X', 'Facebook', 'Email')",
            name="ck_campaigns_channel",
        ),
        CheckConstraint(
            "status IN ('Planning', 'In progress')",
            name="ck_campaigns_status",
        ),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_campaigns_progress"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brand_id: Mapped[str] = mapped_column(String(80), nullable=False, default="fundly", index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    objective: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Planning", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_date: Mapped[str] = mapped_column(String(10), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class CalendarRecord(Base):
    __tablename__ = "calendar_entries"
    __table_args__ = (
        CheckConstraint("status = 'Scheduled'", name="ck_calendar_entries_status"),
        Index("uq_calendar_entries_draft_id", "draft_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    draft_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    brand_id: Mapped[str] = mapped_column(String(80), nullable=False, default="fundly", index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Scheduled")
    scheduled_for: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
