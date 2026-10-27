"""Local demo API for the Fundly AI Marketing Agent dashboard."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.database import SessionFactory, get_session
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
from app.services.content_generator import (
    AIConfigurationError,
    AIInvalidResponseError,
    AIProviderError,
    AIProviderTimeoutError,
    ContentGenerator,
)
from app.services.draft_repository import DraftRepository, DraftVersionConflict

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_draft_repository(request: Request) -> DraftRepository:
    return request.app.state.draft_repository


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Report that the local API process is ready."""
    return HealthResponse(status="ok", mode="demo")


@router.get(
    "/api/dashboard/overview",
    response_model=OverviewResponse,
    tags=["dashboard"],
    summary="Get demo dashboard metrics for the Fundly brand",
)
async def get_overview() -> OverviewResponse:
    """Return fictional, clearly marked overview metrics."""
    return OverviewResponse.model_validate(OVERVIEW)


@router.get("/api/campaigns", response_model=CampaignListResponse, tags=["campaigns"])
async def get_campaigns() -> CampaignListResponse:
    """Return the in-memory sample campaign list."""
    return CampaignListResponse(items=CAMPAIGNS, total=len(CAMPAIGNS))


@router.get("/api/content", response_model=ContentListResponse, tags=["content"])
async def get_content() -> ContentListResponse:
    """Return the in-memory sample content list."""
    return ContentListResponse(items=CONTENT, total=len(CONTENT))


@router.post(
    "/api/content/generate",
    response_model=GeneratedContent,
    tags=["content"],
    summary="Generate an AI marketing draft for the Fundly brand",
)
async def generate_ai_content(request: ContentGenerationRequest, http_request: Request) -> GeneratedContent:
    """Generate validated content through the configured server-side AI provider."""
    generator: ContentGenerator = http_request.app.state.content_generator
    try:
        return await generator.generate(request)
    except AIConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="AI content generation is not configured. Check GEMINI_API_KEY and GEMINI_MODEL in api/.env.",
        ) from exc
    except AIProviderTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="The AI provider timed out. Please try again.",
        ) from exc
    except AIInvalidResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned content that could not be validated. Please retry.",
        ) from exc
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI provider request failed. Please try again later.",
        ) from exc


@router.get("/api/drafts", response_model=DraftListResponse, tags=["drafts"])
def list_drafts(
    session: Session = Depends(get_session),
    repository: DraftRepository = Depends(_get_draft_repository),
) -> DraftListResponse:
    """List saved drafts from persistent storage."""
    items = repository.list(session)
    return DraftListResponse(items=items, total=len(items))


@router.post(
    "/api/drafts",
    response_model=DraftResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["drafts"],
)
def create_draft(
    request: SaveDraftRequest,
    session: Session = Depends(get_session),
    repository: DraftRepository = Depends(_get_draft_repository),
) -> DraftResponse:
    """Save an editable draft in the database."""
    return repository.create(session, request)


@router.patch("/api/drafts/{draft_id}", response_model=DraftResponse, tags=["drafts"])
def update_draft(
    draft_id: str,
    request: DraftUpdateRequest,
    session: Session = Depends(get_session),
    repository: DraftRepository = Depends(_get_draft_repository),
) -> DraftResponse:
    """Update text or status; approval never triggers publishing."""
    changes = request.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide caption, hashtags, or status to update")
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Draft fields cannot be set to null")

    try:
        updated = repository.update(session, draft_id, changes)
    except DraftVersionConflict as exc:
        raise HTTPException(status_code=409, detail="Draft changed concurrently; reload and retry") from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' was not found")
    return updated


def _log_database_failure(context: str, error: Exception) -> None:
    original = getattr(error, "orig", error)
    driver_code = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    logger.error(
        "Database %s failed (exception=%s, sqlstate=%s)",
        context,
        type(error).__name__,
        driver_code or "unavailable",
    )


def create_app(
    session_factory: sessionmaker[Session] | None = None,
    repository: DraftRepository | None = None,
    content_generator: ContentGenerator | None = None,
) -> FastAPI:
    """Create an app with an injectable session factory for isolated tests."""
    application = FastAPI(
        title="Fundly AI Marketing Agent API",
        description=(
            "Dashboard metrics and scheduled content are sample data. Content generation uses "
            "a configured server-side AI provider; approval does not publish or post content."
        ),
        version="0.2.0",
    )
    application.state.session_factory = session_factory or SessionFactory
    application.state.draft_repository = repository or DraftRepository()
    application.state.content_generator = content_generator or ContentGenerator()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )
    application.include_router(router)

    @application.exception_handler(OperationalError)
    async def database_unavailable(_request: Request, error: OperationalError) -> JSONResponse:
        _log_database_failure("connection", error)
        return JSONResponse(status_code=503, content={"detail": "Draft storage is temporarily unavailable"})

    @application.exception_handler(IntegrityError)
    async def database_integrity_conflict(_request: Request, error: IntegrityError) -> JSONResponse:
        _log_database_failure("constraint", error)
        return JSONResponse(status_code=409, content={"detail": "Draft could not be saved because of a data conflict"})

    @application.exception_handler(DBAPIError)
    async def database_driver_error(_request: Request, error: DBAPIError) -> JSONResponse:
        _log_database_failure("operation", error)
        if error.connection_invalidated:
            return JSONResponse(status_code=503, content={"detail": "Draft storage is temporarily unavailable"})
        return JSONResponse(status_code=500, content={"detail": "Draft storage operation failed"})

    @application.exception_handler(SQLAlchemyError)
    async def database_internal_error(_request: Request, error: SQLAlchemyError) -> JSONResponse:
        _log_database_failure("operation", error)
        return JSONResponse(status_code=500, content={"detail": "Draft storage operation failed"})

    return application


app = create_app()
