"""Process-local draft storage. Data is cleared when the API restarts."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from app.models import DraftResponse, SaveDraftRequest


class InMemoryDraftStore:
    def __init__(self) -> None:
        self._drafts: dict[str, DraftResponse] = {}
        self._lock = RLock()

    def list(self) -> list[DraftResponse]:
        with self._lock:
            ordered = sorted(self._drafts.values(), key=lambda draft: draft.updated_at, reverse=True)
            return [draft.model_copy(deep=True) for draft in ordered]

    def create(self, request: SaveDraftRequest) -> DraftResponse:
        now = datetime.now(timezone.utc).isoformat()
        draft = DraftResponse(
            id=str(uuid4()),
            topic=request.topic,
            caption=request.caption,
            hashtags=request.hashtags,
            platform=request.platform,
            objective=request.objective,
            tone=request.tone,
            character_count=len(request.caption),
            status="draft",
            created_at=now,
            updated_at=now,
            is_demo_generated=True,
        )
        with self._lock:
            self._drafts[draft.id] = draft
            return draft.model_copy(deep=True)

    def update(self, draft_id: str, changes: dict[str, object]) -> DraftResponse | None:
        with self._lock:
            existing = self._drafts.get(draft_id)
            if existing is None:
                return None

            updates = dict(changes)
            content_changed = any(
                field in updates and updates[field] != getattr(existing, field)
                for field in ("caption", "hashtags")
            )
            caption = updates.get("caption")
            if isinstance(caption, str):
                updates["character_count"] = len(caption)
            if content_changed and existing.status == "approved":
                updates["status"] = "draft"
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated = existing.model_copy(update=updates, deep=True)
            self._drafts[draft_id] = updated
            return updated.model_copy(deep=True)

    def clear(self) -> None:
        """Clear process-local records; exposed for isolated tests only."""
        with self._lock:
            self._drafts.clear()


draft_store = InMemoryDraftStore()
