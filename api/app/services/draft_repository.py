"""Transactional SQLAlchemy repository for persistent drafts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db_models import DraftRecord
from app.models import DraftResponse, SaveDraftRequest


class DraftVersionConflict(Exception):
    """Raised when a database row changed after it was read for update."""


def _as_response(record: DraftRecord) -> DraftResponse:
    created = record.created_at
    updated = record.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return DraftResponse(
        id=record.id,
        brand_id=record.brand_id,
        topic=record.topic,
        caption=record.caption,
        hashtags=list(record.hashtags),
        platform=record.platform,
        objective=record.objective,
        tone=record.tone,
        character_count=record.character_count,
        status=record.status,
        created_at=created.isoformat(),
        updated_at=updated.isoformat(),
        is_demo_generated=record.is_demo_generated,
    )


class DraftRepository:
    def list(self, session: Session) -> list[DraftResponse]:
        records = session.scalars(
            select(DraftRecord).order_by(DraftRecord.updated_at.desc(), DraftRecord.id)
        ).all()
        return [_as_response(record) for record in records]

    def create(self, session: Session, request: SaveDraftRequest) -> DraftResponse:
        now = datetime.now(timezone.utc)
        record = DraftRecord(
            id=str(uuid4()),
            brand_id="fundly",
            topic=request.topic,
            caption=request.caption,
            hashtags=list(request.hashtags),
            platform=request.platform,
            objective=request.objective,
            tone=request.tone,
            character_count=len(request.caption),
            status="draft",
            created_at=now,
            updated_at=now,
            is_demo_generated=True,
            version=1,
        )
        with session.begin():
            session.add(record)
            session.flush()
            response = _as_response(record)
        return response

    def update(
        self,
        session: Session,
        draft_id: str,
        changes: dict[str, Any],
        *,
        expected_version: int | None = None,
    ) -> DraftResponse | None:
        with session.begin():
            current = session.scalar(select(DraftRecord).where(DraftRecord.id == draft_id))
            if current is None:
                return None
            version = current.version
            guard_version = version if expected_version is None else expected_version

            content_changed = any(
                key in changes and changes[key] != getattr(current, key)
                for key in ("caption", "hashtags")
            )
            values = dict(changes)
            if isinstance(values.get("caption"), str):
                values["character_count"] = len(values["caption"])
            if content_changed and current.status == "approved":
                values["status"] = "draft"
            values.update(
                updated_at=datetime.now(timezone.utc),
                version=guard_version + 1,
            )

            result = session.execute(
                update(DraftRecord)
                .where(DraftRecord.id == draft_id, DraftRecord.version == guard_version)
                .values(**values)
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                raise DraftVersionConflict

            session.expire_all()
            refreshed = session.scalar(select(DraftRecord).where(DraftRecord.id == draft_id))
            assert refreshed is not None
            response = _as_response(refreshed)
        return response
