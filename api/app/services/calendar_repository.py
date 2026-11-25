"""Persistent local calendar entries created from approved drafts."""

from __future__ import annotations

from datetime import timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db_models import CalendarRecord, DraftRecord
from app.models import CalendarEntry, ScheduleCreateRequest, ScheduleUpdateRequest


class CalendarDraftNotFound(Exception):
    pass


class CalendarDraftNotApproved(Exception):
    pass


class CalendarEntryNotFound(Exception):
    pass


class CalendarEntryAlreadyScheduled(Exception):
    pass


class CalendarRepository:
    def list(self, session: Session) -> list[CalendarEntry]:
        records = session.scalars(
            select(CalendarRecord).order_by(CalendarRecord.scheduled_for.asc(), CalendarRecord.id)
        ).all()
        return [_to_response(record) for record in records]

    def schedule(self, session: Session, request: ScheduleCreateRequest) -> CalendarEntry:
        with session.begin():
            draft = session.get(DraftRecord, request.draft_id)
            if draft is None:
                raise CalendarDraftNotFound
            if draft.status != "approved":
                raise CalendarDraftNotApproved
            existing = session.scalar(select(CalendarRecord).where(CalendarRecord.draft_id == draft.id))
            if existing is not None:
                raise CalendarEntryAlreadyScheduled
            record = CalendarRecord(
                id=f"calendar-{uuid4().hex[:12]}",
                draft_id=draft.id,
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

    def reschedule(self, session: Session, entry_id: str, request: ScheduleUpdateRequest) -> CalendarEntry:
        with session.begin():
            record = session.get(CalendarRecord, entry_id)
            if record is None:
                raise CalendarEntryNotFound
            record.scheduled_for = request.scheduled_for
        return _to_response(record)

    def unschedule(self, session: Session, entry_id: str) -> None:
        with session.begin():
            record = session.get(CalendarRecord, entry_id)
            if record is None:
                raise CalendarEntryNotFound
            session.delete(record)


def _platform_label(platform: str) -> str:
    return {"x": "X", "linkedin": "LinkedIn", "instagram": "Instagram", "facebook": "Facebook"}[platform]


def _to_response(record: CalendarRecord) -> CalendarEntry:
    scheduled = record.scheduled_for
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    return CalendarEntry(
        id=record.id,
        brand_id=record.brand_id,
        channel=record.channel,
        title=record.title,
        body=record.body,
        status=record.status,
        scheduled_for=scheduled.isoformat(),
        is_ai_generated_example=False,
        draft_id=record.draft_id,
    )
