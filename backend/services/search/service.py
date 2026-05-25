from __future__ import annotations

import logging
from threading import RLock
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session, joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.calendar.event_participant import EventParticipant
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument
from backend.models.search.search_log import SearchLog
from backend.models.task.task import Task
from backend.services.search.answer import build_rag_answer
from backend.services.search.cache import SearchDocumentCacheMixin
from backend.services.search.constants import (
    TARGET_CALENDAR_EVENT,
    TARGET_COMMUNITY,
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_TASK,
    TARGET_TOPIC,
)
from backend.services.search.embedding import SearchEmbeddingProvider
from backend.services.search.indexing import SearchIndexingMixin
from backend.services.search.results import SearchResultMixin
from backend.services.search.types import CachedSearchDocument
from backend.services.search.utils import (
    calculate_keyword_score,
    calculate_recency_score,
    cosine_similarity,
    normalize_uuid,
)


logger = logging.getLogger(__name__)


class SearchService(SearchIndexingMixin, SearchDocumentCacheMixin, SearchResultMixin):
    _cache_lock = RLock()
    _document_cache: dict[UUID, tuple[CachedSearchDocument, ...]] = {}

    def __init__(self, embedding_provider: SearchEmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or SearchEmbeddingProvider()

    @classmethod
    def invalidate_cache(cls, account_id: UUID | None = None) -> None:
        with cls._cache_lock:
            if account_id is None:
                cls._document_cache.clear()
            else:
                cls._document_cache.pop(account_id, None)

    def search(
        self,
        query: str,
        limit: int = 20,
        target_types: list[str] | None = None,
    ) -> dict:
        normalized_query = query.strip()
        if not normalized_query:
            return self._empty_response(query)

        selected_target_types = self._normalize_target_types(target_types)
        query_embedding, query_embedding_model = self.embedding_provider.embed(
            normalized_query
        )

        account_id = get_current_account_id()
        documents = self._load_cached_candidate_documents(
            account_id=account_id,
            target_types=selected_target_types,
            limit=max(limit * 50, 300),
        )
        results = []

        for document in documents:
            semantic_score = cosine_similarity(
                query_embedding,
                document.embedding,
            )
            keyword_score = calculate_keyword_score(normalized_query, document)
            recency_score = calculate_recency_score(document.occurred_at)
            score = (
                0.55 * semantic_score
                + 0.35 * keyword_score
                + 0.10 * recency_score
            )

            if score <= 0:
                continue

            results.append(
                self._serialize_cached_result(
                    document=document,
                    score=score,
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    recency_score=recency_score,
                    query=normalized_query,
                )
            )

        results.sort(
            key=lambda item: (
                -item["score"],
                item["occurred_at"] is None,
                item["occurred_at"] or "",
                item["title"],
            )
        )
        limited_results = results[:limit]
        groups = self._group_results(limited_results)
        answer = build_rag_answer(normalized_query, limited_results, groups)
        self._record_search_log(
            account_id=account_id,
            query=normalized_query,
            target_types=selected_target_types,
            results=limited_results,
        )

        return {
            "query": query,
            "embedding_model": query_embedding_model,
            "results": limited_results,
            "groups": groups,
            "answer": answer,
        }

    def _record_search_log(
        self,
        account_id: UUID,
        query: str,
        target_types: list[str] | None,
        results: list[dict],
    ) -> None:
        top_result = results[0] if results else None
        db: Session = SessionLocal()
        try:
            db.add(
                SearchLog(
                    account_id=account_id,
                    query=query,
                    target_types=target_types or [],
                    result_count=len(results),
                    top_result_type=top_result["target_type"] if top_result else None,
                    top_result_id=UUID(top_result["target_id"])
                    if top_result
                    else None,
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to record search log")
        finally:
            db.close()

    def index_interaction(self, interaction_id: str) -> None:
        db: Session = SessionLocal()
        account_id: UUID | None = None
        try:
            account_id = get_current_account_id()
            interaction_uuid = normalize_uuid(interaction_id, "Interaction is invalid")
            interaction = (
                self._visible_interactions_query(db, account_id)
                .filter(Interaction.id == interaction_uuid)
                .first()
            )
            if interaction is None:
                self._delete_target_document(
                    db=db,
                    account_id=account_id,
                    target_type=TARGET_INTERACTION,
                    target_id=interaction_uuid,
                )
                db.commit()
                return

            self._index_interaction(db, account_id, interaction)
            if interaction.person:
                self._index_person(db, account_id, interaction.person)
            if interaction.community and not interaction.community.is_hidden:
                self._index_community(db, account_id, interaction.community)
            if interaction.topic:
                self._index_topic(db, account_id, interaction.topic)
            db.commit()
        finally:
            db.close()
            if account_id is not None:
                self.invalidate_cache(account_id)

    def index_task(self, task_id: str) -> None:
        db: Session = SessionLocal()
        account_id: UUID | None = None
        try:
            account_id = get_current_account_id()
            task_uuid = normalize_uuid(task_id, "Task is invalid")
            task = (
                db.query(Task)
                .options(joinedload(Task.links))
                .filter(Task.id == task_uuid, Task.account_id == account_id)
                .first()
            )
            if task is None or task.candidate_status == "dismissed":
                self._delete_target_document(
                    db=db,
                    account_id=account_id,
                    target_type=TARGET_TASK,
                    target_id=task_uuid,
                )
                db.commit()
                return

            self._index_task(db, account_id, task)
            db.commit()
        finally:
            db.close()
            if account_id is not None:
                self.invalidate_cache(account_id)

    def index_calendar_event(self, calendar_event_id: str) -> None:
        db: Session = SessionLocal()
        account_id: UUID | None = None
        try:
            account_id = get_current_account_id()
            event_uuid = normalize_uuid(calendar_event_id, "Calendar event is invalid")
            calendar_event = (
                db.query(CalendarEvent)
                .options(
                    joinedload(CalendarEvent.participants).joinedload(
                        EventParticipant.person
                    )
                )
                .filter(
                    CalendarEvent.id == event_uuid,
                    CalendarEvent.account_id == account_id,
                )
                .first()
            )
            if calendar_event is None:
                self._delete_target_document(
                    db=db,
                    account_id=account_id,
                    target_type=TARGET_CALENDAR_EVENT,
                    target_id=event_uuid,
                )
                db.commit()
                return

            self._index_calendar_event(db, account_id, calendar_event)
            db.commit()
        finally:
            db.close()
            if account_id is not None:
                self.invalidate_cache(account_id)

    def rebuild_account_index(self) -> dict[str, int]:
        db: Session = SessionLocal()
        account_id: UUID | None = None
        try:
            account_id = get_current_account_id()
            db.execute(
                sa_delete(SearchDocument).where(
                    SearchDocument.account_id == account_id
                )
            )

            people = (
                db.query(Person)
                .options(joinedload(Person.primary_community))
                .filter(Person.account_id == account_id, Person.is_hidden.is_(False))
                .all()
            )
            communities = (
                db.query(Community)
                .filter(Community.account_id == account_id, Community.is_hidden.is_(False))
                .all()
            )
            topics = (
                db.query(Topic)
                .filter(Topic.account_id == account_id)
                .all()
            )
            interactions = self._visible_interactions_query(db, account_id).all()
            tasks = (
                db.query(Task)
                .options(joinedload(Task.links))
                .filter(
                    Task.account_id == account_id,
                    Task.candidate_status != "dismissed",
                )
                .all()
            )
            calendar_events = (
                db.query(CalendarEvent)
                .options(
                    joinedload(CalendarEvent.participants).joinedload(
                        EventParticipant.person
                    )
                )
                .filter(CalendarEvent.account_id == account_id)
                .all()
            )

            interactions_by_person = self._group_interactions_by_field(
                interactions,
                "person_id",
            )
            interactions_by_community = self._group_interactions_by_field(
                interactions,
                "community_id",
            )
            interactions_by_topic = self._group_interactions_by_field(
                interactions,
                "topic_id",
            )
            people_by_primary_community = self._group_people_by_primary_community(
                people
            )
            task_reference_maps = {
                TARGET_PERSON: {person.id: person for person in people},
                TARGET_COMMUNITY: {
                    community.id: community for community in communities
                },
                TARGET_TOPIC: {topic.id: topic for topic in topics},
            }

            for person in people:
                self._index_person(
                    db,
                    account_id,
                    person,
                    interactions=interactions_by_person.get(person.id, []),
                )
            for community in communities:
                self._index_community(
                    db,
                    account_id,
                    community,
                    interactions=interactions_by_community.get(community.id, []),
                    people=people_by_primary_community.get(community.id, []),
                )
            for topic in topics:
                self._index_topic(
                    db,
                    account_id,
                    topic,
                    interactions=interactions_by_topic.get(topic.id, []),
                )
            for interaction in interactions:
                self._index_interaction(db, account_id, interaction)
            for task in tasks:
                self._index_task(
                    db,
                    account_id,
                    task,
                    link_reference_maps=task_reference_maps,
                )
            for calendar_event in calendar_events:
                self._index_calendar_event(db, account_id, calendar_event)

            db.commit()
            return {
                "people": len(people),
                "communities": len(communities),
                "topics": len(topics),
                "interactions": len(interactions),
                "tasks": len(tasks),
                "calendar_events": len(calendar_events),
            }
        finally:
            db.close()
            if account_id is not None:
                self.invalidate_cache(account_id)

    def _group_interactions_by_field(
        self,
        interactions: list[Interaction],
        field_name: str,
    ) -> dict[UUID, list[Interaction]]:
        grouped: dict[UUID, list[Interaction]] = {}
        for interaction in interactions:
            key = getattr(interaction, field_name)
            if key is None:
                continue
            grouped.setdefault(key, []).append(interaction)
        return grouped

    def _group_people_by_primary_community(
        self,
        people: list[Person],
    ) -> dict[UUID, list[Person]]:
        grouped: dict[UUID, list[Person]] = {}
        for person in sorted(people, key=lambda item: item.name):
            if person.primary_community_id is None:
                continue
            grouped.setdefault(person.primary_community_id, []).append(person)
        return grouped
