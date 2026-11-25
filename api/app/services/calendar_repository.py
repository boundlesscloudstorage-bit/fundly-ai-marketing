"""Persistent local calendar entries created from approved drafts."""

from __future__ import annotations

from datetime import timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import CalendarRecord, DraftRecord
from app.models import ContentItem, ScheduleCreateRequest


class CalendarDraftNotFound(Exception):
    pass


class CalendarDraftNotApproved(Exception):
    pass


class CalendarRepository:
    def list(self, session: Session) -> list[ContentItem]:
        records = session.scalars(
            select(CalendarRecord).order_by(CalendarRecord.scheduled_for.asc(), CalendarRecord.id)
        ).all()
        return [_to_response(record) for record in records]

    def schedule(self, session: Session, request: ScheduleCreateRequest) -> ContentItem:
        with session.begin():
            draft = session.get(DraftRecord, request.draft_id)
            if draft is None:
                raise CalendarDraftNotFound
            if draft.status != "approved":
                raise CalendarDraftNotApproved
            record = CalendarRecord(
                id=f"calendar-{uuid4().hex[:12]}",
                brand_id=draft.brand_id,
                channel=_platform_label(draft.platform),
                title=draft.topic,
                body=draft.caption,
                status="Scheduled",
                scheduled_for=request.scheduled_for,
                is_demo=True,
            )
            session.add(record)
        return _to_response(record)


def _platform_label(platform: str) -> str:
    return {"x": "X", "linkedin": "LinkedIn", "instagram": "Instagram", "facebook": "Facebook"}[platform]


def _to_response(record: CalendarRecord) -> ContentItem:
    scheduled = record.scheduled_for
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    return ContentItem(
        id=record.id,
        brand_id=record.brand_id,
        channel=record.channel,
        title=record.title,
        body=record.body,
        status=record.status,
        scheduled_for=scheduled.isoformat(),
        is_ai_generated_example=False,
    )
