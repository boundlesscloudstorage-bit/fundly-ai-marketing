"""Thread-safe, process-local campaign data for the local demonstration API."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from app.mock_data import CAMPAIGNS
from app.models import Campaign, CampaignCreateRequest

_OBJECTIVE_LABELS = {
    "awareness": "Awareness",
    "education": "Education",
    "consideration": "Consideration",
    "engagement": "Engagement",
}


class CampaignStore:
    """Keep sample and newly created campaigns in memory until API restart."""

    def __init__(self, initial_campaigns: list[dict[str, object]] | None = None) -> None:
        self._lock = RLock()
        seed = CAMPAIGNS if initial_campaigns is None else initial_campaigns
        self._campaigns = [Campaign.model_validate(item) for item in seed]

    def list(self) -> list[Campaign]:
        with self._lock:
            return [campaign.model_copy(deep=True) for campaign in self._campaigns]

    def create(self, request: CampaignCreateRequest) -> Campaign:
        campaign = Campaign(
            id=f"camp-{uuid4().hex[:12]}",
            brand_id="fundly",
            name=request.name,
            channel=f"{request.channel} · {_OBJECTIVE_LABELS[request.objective]}",
            status="Planning",
            progress=0,
            target_date=request.target_date.isoformat(),
            is_demo=True,
        )
        with self._lock:
            self._campaigns.insert(0, campaign)
        return campaign.model_copy(deep=True)
