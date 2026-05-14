import logging

from backend.services.ai_service import AIService
from backend.services.insight_service import InsightService
from backend.services.relation_service import RelationService


logger = logging.getLogger(__name__)


def process_interaction_after_save(interaction_id: str, person_id: str) -> None:
    try:
        ai_service = AIService()
        insight_service = InsightService()
        relation_service = RelationService()

        parsed = ai_service.analyze_interaction(interaction_id)
        if parsed is not None:
            insight_service.create_insight_from_ai(str(parsed.id))

        relation_service.update_relation(
            from_person_id=person_id,
            to_person_id=person_id,
            relation_type=1,
        )
    except Exception:
        logger.exception(
            "Failed to process interaction after save",
            extra={"interaction_id": interaction_id},
        )
