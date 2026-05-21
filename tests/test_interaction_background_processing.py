import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import BackgroundTasks

from backend.app.api.interaction import InteractionCreateRequest, record_interaction
from backend.services.interaction_processing_service import process_interaction_after_save


class InteractionBackgroundProcessingTest(unittest.TestCase):
    def test_record_interaction_queues_post_processing(self) -> None:
        interaction_id = uuid4()
        payload = InteractionCreateRequest(
            person_id=str(uuid4()),
            interaction_type="MEETING",
            content="meeting notes",
        )
        background_tasks = BackgroundTasks()

        with patch("backend.app.api.interaction.InteractionService") as service_cls:
            service_cls.return_value.record_interaction.return_value = SimpleNamespace(
                id=interaction_id
            )

            response = record_interaction(payload, background_tasks)

        self.assertEqual(
            response,
            {
                "status": "ok",
                "interaction_id": str(interaction_id),
            },
        )
        self.assertEqual(len(background_tasks.tasks), 1)

        task = background_tasks.tasks[0]
        self.assertIs(task.func, process_interaction_after_save)
        self.assertEqual(task.kwargs["interaction_id"], str(interaction_id))
        self.assertEqual(task.kwargs["person_id"], payload.person_id)

    def test_process_interaction_after_save_runs_ai_and_followups(self) -> None:
        parsed_note_id = uuid4()

        with (
            patch(
                "backend.services.interaction_processing_service.AIService"
            ) as ai_service_cls,
            patch(
                "backend.services.interaction_processing_service.InsightService"
            ) as insight_service_cls,
            patch(
                "backend.services.interaction_processing_service.RelationService"
            ) as relation_service_cls,
            patch(
                "backend.services.interaction_processing_service.SearchService"
            ) as search_service_cls,
            patch(
                "backend.services.interaction_processing_service.TaskService"
            ) as task_service_cls,
        ):
            ai_service_cls.return_value.analyze_interaction.return_value = SimpleNamespace(
                id=parsed_note_id
            )
            task_service_cls.return_value.extract_candidates_from_interaction.return_value = [
                "task-1"
            ]

            process_interaction_after_save(
                interaction_id="interaction-1",
                person_id="person-1",
            )

        ai_service_cls.return_value.analyze_interaction.assert_called_once_with(
            "interaction-1"
        )
        insight_service_cls.return_value.create_insight_from_ai.assert_called_once_with(
            str(parsed_note_id)
        )
        search_service_cls.return_value.index_interaction.assert_called_once_with(
            "interaction-1"
        )
        task_service_cls.return_value.extract_candidates_from_interaction.assert_called_once_with(
            "interaction-1"
        )
        search_service_cls.return_value.index_task.assert_called_once_with("task-1")
        relation_service_cls.return_value.update_relation.assert_called_once_with(
            from_person_id="person-1",
            to_person_id="person-1",
            relation_type=1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
