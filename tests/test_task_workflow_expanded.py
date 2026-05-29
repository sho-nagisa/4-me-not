import unittest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.db.session import SessionLocal
from backend.models.base.enums import TaskStatus
from backend.models.search.search_document import SearchDocument
from backend.models.task.task import Task
from backend.services.search import SearchService
from backend.services.task_service import (
    TASK_ROLE_DEADLINE_FROM,
    TASK_ROLE_RELATED,
    TASK_ROLE_SOURCE,
    TASK_TARGET_COMMUNITY,
    TASK_TARGET_INTERACTION,
    TASK_TARGET_PERSON,
    TASK_TARGET_TOPIC,
    extract_task_candidates,
    normalize_candidate_title,
    split_candidate_sentences,
)
from backend.services.task_service import TaskService
from tests.test_support import DbFixture, cleanup_test_data, unique_prefix


class TaskWorkflowExpandedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_test_data("[TEST:task:")
        cls.client.close()

    def setUp(self) -> None:
        self.prefix = unique_prefix("task")
        self.fixture = DbFixture(self.prefix)

    def tearDown(self) -> None:
        pass

    def _interaction_for_task(self, text: str | None = None):
        community = self.fixture.create_community("Tasks")
        topic = self.fixture.create_topic("Follow up")
        person = self.fixture.create_person("Alice", primary_community=community)
        interaction = self.fixture.create_interaction(
            person=person,
            community=community,
            topic=topic,
            content=text or "5月25日までに資料を送る",
            occurred_at=datetime(2026, 5, 21, 10, 0, tzinfo=timezone.utc),
        )
        return person, community, topic, interaction

    def test_extract_candidates_creates_task_and_links(self) -> None:
        person, community, topic, interaction = self._interaction_for_task()

        task_ids = TaskService().extract_candidates_from_interaction(str(interaction.id))

        self.assertEqual(len(task_ids), 1)
        task = self.fixture.load_task(task_ids[0])
        self.assertTrue(task.is_candidate)
        self.assertEqual(task.candidate_status, "pending")
        self.assertEqual(task.source_type, TASK_TARGET_INTERACTION)
        self.assertEqual(task.source_id, interaction.id)
        self.assertEqual(task.due_at.date().isoformat(), "2026-05-25")

        links = {(link.target_type, link.target_id, link.role) for link in task.links}
        self.assertIn((TASK_TARGET_INTERACTION, interaction.id, TASK_ROLE_SOURCE), links)
        self.assertIn((TASK_TARGET_PERSON, person.id, TASK_ROLE_RELATED), links)
        self.assertIn((TASK_TARGET_COMMUNITY, community.id, TASK_ROLE_RELATED), links)
        self.assertIn((TASK_TARGET_TOPIC, topic.id, TASK_ROLE_RELATED), links)
        self.assertIn(
            (TASK_TARGET_INTERACTION, interaction.id, TASK_ROLE_DEADLINE_FROM),
            links,
        )

    def test_extract_candidates_skips_existing_active_candidate(self) -> None:
        _, _, _, interaction = self._interaction_for_task()
        first_ids = TaskService().extract_candidates_from_interaction(str(interaction.id))

        second_ids = TaskService().extract_candidates_from_interaction(str(interaction.id))

        self.assertEqual(len(first_ids), 1)
        self.assertEqual(second_ids, [])

    def test_extract_candidates_allows_dismissed_candidate_reproposal(self) -> None:
        _, _, _, interaction = self._interaction_for_task()
        first_ids = TaskService().extract_candidates_from_interaction(str(interaction.id))
        task = self.fixture.load_task(first_ids[0])

        db = SessionLocal()
        try:
            record = db.get(Task, task.id)
            record.candidate_status = "dismissed"
            db.commit()
        finally:
            db.close()

        second_ids = TaskService().extract_candidates_from_interaction(str(interaction.id))

        self.assertEqual(len(second_ids), 1)
        self.assertNotEqual(first_ids[0], second_ids[0])

    def test_list_tasks_filters_candidates_and_status(self) -> None:
        self.fixture.create_task("Pending", is_candidate=True, candidate_status="pending")
        self.fixture.create_task("Accepted", is_candidate=False, candidate_status="accepted")
        self.fixture.create_task("Dismissed", is_candidate=True, candidate_status="dismissed")

        pending = self.client.get(
            "/api/tasks",
            params={"candidate_status": "pending", "limit": 20},
        )
        accepted_only = self.client.get(
            "/api/tasks",
            params={"include_candidates": "false", "limit": 20},
        )

        self.assertEqual(pending.status_code, 200, pending.text)
        self.assertTrue(
            all(item["candidate_status"] == "pending" for item in pending.json())
        )
        accepted_titles = [item["title"] for item in accepted_only.json()]
        self.assertTrue(any("Accepted" in title for title in accepted_titles))
        self.assertFalse(any("Pending" in title for title in accepted_titles))

    def test_list_tasks_rejects_limit_outside_supported_range(self) -> None:
        too_small = self.client.get("/api/tasks", params={"limit": 0})
        too_large = self.client.get("/api/tasks", params={"limit": 201})

        self.assertEqual(too_small.status_code, 422, too_small.text)
        self.assertEqual(too_large.status_code, 422, too_large.text)

    def test_create_manual_task_indexes_task_for_search(self) -> None:
        response = self.client.post(
            "/api/tasks",
            json={
                "title": f"{self.prefix} Manual Task",
                "description": f"{self.prefix} manual task body",
                "due_at": "2026-06-03T23:59:00+00:00",
                "priority": 3,
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["title"], f"{self.prefix} Manual Task")
        self.assertEqual(payload["status"], "TODO")
        self.assertFalse(payload["is_candidate"])
        self.assertEqual(payload["candidate_status"], "accepted")
        self.assertEqual(payload["source_type"], "manual")
        self.assertEqual(payload["priority"], 3)

        db = SessionLocal()
        try:
            document = (
                db.query(SearchDocument)
                .filter(
                    SearchDocument.target_type == "task",
                    SearchDocument.target_id == UUID(payload["id"]),
                )
                .first()
            )
            self.assertIsNotNone(document)
            self.assertIn("Manual Task", document.title)
        finally:
            db.close()

    def test_create_manual_task_rejects_blank_title(self) -> None:
        response = self.client.post("/api/tasks", json={"title": "   "})

        self.assertEqual(response.status_code, 400)

    def test_update_task_edits_fields_and_reindexes(self) -> None:
        task = self.fixture.create_task("Editable", is_candidate=False, candidate_status="accepted")
        SearchService().index_task(str(task.id))

        response = self.client.patch(
            f"/api/tasks/{task.id}",
            json={
                "title": f"{self.prefix} Updated Task",
                "description": f"{self.prefix} updated description",
                "due_at": None,
                "priority": 5,
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["title"], f"{self.prefix} Updated Task")
        self.assertEqual(payload["description"], f"{self.prefix} updated description")
        self.assertIsNone(payload["due_at"])
        self.assertEqual(payload["priority"], 5)

        db = SessionLocal()
        try:
            document = (
                db.query(SearchDocument)
                .filter(
                    SearchDocument.target_type == "task",
                    SearchDocument.target_id == task.id,
                )
                .first()
            )
            self.assertIsNotNone(document)
            self.assertEqual(document.title, f"{self.prefix} Updated Task")
        finally:
            db.close()

    def test_complete_and_reopen_task_update_status(self) -> None:
        task = self.fixture.create_task("Toggle", is_candidate=False, candidate_status="accepted")

        completed = self.client.post(f"/api/tasks/{task.id}/complete")
        reopened = self.client.post(f"/api/tasks/{task.id}/reopen")

        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["status"], "DONE")
        self.assertEqual(reopened.status_code, 200, reopened.text)
        self.assertEqual(reopened.json()["status"], "TODO")

    def test_list_tasks_filters_open_status_and_search_text(self) -> None:
        self.fixture.create_task(
            "Open Followup",
            description=f"{self.prefix} alpha task",
            is_candidate=False,
            candidate_status="accepted",
            status=TaskStatus.TODO,
        )
        self.fixture.create_task(
            "Closed Followup",
            description=f"{self.prefix} alpha done",
            is_candidate=False,
            candidate_status="accepted",
            status=TaskStatus.DONE,
        )
        self.fixture.create_task(
            "Other",
            description=f"{self.prefix} beta task",
            is_candidate=False,
            candidate_status="accepted",
            status=TaskStatus.TODO,
        )

        response = self.client.get(
            "/api/tasks",
            params={
                "include_candidates": "false",
                "open_only": "true",
                "search": "alpha",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        titles = [item["title"] for item in response.json()]
        self.assertTrue(any("Open Followup" in title for title in titles))
        self.assertFalse(any("Closed Followup" in title for title in titles))
        self.assertFalse(any("Other" in title for title in titles))

    def test_update_task_rejects_invalid_status_and_priority(self) -> None:
        task = self.fixture.create_task("Invalid Update", is_candidate=False)

        bad_status = self.client.patch(
            f"/api/tasks/{task.id}",
            json={"status": "UNKNOWN"},
        )
        bad_priority = self.client.patch(
            f"/api/tasks/{task.id}",
            json={"priority": 9},
        )

        self.assertEqual(bad_status.status_code, 400)
        self.assertEqual(bad_priority.status_code, 422)

    def test_accept_task_candidate_marks_accepted(self) -> None:
        task = self.fixture.create_task("Candidate", is_candidate=True)

        response = self.client.post(f"/api/tasks/{task.id}/accept")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertFalse(payload["is_candidate"])
        self.assertEqual(payload["candidate_status"], "accepted")

    def test_dismiss_task_candidate_marks_dismissed_and_unindexes(self) -> None:
        task = self.fixture.create_task("Searchable Candidate", is_candidate=True)
        SearchService().index_task(str(task.id))

        response = self.client.post(f"/api/tasks/{task.id}/dismiss")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["is_candidate"])
        self.assertEqual(payload["candidate_status"], "dismissed")

        db = SessionLocal()
        try:
            document = (
                db.query(SearchDocument)
                .filter(
                    SearchDocument.target_type == "task",
                    SearchDocument.target_id == task.id,
                )
                .first()
            )
            self.assertIsNone(document)
        finally:
            db.close()

    def test_task_candidate_status_endpoints_return_400_or_404(self) -> None:
        bad_uuid = self.client.post("/api/tasks/not-a-uuid/accept")
        missing = self.client.post(f"/api/tasks/{uuid4()}/dismiss")

        self.assertEqual(bad_uuid.status_code, 400)
        self.assertEqual(missing.status_code, 404)

    def test_extract_task_candidates_handles_iso_due_date(self) -> None:
        candidates = extract_task_candidates(
            "TODO: 2026-06-03までに企画書を送る",
            base_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].due_at.date().isoformat(), "2026-06-03")

    def test_extract_task_candidates_handles_today(self) -> None:
        candidates = extract_task_candidates(
            "今日までに返信する",
            base_at=datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(candidates[0].due_at.date().isoformat(), "2026-05-21")

    def test_extract_task_candidates_handles_tomorrow(self) -> None:
        candidates = extract_task_candidates(
            "明日までに確認する",
            base_at=datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(candidates[0].due_at.date().isoformat(), "2026-05-22")

    def test_extract_task_candidates_handles_next_week(self) -> None:
        candidates = extract_task_candidates(
            "来週までに資料を準備する",
            base_at=datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(candidates[0].due_at.date().isoformat(), "2026-05-28")

    def test_extract_task_candidates_rolls_past_month_day_to_next_year(self) -> None:
        candidates = extract_task_candidates(
            "1月5日までに資料を送る",
            base_at=datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(candidates[0].due_at.date().isoformat(), "2027-01-05")

    def test_extract_task_candidates_limits_to_five_results(self) -> None:
        text = "。".join(f"TODO: item {index} を確認する" for index in range(8))

        candidates = extract_task_candidates(
            text,
            base_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
        )

        self.assertEqual(len(candidates), 5)

    def test_normalize_candidate_title_trims_prefix_and_caps_length(self) -> None:
        title = normalize_candidate_title(f"TODO: {'a' * 160}")

        self.assertFalse(title.startswith("TODO"))
        self.assertEqual(len(title), 120)
        self.assertTrue(title.endswith("..."))

    def test_split_candidate_sentences_handles_newlines_bullets_and_punctuation(self) -> None:
        sentences = split_candidate_sentences("TODO: Aを確認する\n- Bを送る。Cを準備する")

        self.assertIn("Aを確認する", sentences[0])
        self.assertTrue(any("Bを送る" in item for item in sentences))
        self.assertTrue(any("Cを準備する" in item for item in sentences))


if __name__ == "__main__":
    unittest.main(verbosity=2)
