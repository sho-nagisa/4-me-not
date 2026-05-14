import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.testing.demo_data import cleanup_demo_data


class APISmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.prefix = f"[SMOKE:{uuid4().hex[:8]}]"

        cleanup_demo_data(cls.prefix)

        community_root = cls.client.post(
            "/api/communities",
            json={
                "name": f"{cls.prefix} スモーク大学",
                "description": f"{cls.prefix} root",
            },
        )
        assert community_root.status_code == 200, community_root.text
        cls.community_root_id = community_root.json()["id"]

        community_child = cls.client.post(
            "/api/communities",
            json={
                "name": f"{cls.prefix} 面接練習会",
                "description": f"{cls.prefix} child",
                "parent_id": cls.community_root_id,
            },
        )
        assert community_child.status_code == 200, community_child.text
        cls.community_child_id = community_child.json()["id"]

        topic_root = cls.client.post(
            "/api/topics",
            json={
                "name": "就活",
                "description": f"{cls.prefix} topic-root",
            },
        )
        assert topic_root.status_code == 200, topic_root.text
        cls.topic_root_id = topic_root.json()["id"]

        topic_child = cls.client.post(
            "/api/topics",
            json={
                "name": "面接",
                "description": f"{cls.prefix} topic-child",
                "parent_id": cls.topic_root_id,
            },
        )
        assert topic_child.status_code == 200, topic_child.text
        cls.topic_child_id = topic_child.json()["id"]

        person = cls.client.post(
            "/api/persons",
            json={
                "name": "スモーク太郎",
                "canonical_name": f"{cls.prefix}:person",
                "primary_community_id": cls.community_child_id,
            },
        )
        assert person.status_code == 200, person.text
        cls.person_id = person.json()["id"]
        cls.interaction_id = None

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_demo_data(cls.prefix)
        cls.client.close()

    def test_01_health(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_02_reference_endpoints(self) -> None:
        persons = self.client.get("/api/persons")
        communities = self.client.get("/api/communities")
        topics = self.client.get("/api/topics")

        self.assertEqual(persons.status_code, 200)
        self.assertEqual(communities.status_code, 200)
        self.assertEqual(topics.status_code, 200)

        self.assertTrue(
            any(item["id"] == self.person_id for item in persons.json()),
            "Created person is not listed in /api/persons",
        )
        self.assertTrue(
            any(item["id"] == self.community_child_id for item in communities.json()),
            "Created community is not listed in /api/communities",
        )
        self.assertTrue(
            any(item["id"] == self.topic_child_id for item in topics.json()),
            "Created topic is not listed in /api/topics",
        )

    def test_03_duplicate_community_sibling_is_rejected(self) -> None:
        duplicate_root = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} スモーク大学",
                "description": f"{self.prefix} duplicate-root",
            },
        )
        duplicate_child = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} 面接練習会",
                "description": f"{self.prefix} duplicate-child",
                "parent_id": self.community_root_id,
            },
        )

        self.assertEqual(duplicate_root.status_code, 409, duplicate_root.text)
        self.assertEqual(duplicate_child.status_code, 409, duplicate_child.text)

    def test_03_manage_visibility_and_delete(self) -> None:
        temp_community = self.client.post(
            "/api/communities",
            json={
                "name": f"{self.prefix} Temporary Community",
                "description": f"{self.prefix} temp-community",
            },
        )
        self.assertEqual(temp_community.status_code, 200, temp_community.text)
        temp_community_id = temp_community.json()["id"]

        temp_person = self.client.post(
            "/api/persons",
            json={
                "name": f"{self.prefix} Temporary Person",
                "canonical_name": f"{self.prefix}:temp-person",
                "primary_community_id": temp_community_id,
            },
        )
        self.assertEqual(temp_person.status_code, 200, temp_person.text)
        temp_person_id = temp_person.json()["id"]

        hide_person = self.client.patch(
            f"/api/persons/{temp_person_id}",
            json={"is_hidden": True},
        )
        hide_community = self.client.patch(
            f"/api/communities/{temp_community_id}",
            json={"is_hidden": True},
        )

        self.assertEqual(hide_person.status_code, 200, hide_person.text)
        self.assertEqual(hide_community.status_code, 200, hide_community.text)
        self.assertTrue(hide_person.json()["is_hidden"])
        self.assertTrue(hide_community.json()["is_hidden"])

        visible_persons = self.client.get("/api/persons")
        visible_communities = self.client.get("/api/communities")
        hidden_persons = self.client.get("/api/persons", params={"include_hidden": "true"})
        hidden_communities = self.client.get(
            "/api/communities", params={"include_hidden": "true"}
        )

        self.assertEqual(visible_persons.status_code, 200)
        self.assertEqual(visible_communities.status_code, 200)
        self.assertEqual(hidden_persons.status_code, 200)
        self.assertEqual(hidden_communities.status_code, 200)

        self.assertFalse(
            any(item["id"] == temp_person_id for item in visible_persons.json())
        )
        self.assertFalse(
            any(item["id"] == temp_community_id for item in visible_communities.json())
        )
        self.assertTrue(any(item["id"] == temp_person_id for item in hidden_persons.json()))
        self.assertTrue(
            any(item["id"] == temp_community_id for item in hidden_communities.json())
        )

        delete_person = self.client.delete(f"/api/persons/{temp_person_id}")
        delete_community = self.client.delete(f"/api/communities/{temp_community_id}")

        self.assertEqual(delete_person.status_code, 200, delete_person.text)
        self.assertEqual(delete_community.status_code, 200, delete_community.text)

        after_delete_persons = self.client.get(
            "/api/persons", params={"include_hidden": "true"}
        )
        after_delete_communities = self.client.get(
            "/api/communities", params={"include_hidden": "true"}
        )

        self.assertFalse(
            any(item["id"] == temp_person_id for item in after_delete_persons.json())
        )
        self.assertFalse(
            any(item["id"] == temp_community_id for item in after_delete_communities.json())
        )

    def test_04_record_interaction(self) -> None:
        response = self.client.post(
            "/api/interactions",
            json={
                "person_id": self.person_id,
                "community_id": self.community_child_id,
                "topic_id": self.topic_child_id,
                "interaction_type": "MEETING",
                "share_level": "PARTIAL",
                "content": "面接練習で自己紹介と志望動機の話をした。",
                "note": f"{self.prefix} 回答の深掘りはまだ途中。",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.__class__.interaction_id = payload["interaction_id"]

    def test_05_search_interactions(self) -> None:
        if self.interaction_id is None:
            self.skipTest("interaction is not created")

        response = self.client.get(
            "/api/interactions",
            params={
                "person_id": self.person_id,
                "community_id": self.community_child_id,
                "topic_id": self.topic_child_id,
                "share_level": "PARTIAL",
                "search": "志望動機",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        items = response.json()
        self.assertTrue(items)
        self.assertTrue(any(item["id"] == self.interaction_id for item in items))

        limited_response = self.client.get("/api/interactions", params={"limit": 1})
        self.assertEqual(limited_response.status_code, 200, limited_response.text)
        self.assertLessEqual(len(limited_response.json()), 1)

        extra_response = self.client.post(
            "/api/interactions",
            json={
                "person_id": self.person_id,
                "community_id": self.community_child_id,
                "topic_id": self.topic_child_id,
                "interaction_type": "MEETING",
                "share_level": "SHARED",
                "content": f"{self.prefix} pagination extra record",
                "note": f"{self.prefix} pagination extra note",
            },
        )
        self.assertEqual(extra_response.status_code, 200, extra_response.text)

        paged_response = self.client.get(
            "/api/interactions",
            params={"limit": 1, "offset": 1, "include_total": "true"},
        )
        self.assertEqual(paged_response.status_code, 200, paged_response.text)
        paged_payload = paged_response.json()
        self.assertEqual(paged_payload["limit"], 1)
        self.assertEqual(paged_payload["offset"], 1)
        self.assertGreaterEqual(paged_payload["total_count"], 2)
        self.assertLessEqual(len(paged_payload["items"]), 1)

    def test_06_person_dashboard(self) -> None:
        if self.interaction_id is None:
            self.skipTest("interaction is not created")

        response = self.client.get(f"/api/persons/{self.person_id}/dashboard")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["person"]["id"], self.person_id)
        self.assertGreaterEqual(payload["overview"]["interaction_count"], 1)
        self.assertIn("top_topics", payload)
        self.assertIn("top_communities", payload)
        self.assertIn("conversation_prep", payload)

    def test_07_interaction_overview(self) -> None:
        if self.interaction_id is None:
            self.skipTest("interaction is not created")

        response = self.client.get(
            "/api/interactions/overview",
            params={"recent_limit": 20, "person_limit": 30},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertGreaterEqual(payload["total_count"], 1)
        self.assertTrue(
            any(item["id"] == self.interaction_id for item in payload["recent_interactions"])
        )
        self.assertTrue(
            any(
                item["person_id"] == self.person_id and item["count"] >= 1
                for item in payload["person_counts"]
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
