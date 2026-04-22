from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.ai_service import AIService
from backend.services.insight_service import InsightService
from backend.services.interaction_service import InteractionService
from backend.services.relation_service import RelationService


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
    limit: int | None = None,
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


@router.post("")
def record_interaction(payload: InteractionCreateRequest):
    interaction_service = InteractionService()
    ai_service = AIService()
    insight_service = InsightService()
    relation_service = RelationService()

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

    parsed = ai_service.analyze_interaction(str(interaction.id))
    if parsed is not None:
        insight_service.create_insight_from_ai(str(parsed.id))

    relation_service.update_relation(
        from_person_id=payload.person_id,
        to_person_id=payload.person_id,
        relation_type=1,
    )

    return {
        "status": "ok",
        "interaction_id": str(interaction.id),
    }
