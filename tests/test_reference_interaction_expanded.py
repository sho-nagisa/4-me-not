import unittest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete as sa_delete

from backend.app.account_context import get_current_account_id
from backend.app.main import app
from backend.db.session import SessionLocal
from backend.models.account.account import Account
from backend.models.person.person import Person
from tests.test_support import DbFixture, cleanup_test_data, unique_prefix


class ReferenceInteractionExpandedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_test_data("[TEST:ref:")
        cls.client.close()

    def setUp(self) -> None:
        self.prefix = unique_prefix("ref")
        self.fixture = DbFixture(self.prefix)

    def tearDown(self) -> None:
        pass

    def test_create_person_rejects_missing_primary_community(self) -> None:
        response = self.client.post(
            "/api/persons",
            json={
                "name": f"{self.prefix} Person",
                "canonical_name": f"{self.prefix}:missing-primary",
                "primary_community_id": str(uuid4()),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_create_person_rejects_hidden_primary_community(self) -> None:
        community = self.fixture.create_community("Hidden Primary", hidden=True)

        response = self.client.post(
            "/api/persons",
            json={
                "name": f"{self.prefix} Person",
                "canonical_name": f"{self.prefix}:hidden-primary",
                "primary_community_id": str(community.id),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_create_person_duplicate_canonical_name_has_defined_error(self) -> None:
        canonical = f"{self.prefix}:duplicate"
        first = self.client.post(
            "/api/persons",
            json={"name": f"{self.prefix} One", "canonical_name": canonical},
        )
        second = self.client.post(
            "/api/persons",
            json={"name": f"{self.prefix} Two", "canonical_name": canonical},
        )

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 409, second.text)

    def test_create_person_rejects_blank_name(self) -> None:
        response = self.client.post(
            "/api/persons",
            json={"name": "   ", "canonical_name": f"{self.prefix}:blank-name"},
        )

        self.assertEqual(response.status_code, 400)

    def test_create_community_rejects_blank_name(self) -> None:
        response = self.client.post(
            "/api/communities",
            json={"name": "   ", "description": f"{self.prefix} blank"},
        )

        self.assertEqual(response.status_code, 400)

    def test_create_community_allows_same_name_under_different_parent(self) -> None:
        root_a = self.fixture.create_community("Root A")
        root_b = self.fixture.create_community("Root B")

        child_a = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} Same Child",
                "description": f"{self.prefix} child-a",
                "parent_id": str(root_a.id),
            },
        )
        child_b = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} Same Child",
                "description": f"{self.prefix} child-b",
                "parent_id": str(root_b.id),
            },
        )

        self.assertEqual(child_a.status_code, 200, child_a.text)
        self.assertEqual(child_b.status_code, 200, child_b.text)

    def test_create_community_rejects_hidden_parent(self) -> None:
        parent = self.fixture.create_community("Hidden Parent", hidden=True)

        response = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} Child",
                "description": f"{self.prefix} child",
                "parent_id": str(parent.id),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_create_community_rejects_invalid_parent_uuid(self) -> None:
        response = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} Invalid Parent",
                "description": f"{self.prefix} invalid parent",
                "parent_id": "not-a-uuid",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_reference_paths_respect_include_hidden(self) -> None:
        root = self.fixture.create_community("Root")
        child = self.fixture.create_community("Child", parent=root)
        person = self.fixture.create_person("Path Person", primary_community=child)
        self.client.patch(f"/api/communities/{root.id}", json={"is_hidden": True})

        visible_communities = self.client.get("/api/communities")
        hidden_communities = self.client.get(
            "/api/communities",
            params={"include_hidden": "true"},
        )
        visible_people = self.client.get("/api/persons")
        hidden_people = self.client.get("/api/persons", params={"include_hidden": "true"})

        visible_child = next(item for item in visible_communities.json() if item["id"] == str(child.id))
        hidden_child = next(item for item in hidden_communities.json() if item["id"] == str(child.id))
        visible_person = next(item for item in visible_people.json() if item["id"] == str(person.id))
        hidden_person = next(item for item in hidden_people.json() if item["id"] == str(person.id))

        self.assertNotIn("Root", visible_child["path"])
        self.assertIn("Root", hidden_child["path"])
        self.assertEqual(visible_person["primary_community_id"], str(child.id))
        self.assertIsNone(visible_person["primary_community_path"])
        self.assertEqual(hidden_person["primary_community_id"], str(child.id))
        self.assertIn("Root", hidden_person["primary_community_path"])

    def test_create_topic_rejects_invalid_parent_uuid(self) -> None:
        response = self.client.post(
            "/api/topics",
            json={
                "name": f"{self.prefix} Topic",
                "description": f"{self.prefix} topic",
                "parent_id": "not-a-uuid",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_topic_rejects_missing_parent(self) -> None:
        response = self.client.post(
            "/api/topics",
            json={
                "name": f"{self.prefix} Topic",
                "description": f"{self.prefix} topic",
                "parent_id": str(uuid4()),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_create_topic_builds_parent_child_path(self) -> None:
        parent = self.fixture.create_topic("Parent")
        response = self.client.post(
            "/api/topics",
            json={
                "name": f"{self.prefix} Child Topic",
                "description": f"{self.prefix} topic child",
                "parent_id": str(parent.id),
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Parent", response.json()["path"])
        self.assertIn("Child Topic", response.json()["path"])

    def test_record_interaction_rejects_invalid_person_uuid(self) -> None:
        response = self.client.post(
            "/api/interactions",
            json={
                "person_id": "not-a-uuid",
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_record_interaction_rejects_missing_person(self) -> None:
        response = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(uuid4()),
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_record_interaction_rejects_hidden_person(self) -> None:
        person = self.fixture.create_person("Hidden", hidden=True)

        response = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_record_interaction_rejects_invalid_missing_or_hidden_community(self) -> None:
        person = self.fixture.create_person("Person")
        hidden = self.fixture.create_community("Hidden", hidden=True)

        invalid = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "community_id": "not-a-uuid",
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )
        missing = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "community_id": str(uuid4()),
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )
        hidden_response = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "community_id": str(hidden.id),
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(hidden_response.status_code, 404)

    def test_record_interaction_rejects_invalid_or_missing_topic(self) -> None:
        person = self.fixture.create_person("Person")

        invalid = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "topic_id": "not-a-uuid",
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )
        missing = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "topic_id": str(uuid4()),
                "interaction_type": "MEETING",
                "content": "hello",
            },
        )

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(missing.status_code, 404)

    def test_record_interaction_rejects_unsupported_type_or_share_level(self) -> None:
        person = self.fixture.create_person("Person")

        bad_type = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "interaction_type": "MAIL",
                "content": "hello",
            },
        )
        bad_share = self.client.post(
            "/api/interactions",
            json={
                "person_id": str(person.id),
                "interaction_type": "MEETING",
                "share_level": "SECRET",
                "content": "hello",
            },
        )

        self.assertEqual(bad_type.status_code, 400)
        self.assertEqual(bad_share.status_code, 400)

    def test_list_interactions_filters_by_date_range(self) -> None:
        person = self.fixture.create_person("Person")
        inside = self.fixture.create_interaction(
            person=person,
            content="inside",
            occurred_at=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )
        self.fixture.create_interaction(
            person=person,
            content="outside",
            occurred_at=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
        )

        response = self.client.get(
            "/api/interactions",
            params={
                "person_id": str(person.id),
                "date_from": "2026-05-19T00:00:00+00:00",
                "date_to": "2026-05-21T00:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        ids = {item["id"] for item in response.json()}
        self.assertIn(str(inside.id), ids)
        self.assertEqual(len(ids), 1)

    def test_list_interactions_orders_by_occurred_at_then_created_at_desc(self) -> None:
        person = self.fixture.create_person("Person")
        older = self.fixture.create_interaction(
            person=person,
            content="older",
            occurred_at=datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc),
        )
        newer = self.fixture.create_interaction(
            person=person,
            content="newer",
            occurred_at=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )

        response = self.client.get(
            "/api/interactions",
            params={"person_id": str(person.id), "limit": 2},
        )

        ids = [item["id"] for item in response.json()]
        self.assertEqual(ids[0], str(newer.id))
        self.assertEqual(ids[1], str(older.id))

    def test_record_interaction_normalizes_type_aliases(self) -> None:
        person = self.fixture.create_person("Person")

        for alias, expected in (
            ("CALL", "MESSAGE"),
            ("CHAT", "TALK"),
            ("OBSERVATION", "EVENT"),
        ):
            response = self.client.post(
                "/api/interactions",
                json={
                    "person_id": str(person.id),
                    "interaction_type": alias,
                    "content": f"{self.prefix} {alias}",
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            interaction_id = response.json()["interaction_id"]
            listed = self.client.get("/api/interactions", params={"person_id": str(person.id)})
            item = next(item for item in listed.json() if item["id"] == interaction_id)
            self.assertEqual(item["interaction_type"], expected)

    def test_person_dashboard_aggregates_share_topics_communities_and_notes(self) -> None:
        community = self.fixture.create_community("Dashboard Community")
        topic = self.fixture.create_topic("Dashboard Topic")
        person = self.fixture.create_person("Dashboard Person", primary_community=community)
        self.fixture.create_interaction(
            person=person,
            community=community,
            topic=topic,
            content="shared",
            note=f"{self.prefix} shared note",
        )
        self.fixture.create_interaction(
            person=person,
            community=community,
            topic=topic,
            content="partial",
            share_level=2,
        )

        response = self.client.get(f"/api/persons/{person.id}/dashboard")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["overview"]["interaction_count"], 2)
        self.assertTrue(payload["share_summary"])
        self.assertTrue(payload["top_topics"])
        self.assertTrue(payload["top_communities"])
        self.assertTrue(payload["conversation_prep"]["recent_notes"])

    def test_interaction_overview_excludes_hidden_people_and_applies_limits(self) -> None:
        visible = self.fixture.create_person("Visible")
        hidden = self.fixture.create_person("Hidden", hidden=True)
        visible_interaction = self.fixture.create_interaction(
            person=visible,
            content="visible",
            occurred_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        self.fixture.create_interaction(
            person=hidden,
            content="hidden",
            occurred_at=datetime(2031, 1, 1, tzinfo=timezone.utc),
        )

        response = self.client.get(
            "/api/interactions/overview",
            params={"recent_limit": 1, "person_limit": 1},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertLessEqual(len(payload["recent_interactions"]), 1)
        self.assertLessEqual(len(payload["person_counts"]), 1)
        self.assertTrue(
            any(item["id"] == str(visible_interaction.id) for item in payload["recent_interactions"])
        )

    def test_delete_person_removes_related_interactions_from_lists(self) -> None:
        person = self.fixture.create_person("Delete Person")
        interaction = self.fixture.create_interaction(person=person, content="delete-person")

        delete_response = self.client.delete(f"/api/persons/{person.id}")
        list_response = self.client.get("/api/interactions", params={"search": "delete-person"})

        self.assertEqual(delete_response.status_code, 200, delete_response.text)
        self.assertEqual(list_response.status_code, 200, list_response.text)
        self.assertFalse(any(item["id"] == str(interaction.id) for item in list_response.json()))

    def test_delete_community_preserves_interaction_with_null_community_reference(self) -> None:
        community = self.fixture.create_community("Delete Community")
        person = self.fixture.create_person("Community Person", primary_community=community)
        interaction = self.fixture.create_interaction(
            person=person,
            community=community,
            content="delete-community",
        )

        delete_response = self.client.delete(f"/api/communities/{community.id}")
        list_response = self.client.get("/api/interactions", params={"search": "delete-community"})

        self.assertEqual(delete_response.status_code, 200, delete_response.text)
        self.assertEqual(list_response.status_code, 200, list_response.text)
        payload = next(item for item in list_response.json() if item["id"] == str(interaction.id))
        self.assertIsNone(payload["community_id"])

    def test_required_api_fields_return_422(self) -> None:
        person_response = self.client.post("/api/persons", json={})
        interaction_response = self.client.post("/api/interactions", json={})
        community_response = self.client.post("/api/communities", json={})

        self.assertEqual(person_response.status_code, 422)
        self.assertEqual(interaction_response.status_code, 422)
        self.assertEqual(community_response.status_code, 422)

    def test_person_interaction_counts_include_zero_primary_community_members(self) -> None:
        community = self.fixture.create_community("Counts Community")
        person = self.fixture.create_person("No Interactions", primary_community=community)

        response = self.client.get(
            "/api/persons/interaction-counts",
            params={"community_id": str(community.id)},
        )

        self.assertEqual(response.status_code, 200, response.text)
        item = next(item for item in response.json() if item["person_id"] == str(person.id))
        self.assertEqual(item["count"], 0)

    def test_services_scope_queries_by_current_account_id(self) -> None:
        other_account_id = uuid4()
        db = SessionLocal()
        try:
            db.add(Account(id=other_account_id, email=f"{self.prefix}@example.test"))
            db.flush()
            db.add(
                Person(
                    account_id=other_account_id,
                    name=f"{self.prefix} Other Account Person",
                    canonical_name=f"{self.prefix}:other-account",
                )
            )
            db.commit()

            response = self.client.get("/api/persons", params={"include_hidden": "true"})
            names = [item["name"] for item in response.json()]
            self.assertNotIn(f"{self.prefix} Other Account Person", names)
        finally:
            db.execute(sa_delete(Account).where(Account.id == other_account_id))
            db.commit()
            db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
