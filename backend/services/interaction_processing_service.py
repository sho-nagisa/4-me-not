import logging

from backend.services.ai_service import AIService
from backend.services.insight_service import InsightService
from backend.services.relation_service import RelationService
from backend.services.search import SearchService
from backend.services.task_service import TaskService


logger = logging.getLogger(__name__)


def process_interaction_after_save(interaction_id: str, person_id: str) -> None:
    try:
        ai_service = AIService()
        insight_service = InsightService()
        relation_service = RelationService()
        search_service = SearchService()
        task_service = TaskService()

        parsed = ai_service.analyze_interaction(interaction_id)
        if parsed is not None:
            insight_service.create_insight_from_ai(str(parsed.id))

        search_service.index_interaction(interaction_id)
        for task_id in task_service.extract_candidates_from_interaction(interaction_id):
            search_service.index_task(task_id)

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
