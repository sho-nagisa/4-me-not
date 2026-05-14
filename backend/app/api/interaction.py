from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel

from backend.services.interaction_service import InteractionService
from backend.services.interaction_processing_service import (
    process_interaction_after_save,
)


router = APIRouter(prefix="/interactions", tags=["interaction"])


class InteractionCreateRequest(BaseModel):
    occurred_at: datetime | None = None
    person_id: str
    community_id: str | None = None
    topic_id: str | None = None
    interaction_type: str
    share_level: str = "SHARED"
    content: str
    note: str | None = None


@router.get("")
def list_interactions(
    person_id: str | None = None,
    community_id: str | None = None,
    topic_id: str | None = None,
    share_level: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int | None = Query(default=None, ge=1, le=200),
):
    interaction_service = InteractionService()
    return interaction_service.list_interactions(
        person_id=person_id,
        community_id=community_id,
        topic_id=topic_id,
        share_level=share_level,
        search=search,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("/overview")
def get_interaction_overview(
    recent_limit: int = Query(default=4, ge=1, le=20),
    person_limit: int = Query(default=7, ge=1, le=30),
):
    interaction_service = InteractionService()
    return interaction_service.get_interaction_overview(
        recent_limit=recent_limit,
        person_limit=person_limit,
    )


@router.post("")
def record_interaction(
    payload: InteractionCreateRequest,
    background_tasks: BackgroundTasks,
):
    interaction_service = InteractionService()

    interaction = interaction_service.record_interaction(
        person_id=payload.person_id,
        interaction_type=payload.interaction_type,
        community_id=payload.community_id,
        topic_id=payload.topic_id,
        share_level=payload.share_level,
        occurred_at=payload.occurred_at,
        content=payload.content,
        note=payload.note,
    )
    interaction_id = str(interaction.id)

    background_tasks.add_task(
        process_interaction_after_save,
        interaction_id=interaction_id,
        person_id=payload.person_id,
    )

    return {
        "status": "ok",
        "interaction_id": interaction_id,
    }
