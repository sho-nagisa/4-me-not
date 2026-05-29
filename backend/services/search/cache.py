from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from backend.db.session import db_session
from backend.models.base.enums import TaskStatus
from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.calendar.event_participant import EventParticipant
from backend.models.community.community import Community
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument
from backend.models.task.task import Task
from backend.services.hierarchy_path import build_hierarchy_path_from_map
from backend.services.search.constants import (
    TARGET_CALENDAR_EVENT,
    TARGET_COMMUNITY,
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_TASK,
    TARGET_TOPIC,
)
from backend.services.search.types import CachedSearchDocument
from backend.services.search.utils import first_non_empty, parse_embedding, task_status_label


class SearchDocumentCacheMixin:
    def _load_candidate_documents(
        self,
        db: Session,
        account_id: UUID,
        target_types: list[str] | None,
        limit: int,
    ) -> list[SearchDocument]:
        query = db.query(SearchDocument).filter(SearchDocument.account_id == account_id)
        if target_types:
            query = query.filter(SearchDocument.target_type.in_(target_types))
        return (
            query.order_by(
                SearchDocument.occurred_at.desc().nullslast(),
                SearchDocument.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

    def _load_cached_candidate_documents(
        self,
        account_id: UUID,
        target_types: list[str] | None,
        limit: int,
    ) -> tuple[CachedSearchDocument, ...]:
        documents = self._get_cached_documents(account_id)
        if target_types:
            allowed_types = set(target_types)
            documents = tuple(
                document
                for document in documents
                if document.target_type in allowed_types
            )
        return documents[:limit]

    def _get_cached_documents(self, account_id: UUID) -> tuple[CachedSearchDocument, ...]:
        with self._cache_lock:
            cached = self._document_cache.get(account_id)
        if cached is not None:
            return cached

        documents = self._build_cached_documents(account_id)
        with self._cache_lock:
            cached = self._document_cache.setdefault(account_id, documents)
        return cached

    def _build_cached_documents(self, account_id: UUID) -> tuple[CachedSearchDocument, ...]:
        with db_session() as db:
            documents = self._load_candidate_documents(
                db=db,
                account_id=account_id,
                target_types=None,
                limit=10_000,
            )
            reference_maps = self._build_cached_reference_maps(
                db,
                account_id,
                documents,
            )
            detail_maps = self._build_cached_detail_maps(
                db,
                account_id,
                documents,
            )
            cached_documents = []

            for document in documents:
                if not self._document_is_visible(document, reference_maps):
                    continue

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
                    reference_maps["communities"].get(community_id)
                    if community_id
                    else None
                )
                topic = reference_maps["topics"].get(topic_id) if topic_id else None
                details = detail_maps.get(document.target_type, {}).get(
                    document.target_id,
                    {},
                )

                cached_documents.append(
                    CachedSearchDocument(
                        id=document.id,
                        target_type=document.target_type,
                        target_id=document.target_id,
                        title=document.title,
                        summary=document.summary,
                        search_text=document.search_text,
                        embedding=tuple(parse_embedding(document.embedding_json)),
                        occurred_at=document.occurred_at,
                        indexed_at=document.indexed_at,
                        created_at=document.created_at,
                        person_id=person_id,
                        person_name=person.name if person else None,
                        community_id=community_id,
                        community_path=self._build_cached_path(
                            community,
                            reference_maps["communities"],
                        )
                        if community
                        else None,
                        topic_id=topic_id,
                        topic_path=self._build_cached_path(
                            topic,
                            reference_maps["topics"],
                        )
                        if topic
                        else None,
                        due_at=details.get("due_at"),
                        status=details.get("status"),
                        status_label=details.get("status_label"),
                        source_type=details.get("source_type"),
                        is_candidate=bool(details.get("is_candidate", False)),
                        candidate_status=details.get("candidate_status"),
                        start_at=details.get("start_at"),
                        end_at=details.get("end_at"),
                        location=details.get("location"),
                        target_label=details.get("target_label"),
                    )
                )

            return tuple(cached_documents)

    def _build_cached_reference_maps(
        self,
        db: Session,
        account_id: UUID,
        documents: list[SearchDocument],
    ) -> dict[str, dict[UUID, object]]:
        person_ids: set[UUID] = set()
        for document in documents:
            if document.person_id:
                person_ids.add(document.person_id)
            if document.target_type == TARGET_PERSON:
                person_ids.add(document.target_id)

        people = (
            db.query(Person)
            .filter(Person.account_id == account_id, Person.id.in_(person_ids))
            .all()
            if person_ids
            else []
        )
        communities = (
            db.query(Community)
            .filter(Community.account_id == account_id)
            .all()
        )
        topics = (
            db.query(Topic)
            .filter(Topic.account_id == account_id)
            .all()
        )
        return {
            "people": {person.id: person for person in people},
            "communities": {community.id: community for community in communities},
            "topics": {topic.id: topic for topic in topics},
        }

    def _build_cached_detail_maps(
        self,
        db: Session,
        account_id: UUID,
        documents: list[SearchDocument],
    ) -> dict[str, dict[UUID, dict]]:
        task_ids = {
            document.target_id
            for document in documents
            if document.target_type == TARGET_TASK
        }
        calendar_event_ids = {
            document.target_id
            for document in documents
            if document.target_type == TARGET_CALENDAR_EVENT
        }

        tasks = (
            db.query(Task)
            .filter(Task.account_id == account_id, Task.id.in_(task_ids))
            .all()
            if task_ids
            else []
        )
        calendar_events = (
            db.query(CalendarEvent)
            .options(
                joinedload(CalendarEvent.participants).joinedload(
                    EventParticipant.person
                )
            )
            .filter(
                CalendarEvent.account_id == account_id,
                CalendarEvent.id.in_(calendar_event_ids),
            )
            .all()
            if calendar_event_ids
            else []
        )

        return {
            TARGET_TASK: {
                task.id: {
                    "due_at": task.due_at,
                    "status": TaskStatus(task.status).name,
                    "status_label": task_status_label(task.status),
                    "source_type": task.source_type,
                    "is_candidate": bool(task.is_candidate),
                    "candidate_status": task.candidate_status,
                }
                for task in tasks
            },
            TARGET_CALENDAR_EVENT: {
                event.id: {
                    "start_at": event.start_at,
                    "end_at": event.end_at,
                    "location": event.location,
                    "source_type": event.source,
                    "target_label": ", ".join(
                        label
                        for label in (
                            participant.person.name
                            if participant.person
                            else first_non_empty(
                                participant.display_name,
                                participant.email,
                            )
                            for participant in event.participants
                        )
                        if label
                    ),
                }
                for event in calendar_events
            },
        }

    def _build_cached_path(self, record, records_by_id: dict[UUID, object]) -> str | None:
        return build_hierarchy_path_from_map(record, records_by_id)

    def _build_reference_maps(
        self,
        db: Session,
        account_id: UUID,
        documents: list[SearchDocument],
    ) -> dict[str, dict[UUID, object]]:
        person_ids: set[UUID] = set()
        community_ids: set[UUID] = set()
        topic_ids: set[UUID] = set()
        for document in documents:
            if document.person_id:
                person_ids.add(document.person_id)
            if document.community_id:
                community_ids.add(document.community_id)
            if document.topic_id:
                topic_ids.add(document.topic_id)
            if document.target_type == TARGET_PERSON:
                person_ids.add(document.target_id)
            elif document.target_type == TARGET_COMMUNITY:
                community_ids.add(document.target_id)
            elif document.target_type == TARGET_TOPIC:
                topic_ids.add(document.target_id)

        people = (
            db.query(Person)
            .options(joinedload(Person.primary_community))
            .filter(Person.account_id == account_id, Person.id.in_(person_ids))
            .all()
            if person_ids
            else []
        )
        communities = (
            db.query(Community)
            .filter(Community.account_id == account_id, Community.id.in_(community_ids))
            .all()
            if community_ids
            else []
        )
        topics = (
            db.query(Topic)
            .filter(Topic.account_id == account_id, Topic.id.in_(topic_ids))
            .all()
            if topic_ids
            else []
        )
        return {
            "people": {person.id: person for person in people},
            "communities": {community.id: community for community in communities},
            "topics": {topic.id: topic for topic in topics},
        }

    def _document_is_visible(
        self,
        document: SearchDocument,
        reference_maps: dict[str, dict[UUID, object]],
    ) -> bool:
        if document.target_type == TARGET_INTERACTION and document.person_id is None:
            return False

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

        if person_id:
            person = reference_maps["people"].get(person_id)
            if person is None or person.is_hidden:
                return False

        if community_id:
            community = reference_maps["communities"].get(community_id)
            if community is None or community.is_hidden:
                return False

        if document.target_type == TARGET_TOPIC and topic_id:
            topic = reference_maps["topics"].get(topic_id)
            if topic is None:
                return False

        return True
