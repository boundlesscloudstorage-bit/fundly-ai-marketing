"""Validated response schemas for the demonstration API."""

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(StrictModel):
    status: str
    mode: str


class Metric(StrictModel):
    label: str
    value: str
    change: str
    is_demo: bool = True


class OverviewResponse(StrictModel):
    brand_id: str
    brand_name: str
    period: str
    metrics: list[Metric]
    is_demo: bool = True


class Campaign(StrictModel):
    id: str
    brand_id: str
    name: str
    channel: str
    status: str
    progress: int = Field(ge=0, le=100)
    target_date: str
    is_demo: bool = True


class CampaignListResponse(StrictModel):
    items: list[Campaign]
    total: int = Field(ge=0)
    is_demo: bool = True


class ContentItem(StrictModel):
    id: str
    brand_id: str
    channel: str
    title: str
    body: str
    status: str
    scheduled_for: str
    is_ai_generated_example: bool = True


class ContentListResponse(StrictModel):
    items: list[ContentItem]
    total: int = Field(ge=0)
    is_demo: bool = True
