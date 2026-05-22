from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException

from backend.models.search.search_document import SearchDocument
from backend.services.search.answer import empty_rag_answer
from backend.services.search.constants import (
    ALLOWED_TARGET_TYPES,
    GROUP_KEYS,
    TARGET_COMMUNITY,
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_TOPIC,
)
from backend.services.search.types import CachedSearchDocument
from backend.services.search.utils import extract_snippet


class SearchResultMixin:
    def _serialize_result(
        self,
        document: SearchDocument,
        score: float,
        semantic_score: float,
        keyword_score: float,
        recency_score: float,
        reference_maps: dict[str, dict[UUID, object]],
        query: str,
    ) -> dict:
        person_id = (
            document.target_id
            if document.target_type == TARGET_PERSON
            else document.person_id
        )
        community_id = (
            document.target_id
            if document.target_type == TARGET_COMMUNITY
            else document.community_id
        )
        topic_id = (
            document.target_id
            if document.target_type == TARGET_TOPIC
            else document.topic_id
        )
        person = reference_maps["people"].get(person_id) if person_id else None
        community = (
            reference_maps["communities"].get(community_id) if community_id else None
        )
        topic = reference_maps["topics"].get(topic_id) if topic_id else None

        return {
            "id": str(document.id),
            "target_type": document.target_type,
            "target_id": str(document.target_id),
            "title": document.title,
            "summary": document.summary,
            "snippet": extract_snippet(query, document),
            "score": round(score, 6),
            "semantic_score": round(semantic_score, 6),
            "keyword_score": round(keyword_score, 6),
            "recency_score": round(recency_score, 6),
            "person_id": str(person_id) if person_id else None,
            "person_name": person.name if person else None,
            "community_id": str(community_id) if community_id else None,
            "community_path": self._build_path(community) if community else None,
            "topic_id": str(topic_id) if topic_id else None,
            "topic_path": self._build_path(topic) if topic else None,
            "occurred_at": document.occurred_at.isoformat()
            if document.occurred_at
            else None,
            "indexed_at": document.indexed_at.isoformat(),
        }

    def _serialize_cached_result(
        self,
        document: CachedSearchDocument,
        score: float,
        semantic_score: float,
        keyword_score: float,
        recency_score: float,
        query: str,
    ) -> dict:
        return {
            "id": str(document.id),
            "target_type": document.target_type,
            "target_id": str(document.target_id),
            "title": document.title,
            "summary": document.summary,
            "snippet": extract_snippet(query, document),
            "score": round(score, 6),
            "semantic_score": round(semantic_score, 6),
            "keyword_score": round(keyword_score, 6),
            "recency_score": round(recency_score, 6),
            "person_id": str(document.person_id) if document.person_id else None,
            "person_name": document.person_name,
            "community_id": str(document.community_id)
            if document.community_id
            else None,
            "community_path": document.community_path,
            "topic_id": str(document.topic_id) if document.topic_id else None,
            "topic_path": document.topic_path,
            "due_at": document.due_at.isoformat() if document.due_at else None,
            "status": document.status,
            "status_label": document.status_label,
            "source_type": document.source_type,
            "is_candidate": document.is_candidate,
            "candidate_status": document.candidate_status,
            "start_at": document.start_at.isoformat() if document.start_at else None,
            "end_at": document.end_at.isoformat() if document.end_at else None,
            "location": document.location,
            "target_label": document.target_label,
            "occurred_at": document.occurred_at.isoformat()
            if document.occurred_at
            else None,
            "indexed_at": document.indexed_at.isoformat(),
        }

    def _group_results(self, results: list[dict]) -> dict[str, list[dict]]:
        grouped = {
            "people": [],
            "interactions": [],
            "tasks": [],
            "calendar_events": [],
            "communities": [],
            "topics": [],
        }
        for result in results:
            group_key = GROUP_KEYS.get(result["target_type"])
            if group_key:
                grouped[group_key].append(result)
        return grouped

    def _normalize_target_types(self, target_types: list[str] | None) -> list[str] | None:
        if not target_types:
            return None

        normalized = []
        for target_type in target_types:
            value = target_type.strip().lower()
            if value not in ALLOWED_TARGET_TYPES:
                raise HTTPException(status_code=400, detail="Unsupported target type")
            normalized.append(value)
        return sorted(set(normalized))

    def _empty_response(self, query: str) -> dict:
        return {
            "query": query,
            "embedding_model": None,
            "results": [],
            "groups": {
                "people": [],
                "interactions": [],
                "tasks": [],
                "calendar_events": [],
                "communities": [],
                "topics": [],
            },
            "answer": empty_rag_answer(),
        }
