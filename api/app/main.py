"""Local demo API for the Fundly AI Marketing Agent dashboard."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.mock_data import CAMPAIGNS, CONTENT, OVERVIEW
from app.models import CampaignListResponse, ContentListResponse, HealthResponse, OverviewResponse

app = FastAPI(
    title="Fundly AI Marketing Agent API",
    description=(
        "Local demonstration API. All responses are mock data; no AI or social "
        "provider is connected and no content can be published."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Report that the local API process is ready."""
    return HealthResponse(status="ok", mode="demo")


@app.get(
    "/api/dashboard/overview",
    response_model=OverviewResponse,
    tags=["dashboard"],
    summary="Get demo dashboard metrics for the Fundly brand",
)
async def get_overview() -> OverviewResponse:
    """Return fictional, clearly marked overview metrics."""
    return OverviewResponse.model_validate(OVERVIEW)


@app.get(
    "/api/campaigns",
    response_model=CampaignListResponse,
    tags=["campaigns"],
    summary="List demo campaigns",
)
async def get_campaigns() -> CampaignListResponse:
    """Return the in-memory sample campaign list."""
    return CampaignListResponse(items=CAMPAIGNS, total=len(CAMPAIGNS))


@app.get(
    "/api/content",
    response_model=ContentListResponse,
    tags=["content"],
    summary="List demo scheduled content and drafts",
)
async def get_content() -> ContentListResponse:
    """Return the in-memory sample content list."""
    return ContentListResponse(items=CONTENT, total=len(CONTENT))
