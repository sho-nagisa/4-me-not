import unittest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.db.session import SessionLocal
from backend.models.reminder.reminder import Reminder
from backend.models.search.search_document import SearchDocument
from backend.services.calendar_service import CalendarService
from backend.services.search import SearchService
from tests.test_support import DbFixture, cleanup_test_data, unique_prefix


class CalendarReminderExpandedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_test_data("[TEST:cal:")
        cls.client.close()

    def setUp(self) -> None:
        self.prefix = unique_prefix("cal")
        self.fixture = DbFixture(self.prefix)

    def tearDown(self) -> None:
        pass

    def test_create_calendar_event_with_person_and_display_only_participants(self) -> None:
        person = self.fixture.create_person("Participant")

        response = self.client.post(
            "/api/calendar-events",
            json={
                "title": f"{self.prefix} Planning",
                "description": f"{self.prefix} event",
                "location": "Room 1",
                "start_at": "2026-05-23T10:00:00+00:00",
                "end_at": "2026-05-23T11:00:00+00:00",
                "external_id": f"{self.prefix}:event:create",
                "participants": [
                    {"person_id": str(person.id), "role": "owner", "confidence": 0.9},
                    {"display_name": "Guest User", "email": "guest@example.test"},
                ],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["title"], f"{self.prefix} Planning")
        self.assertEqual(len(payload["participants"]), 2)
        self.assertTrue(any(item["person_id"] == str(person.id) for item in payload["participants"]))
        self.assertTrue(any(item["display_name"] == "Guest User" for item in payload["participants"]))

    def test_create_calendar_event_rejects_end_before_start(self) -> None:
        response = self.client.post(
            "/api/calendar-events",
            json={
                "title": f"{self.prefix} Bad Time",
                "start_at": "2026-05-23T12:00:00+00:00",
                "end_at": "2026-05-23T11:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_calendar_event_rejects_end_equal_to_start(self) -> None:
        response = self.client.post(
            "/api/calendar-events",
            json={
                "title": f"{self.prefix} Zero Length",
                "start_at": "2026-05-23T11:00:00+00:00",
                "end_at": "2026-05-23T11:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_calendar_event_rejects_missing_person(self) -> None:
        response = self.client.post(
            "/api/calendar-events",
            json={
                "title": f"{self.prefix} Missing Person",
                "start_at": "2026-05-23T10:00:00+00:00",
                "end_at": "2026-05-23T11:00:00+00:00",
                "participants": [{"person_id": str(uuid4())}],
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_create_calendar_event_rejects_invalid_participant_uuid(self) -> None:
        response = self.client.post(
            "/api/calendar-events",
            json={
                "title": f"{self.prefix} Bad Participant",
                "start_at": "2026-05-23T10:00:00+00:00",
                "end_at": "2026-05-23T11:00:00+00:00",
                "participants": [{"person_id": "not-a-uuid"}],
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_calendar_event_rejects_hidden_person(self) -> None:
        person = self.fixture.create_person("Hidden Participant", hidden=True)

        response = self.client.post(
            "/api/calendar-events",
            json={
                "title": f"{self.prefix} Hidden Person",
                "start_at": "2026-05-23T10:00:00+00:00",
                "end_at": "2026-05-23T11:00:00+00:00",
                "participants": [{"person_id": str(person.id)}],
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_list_calendar_events_orders_by_start_desc_and_limits(self) -> None:
        first = self.fixture.create_calendar_event(
            "First",
            start_at=datetime(2035, 1, 1, 9, 0, tzinfo=timezone.utc),
            end_at=datetime(2035, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        second = self.fixture.create_calendar_event(
            "Second",
            start_at=datetime(2036, 1, 1, 9, 0, tzinfo=timezone.utc),
            end_at=datetime(2036, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        response = self.client.get("/api/calendar-events", params={"limit": 2})

        self.assertEqual(response.status_code, 200, response.text)
        ids = [item["id"] for item in response.json()]
        self.assertEqual(ids[0], str(second.id))
        self.assertIn(str(first.id), ids)

    def test_list_calendar_events_rejects_limit_outside_supported_range(self) -> None:
        too_small = self.client.get("/api/calendar-events", params={"limit": 0})
        too_large = self.client.get("/api/calendar-events", params={"limit": 201})

        self.assertEqual(too_small.status_code, 422, too_small.text)
        self.assertEqual(too_large.status_code, 422, too_large.text)

    def test_create_calendar_event_indexes_event_for_search(self) -> None:
        payload = CalendarService().create_event(
            title=f"{self.prefix} Searchable Event",
            description=f"{self.prefix} calendar-search-token",
            start_at=datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 5, 23, 11, 0, tzinfo=timezone.utc),
            external_id=f"{self.prefix}:searchable-event",
        )

        db = SessionLocal()
        try:
            document = (
                db.query(SearchDocument)
                .filter(
                    SearchDocument.target_type == "calendar_event",
                    SearchDocument.target_id == UUID(payload["id"]),
                    SearchDocument.search_text.like("%calendar-search-token%"),
                )
                .first()
            )
            self.assertIsNotNone(document)
        finally:
            db.close()

    def test_create_calendar_event_duplicate_external_id_has_defined_error(self) -> None:
        external_id = f"{self.prefix}:duplicate-event"
        body = {
            "title": f"{self.prefix} Duplicate",
            "start_at": "2026-05-23T10:00:00+00:00",
            "end_at": "2026-05-23T11:00:00+00:00",
            "external_id": external_id,
        }

        first = self.client.post("/api/calendar-events", json=body)
        second = self.client.post("/api/calendar-events", json=body)

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 409, second.text)

    def test_calendar_event_required_fields_return_422(self) -> None:
        response = self.client.post("/api/calendar-events", json={})

        self.assertEqual(response.status_code, 422)

    def test_create_reminder_accepts_iso_z_datetime_and_optional_message(self) -> None:
        response = self.client.post(
            "/api/reminders",
            json={
                "title": f"{self.prefix} Reminder",
                "remind_at": "2026-05-23T10:00:00Z",
                "message": f"{self.prefix} message",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        reminder_id = response.json()["id"]
        db = SessionLocal()
        try:
            reminder = db.get(Reminder, UUID(reminder_id))
            self.assertEqual(reminder.title, f"{self.prefix} Reminder")
            self.assertEqual(reminder.message, f"{self.prefix} message")
        finally:
            db.close()

    def test_create_reminder_rejects_invalid_remind_at(self) -> None:
        response = self.client.post(
            "/api/reminders",
            json={
                "title": f"{self.prefix} Bad Reminder",
                "remind_at": "not-a-date",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_reminder_rejects_blank_title(self) -> None:
        response = self.client.post(
            "/api/reminders",
            json={
                "title": "   ",
                "remind_at": "2026-05-23T10:00:00Z",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_reminder_required_fields_return_422(self) -> None:
        response = self.client.post("/api/reminders", json={})

        self.assertEqual(response.status_code, 422)

    def test_search_index_can_delete_missing_calendar_event_document(self) -> None:
        event = self.fixture.create_calendar_event("Temporary Indexed")
        service = SearchService()
        service.index_calendar_event(str(event.id))

        cleanup_test_data(self.prefix)
        service.index_calendar_event(str(event.id))

        self.assertEqual(self.fixture.search_documents("calendar_event"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
