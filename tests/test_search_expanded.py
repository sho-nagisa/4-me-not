import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.account_context import get_current_account_id
from backend.app.main import app
from backend.db.session import SessionLocal
from backend.models.search.search_document import SearchDocument
from backend.services.person_service import PersonService
from backend.services.search import SearchService
from backend.services.search.answer import build_rag_answer
from backend.services.search.embedding import SearchEmbeddingProvider
from backend.services.search.utils import (
    calculate_keyword_score,
    calculate_recency_score,
    compact_text,
    cosine_similarity,
    extract_snippet,
    first_non_empty,
    join_search_parts,
    normalize_vector,
    parse_embedding,
)
from tests.test_support import DbFixture, cleanup_test_data, unique_prefix


class SearchExpandedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_test_data("[TEST:search:")
        cls.client.close()

    def setUp(self) -> None:
        self.prefix = unique_prefix("search")
        self.fixture = DbFixture(self.prefix)

    def tearDown(self) -> None:
        pass

    def test_index_interaction_creates_related_search_documents(self) -> None:
        community = self.fixture.create_community("Search Community")
        topic = self.fixture.create_topic("Search Topic")
        person = self.fixture.create_person("Search Person", primary_community=community)
        interaction = self.fixture.create_interaction(
            person=person,
            community=community,
            topic=topic,
            content="searchable meeting content",
        )

        SearchService().index_interaction(str(interaction.id))

        target_types = {doc.target_type for doc in self.fixture.search_documents()}
        self.assertIn("interaction", target_types)
        self.assertIn("person", target_types)
        self.assertIn("community", target_types)
        self.assertIn("topic", target_types)

    def test_index_interaction_removes_hidden_or_invisible_documents(self) -> None:
        community = self.fixture.create_community("Hidden Search")
        person = self.fixture.create_person("Hidden Person", primary_community=community)
        interaction = self.fixture.create_interaction(
            person=person,
            community=community,
            content="hidden searchable content",
        )
        SearchService().index_interaction(str(interaction.id))

        self.client.patch(f"/api/persons/{person.id}", json={"is_hidden": True})
        SearchService().index_interaction(str(interaction.id))

        target_types = {doc.target_type for doc in self.fixture.search_documents()}
        self.assertNotIn("interaction", target_types)
        self.assertNotIn("person", target_types)

    def test_search_endpoint_filters_single_and_multiple_target_types(self) -> None:
        community = self.fixture.create_community("Filter Community")
        topic = self.fixture.create_topic("Filter Topic")
        person = self.fixture.create_person("Filter Person", primary_community=community)
        interaction = self.fixture.create_interaction(
            person=person,
            community=community,
            topic=topic,
            content="filter-target-token",
        )
        SearchService().index_interaction(str(interaction.id))

        one = self.client.get(
            "/api/search",
            params={"q": "filter-target-token", "target_type": "interaction"},
        )
        many = self.client.get(
            "/api/search",
            params=[
                ("q", "filter-target-token"),
                ("target_type", "interaction"),
                ("target_type", "person"),
            ],
        )

        self.assertEqual(one.status_code, 200, one.text)
        self.assertTrue(one.json()["results"])
        self.assertTrue(all(item["target_type"] == "interaction" for item in one.json()["results"]))
        self.assertEqual(many.status_code, 200, many.text)
        self.assertTrue(
            all(item["target_type"] in {"interaction", "person"} for item in many.json()["results"])
        )

    def test_rebuild_account_index_indexes_all_supported_targets(self) -> None:
        community = self.fixture.create_community("Rebuild Community")
        topic = self.fixture.create_topic("Rebuild Topic")
        person = self.fixture.create_person("Rebuild Person", primary_community=community)
        interaction = self.fixture.create_interaction(
            person=person,
            community=community,
            topic=topic,
            content="rebuild-token",
        )
        task = self.fixture.create_task(
            "Rebuild Task",
            source_id=interaction.id,
            links=[("person", person.id, "related", 0.9)],
        )
        self.fixture.create_calendar_event("Rebuild Event")

        counts = SearchService().rebuild_account_index()
        target_types = {doc.target_type for doc in self.fixture.search_documents()}

        self.assertGreaterEqual(counts["people"], 1)
        self.assertGreaterEqual(counts["communities"], 1)
        self.assertGreaterEqual(counts["topics"], 1)
        self.assertGreaterEqual(counts["interactions"], 1)
        self.assertGreaterEqual(counts["tasks"], 1)
        self.assertGreaterEqual(counts["calendar_events"], 1)
        self.assertTrue(
            {"person", "community", "topic", "interaction", "task", "calendar_event"}
            <= target_types
        )
        self.assertIsNotNone(task.id)

    def test_search_service_returns_empty_response_for_blank_query(self) -> None:
        payload = SearchService().search("   ")

        self.assertEqual(payload["query"], "   ")
        self.assertEqual(payload["results"], [])
        self.assertEqual(payload["answer"]["confidence"], "none")

    def test_index_task_excludes_dismissed_tasks_from_search(self) -> None:
        task = self.fixture.create_task("Dismissed Search", candidate_status="pending")
        service = SearchService()
        service.index_task(str(task.id))

        db = SessionLocal()
        try:
            record = db.get(type(task), task.id)
            record.candidate_status = "dismissed"
            db.commit()
        finally:
            db.close()

        service.index_task(str(task.id))

        self.assertEqual(self.fixture.search_documents("task"), [])

    def test_build_rag_answer_aggregates_person_confidence_and_evidence(self) -> None:
        result = {
            "target_type": "interaction",
            "target_id": "interaction-1",
            "title": "career note",
            "summary": "career summary",
            "score": 0.82,
            "person_id": "person-1",
            "person_name": "Alice",
            "community_path": "Team",
            "topic_path": "Career",
        }

        answer = build_rag_answer(
            "career",
            [result],
            {"tasks": [], "calendar_events": [], "topics": [], "communities": []},
        )

        self.assertEqual(answer["confidence"], "high")
        self.assertEqual(answer["primary_person"]["person_id"], "person-1")
        self.assertEqual(answer["evidence"][0]["title"], "career note")
        self.assertTrue(answer["follow_up_queries"])

    def test_embedding_provider_uses_local_fallback_without_api_key(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            provider = SearchEmbeddingProvider()
            vector, model = provider.embed("local fallback text")

        self.assertEqual(model, "local-hash-v1")
        self.assertEqual(len(vector), provider.dimension)

    def test_embedding_provider_falls_back_when_openai_request_fails(self) -> None:
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False),
            patch.object(
                SearchEmbeddingProvider,
                "_embed_with_openai",
                side_effect=RuntimeError("boom"),
            ),
            patch("backend.services.search.embedding.logger.exception"),
        ):
            provider = SearchEmbeddingProvider()
            vector, model = provider.embed("fallback after failure")

        self.assertEqual(model, "local-hash-v1")
        self.assertEqual(len(vector), provider.dimension)

    def test_search_utils_parse_embedding_handles_invalid_json(self) -> None:
        self.assertEqual(parse_embedding("not-json"), [])
        self.assertEqual(parse_embedding('{"bad": true}'), [])
        self.assertEqual(parse_embedding("[1, 2.5, \"x\"]"), [1.0, 2.5])

    def test_search_utils_scores_keyword_exact_title_and_partial_matches(self) -> None:
        document = SearchDocument(
            title="Important Career Plan",
            summary="Discussed interview preparation",
            search_text="career plan interview preparation",
        )

        score = calculate_keyword_score("Career Plan", document)

        self.assertGreaterEqual(score, 0.8)

    def test_search_utils_extract_snippet_prefers_query_neighborhood(self) -> None:
        document = SearchDocument(
            title="Snippet",
            summary=None,
            search_text=f"{'a' * 120} target phrase {'b' * 120}",
        )

        snippet = extract_snippet("target phrase", document, length=80)

        self.assertIn("target phrase", snippet)
        self.assertTrue(snippet.startswith("..."))

    def test_search_result_grouping_groups_by_supported_target_types(self) -> None:
        grouped = SearchService()._group_results(
            [
                {"target_type": "person", "title": "A"},
                {"target_type": "interaction", "title": "B"},
                {"target_type": "task", "title": "C"},
                {"target_type": "calendar_event", "title": "D"},
                {"target_type": "community", "title": "E"},
                {"target_type": "topic", "title": "F"},
            ]
        )

        self.assertEqual(len(grouped["people"]), 1)
        self.assertEqual(len(grouped["interactions"]), 1)
        self.assertEqual(len(grouped["tasks"]), 1)
        self.assertEqual(len(grouped["calendar_events"]), 1)
        self.assertEqual(len(grouped["communities"]), 1)
        self.assertEqual(len(grouped["topics"]), 1)

    def test_search_endpoint_rejects_unknown_target_type(self) -> None:
        response = self.client.get(
            "/api/search",
            params={"q": "anything", "target_type": "unknown"},
        )

        self.assertEqual(response.status_code, 400)

    def test_search_normalize_target_types_deduplicates_and_sorts(self) -> None:
        normalized = SearchService()._normalize_target_types(["task", "person", "task"])

        self.assertEqual(normalized, ["person", "task"])

    def test_search_normalize_target_types_raises_for_unknown(self) -> None:
        with self.assertRaises(HTTPException) as context:
            SearchService()._normalize_target_types(["bad"])

        self.assertEqual(context.exception.status_code, 400)

    def test_search_cache_is_invalidated_after_person_mutation(self) -> None:
        account_id = get_current_account_id()
        SearchService._document_cache[account_id] = tuple()

        PersonService().create_person(
            name=f"{self.prefix} Cache Person",
            canonical_name=f"{self.prefix}:cache-person",
        )

        self.assertNotIn(account_id, SearchService._document_cache)

    def test_search_utils_vector_and_text_helpers(self) -> None:
        self.assertEqual(normalize_vector([0.0, 0.0]), [0.0, 0.0])
        self.assertEqual(cosine_similarity([1.0], [1.0, 0.0]), 0.0)
        self.assertEqual(compact_text(" a  b ", 20), "a b")
        self.assertEqual(first_non_empty(None, "  ", "x"), "x")
        self.assertEqual(join_search_parts([" a ", None, "b"]), "a\nb")

    def test_search_utils_recency_prefers_recent_documents(self) -> None:
        old_at = datetime.now(timezone.utc) - timedelta(days=365)
        recent_at = datetime.now(timezone.utc)

        self.assertLess(calculate_recency_score(old_at), calculate_recency_score(recent_at))


if __name__ == "__main__":
    unittest.main(verbosity=2)
