"""Validated request and response schemas for the demonstration API."""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class ActivityItem(StrictModel):
    id: str
    kind: Literal["campaign", "draft", "calendar"]
    title: str
    detail: str
    occurred_at: str
    is_demo: bool = True


class ActivityListResponse(StrictModel):
    items: list[ActivityItem]
    total: int = Field(ge=0)
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


CampaignChannel = Literal["Instagram", "LinkedIn", "X", "Facebook", "Email"]
CampaignObjective = Literal["awareness", "education", "consideration", "engagement"]


class CampaignCreateRequest(StrictModel):
    name: str = Field(min_length=3, max_length=80)
    channel: CampaignChannel
    objective: CampaignObjective
    target_date: date

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("campaign name must contain at least 3 non-whitespace characters")
        if len(cleaned) > 80:
            raise ValueError("campaign name must contain at most 80 characters")
        return cleaned

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("target_date cannot be in the past")
        return value


class CampaignUpdateRequest(StrictModel):
    name: str | None = Field(default=None, min_length=3, max_length=80)
    channel: CampaignChannel | None = None
    objective: CampaignObjective | None = None
    target_date: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("campaign name must contain at least 3 non-whitespace characters")
        return cleaned

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, value: date | None) -> date | None:
        return value


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


class CalendarEntry(ContentItem):
    draft_id: str | None = None


class CalendarListResponse(StrictModel):
    items: list[CalendarEntry]
    total: int = Field(ge=0)
    is_demo: bool = True


class ScheduleCreateRequest(StrictModel):
    draft_id: str = Field(min_length=1, max_length=36)
    scheduled_for: datetime

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_for(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("scheduled_for must include a timezone")
        if value <= datetime.now(value.tzinfo):
            raise ValueError("scheduled_for must be in the future")
        return value


class ScheduleUpdateRequest(StrictModel):
    scheduled_for: datetime

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_for(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("scheduled_for must include a timezone")
        if value <= datetime.now(value.tzinfo):
            raise ValueError("scheduled_for must be in the future")
        return value


Platform = Literal["x", "linkedin", "instagram", "facebook"]
Objective = Literal["brand_awareness", "engagement", "education", "product_promotion"]
Tone = Literal["professional", "inspiring", "friendly", "persuasive"]
DraftStatus = Literal["draft", "approved"]


class ContentGenerationRequest(StrictModel):
    topic: str = Field(min_length=3, max_length=160)
    platform: Platform
    objective: Objective
    tone: Tone
    keywords: str | None = Field(default=None, max_length=240)

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        return _normalize_marketing_input(value, "topic")

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_marketing_input(value, "keywords", allow_empty=True)


class GeneratedContent(StrictModel):
    topic: str
    caption: str = Field(min_length=1, max_length=2800)
    hashtags: list[str] = Field(max_length=8)
    platform: Platform
    objective: Objective
    tone: Tone
    character_count: int = Field(ge=0)
    is_demo_generated: bool = False

    @field_validator("caption")
    @classmethod
    def validate_caption(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("caption must not be blank")
        _reject_unsupported_claims(cleaned, "caption")
        return cleaned

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, values: list[str]) -> list[str]:
        return _normalize_hashtags(values)

    @model_validator(mode="after")
    def validate_character_count(self) -> "GeneratedContent":
        if self.character_count != len(self.caption):
            raise ValueError("character_count must match caption length")
        return self


class SaveDraftRequest(StrictModel):
    topic: str = Field(min_length=3, max_length=160)
    caption: str = Field(min_length=1, max_length=2800)
    hashtags: list[str] = Field(max_length=8)
    platform: Platform
    objective: Objective
    tone: Tone
    is_demo_generated: bool = True

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        return _normalize_marketing_input(value, "topic")

    @field_validator("caption")
    @classmethod
    def normalize_caption(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("caption must not be blank")
        _reject_unsupported_claims(cleaned, "caption")
        return cleaned

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, values: list[str]) -> list[str]:
        return _normalize_hashtags(values)


class DraftUpdateRequest(StrictModel):
    caption: str | None = Field(default=None, min_length=1, max_length=2800)
    hashtags: list[str] | None = Field(default=None, max_length=8)
    status: DraftStatus | None = None

    @field_validator("caption")
    @classmethod
    def normalize_caption(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("caption must not be blank")
        _reject_unsupported_claims(cleaned, "caption")
        return cleaned

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return values
        return _normalize_hashtags(values)


class DraftResponse(StrictModel):
    id: str
    brand_id: str = "fundly"
    topic: str
    caption: str
    hashtags: list[str]
    platform: Platform
    objective: Objective
    tone: Tone
    character_count: int = Field(ge=0)
    status: DraftStatus
    created_at: str
    updated_at: str
    is_demo_generated: bool = True


class DraftListResponse(StrictModel):
    items: list[DraftResponse]
    total: int = Field(ge=0)
    is_demo: bool = True


def _normalize_marketing_input(value: str, field_name: str, allow_empty: bool = False) -> str:
    cleaned = " ".join(value.split())
    if not cleaned and not allow_empty:
        raise ValueError(f"{field_name} must not be blank")
    if field_name == "topic" and len(cleaned) < 3:
        raise ValueError("topic must contain at least 3 non-whitespace characters")
    if cleaned:
        _reject_unsupported_claims(cleaned, field_name)
    return cleaned


def _reject_unsupported_claims(value: str, field_name: str) -> None:
    unsupported_claim = re.compile(
        r"\b(?:guarantee(?:d)?\s+(?:returns?|profits?|income|wealth|growth|success|results?)|"
        r"risk[- ]free|no[- ]risk|zero[- ]risk|double\s+your\s+money|beat\s+the\s+market|"
        r"(?:can't|cannot|never)\s+lose|get\s+rich(?:\s+quick)?|easy\s+money|instant\s+wealth|"
        r"100%\s+(?:return|profit))\b",
        re.IGNORECASE,
    )
    compact_claim = re.compile(
        r"#?(?:guarantee(?:d)?(?:returns?|profits?|income|wealth|growth|success|results?)|"
        r"riskfree|norisk|zerorisk|doubleyourmoney|beatmarket|cantlose|cannotlose|neverlose|"
        r"getrich(?:quick)?|easymoney|instantwealth)",
        re.IGNORECASE,
    )
    unsupported_performance_figure = re.compile(
        r"\b(?:"
        r"\d+(?:\.\d+)?\s*%\s*(?:(?:annual(?:ized)?|yearly|monthly)\s+)?"
        r"(?:returns?|profits?|gains?|growth|performance)|"
        r"(?:returns?|profits?|gains?|growth|performance)\s+(?:of\s+)?\d+(?:\.\d+)?\s*%|"
        r"(?:returned|grew|increased|gained)\s+(?:by\s+)?\d+(?:\.\d+)?\s*%|"
        r"(?:returned|earned|generated|delivered)\s+\d+(?:\.\d+)?\s*%\s+(?:returns?|profits?|gains?)|"
        r"(?:returned|earned|generated|delivered)\s+\$\s*\d[\d,]*(?:\.\d{1,2})?"
        r")(?![A-Za-z0-9_])",
        re.IGNORECASE,
    )
    if (
        unsupported_claim.search(value)
        or compact_claim.search(value.replace(" ", ""))
        or unsupported_performance_figure.search(value)
    ):
        raise ValueError(f"Remove guaranteed-return or unsupported investment claims from {field_name}")


def _normalize_hashtags(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        tag = value.strip()
        if not re.fullmatch(r"#[A-Za-z0-9_]{1,40}", tag):
            raise ValueError("hashtags must start with # and contain only letters, numbers, or underscores")
        _reject_unsupported_claims(tag, "hashtags")
        normalized.append(tag)
    return normalized
