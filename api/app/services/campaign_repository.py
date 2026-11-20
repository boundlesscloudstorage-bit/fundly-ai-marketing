"""Database-backed campaign persistence for the Fundly workspace."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import CampaignRecord
from app.models import Campaign, CampaignCreateRequest

_OBJECTIVE_LABELS = {
    "awareness": "Awareness",
    "education": "Education",
    "consideration": "Consideration",
    "engagement": "Engagement",
}


class CampaignRepository:
    """Read and write campaigns using the request-scoped SQLAlchemy session."""

    def list(self, session: Session) -> list[Campaign]:
        records = session.scalars(
            select(CampaignRecord).order_by(CampaignRecord.created_at.desc(), CampaignRecord.id.desc())
        ).all()
        return [_to_response(record) for record in records]

    def create(self, session: Session, request: CampaignCreateRequest) -> Campaign:
        now = datetime.now(timezone.utc)
        record = CampaignRecord(
            id=f"camp-{uuid4().hex[:12]}",
            brand_id="fundly",
            name=request.name,
            channel=request.channel,
            objective=request.objective,
            status="Planning",
            progress=0,
            target_date=request.target_date.isoformat(),
            is_demo=True,
            created_at=now,
            updated_at=now,
        )
        with session.begin():
            session.add(record)
        return _to_response(record)


def _to_response(record: CampaignRecord) -> Campaign:
    return Campaign(
        id=record.id,
        brand_id=record.brand_id,
        name=record.name,
        channel=f"{record.channel} \u00b7 {_OBJECTIVE_LABELS[record.objective]}",
        status=record.status,
        progress=record.progress,
        target_date=record.target_date,
        is_demo=record.is_demo,
    )
