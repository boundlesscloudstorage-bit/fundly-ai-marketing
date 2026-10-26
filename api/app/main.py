"""Local demo API for the Fundly AI Marketing Agent dashboard."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.mock_data import CAMPAIGNS, CONTENT, OVERVIEW
from app.models import (
    CampaignListResponse,
    ContentGenerationRequest,
    ContentListResponse,
    DraftListResponse,
    DraftResponse,
    DraftUpdateRequest,
    GeneratedContent,
    HealthResponse,
    OverviewResponse,
    SaveDraftRequest,
)
from app.services.content_generator import generate_content
from app.services.draft_store import draft_store

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
    allow_methods=["GET", "POST", "PATCH"],
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


@app.post(
    "/api/content/generate",
    response_model=GeneratedContent,
    tags=["content"],
    summary="Generate a deterministic demo marketing draft",
)
async def generate_demo_content(request: ContentGenerationRequest) -> GeneratedContent:
    """Return a template-generated example; no AI provider is called."""
    return generate_content(request)


@app.get(
    "/api/drafts",
    response_model=DraftListResponse,
    tags=["drafts"],
    summary="List process-local saved drafts",
)
async def list_drafts() -> DraftListResponse:
    """List drafts held in memory until the API process restarts."""
    items = draft_store.list()
    return DraftListResponse(items=items, total=len(items))


@app.post(
    "/api/drafts",
    response_model=DraftResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["drafts"],
    summary="Save a generated example as a draft",
)
async def create_draft(request: SaveDraftRequest) -> DraftResponse:
    """Save an editable draft in process-local memory."""
    return draft_store.create(request)


@app.patch(
    "/api/drafts/{draft_id}",
    response_model=DraftResponse,
    tags=["drafts"],
    summary="Edit a saved draft or mark it approved",
)
async def update_draft(draft_id: str, request: DraftUpdateRequest) -> DraftResponse:
    """Update text or status; approval never triggers publishing."""
    changes = request.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide caption, hashtags, or status to update")
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Draft fields cannot be set to null")

    updated = draft_store.update(draft_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' was not found")
    return updated
