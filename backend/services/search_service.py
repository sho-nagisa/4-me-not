from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from threading import RLock
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session, joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.base.enums import TaskStatus
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.calendar.event_participant import EventParticipant
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument
from backend.models.task.task import Task
from backend.services.search_answer import build_rag_answer, empty_rag_answer
from backend.services.search_constants import (
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_COMMUNITY,
    TARGET_TOPIC,
    TARGET_TASK,
    TARGET_CALENDAR_EVENT,
    ALLOWED_TARGET_TYPES,
    GROUP_KEYS,
)
from backend.services.search_embedding import SearchEmbeddingProvider
from backend.services.search_utils import (
    calculate_keyword_score,
    calculate_recency_score,
    compact_text,
    cosine_similarity,
    extract_snippet,
    first_non_empty,
    join_search_parts,
    normalize_uuid,
    parse_embedding,
    task_status_label,
)


@dataclass(frozen=True)
class CachedSearchDocument:
    id: UUID
    target_type: str
    target_id: UUID
    title: str
    summary: str | None
    search_text: str
    embedding: tuple[float, ...]
    occurred_at: datetime | None
    indexed_at: datetime
    created_at: datetime
    person_id: UUID | None
    person_name: str | None
    community_id: UUID | None
    community_path: str | None
    topic_id: UUID | None
    topic_path: str | None
    due_at: datetime | None
    status: str | None
    status_label: str | None
    source_type: str | None
    is_candidate: bool
    candidate_status: str | None
    start_at: datetime | None
    end_at: datetime | None
    location: str | None
    target_label: str | None


class SearchService:
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

        return {
            "query": query,
            "embedding_model": query_embedding_model,
            "results": limited_results,
            "groups": groups,
            "answer": build_rag_answer(normalized_query, limited_results, groups),
        }

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

            for person in people:
                self._index_person(db, account_id, person)
            for community in communities:
                self._index_community(db, account_id, community)
            for topic in topics:
                self._index_topic(db, account_id, topic)
            for interaction in interactions:
                self._index_interaction(db, account_id, interaction)
            for task in tasks:
                self._index_task(db, account_id, task)
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

    def _index_interaction(
        self,
        db: Session,
        account_id: UUID,
        interaction: Interaction,
    ) -> None:
        community_path = self._build_path(interaction.community)
        topic_path = self._build_path(interaction.topic)
        content = compact_text(interaction.content)
        note = compact_text(interaction.note)
        title_parts = [interaction.person.name if interaction.person else "Interaction"]
        if topic_path:
            title_parts.append(topic_path)
        title = " - ".join(title_parts)
        summary = first_non_empty(content, note, topic_path, community_path)
        search_text = join_search_parts(
            [
                "type: interaction",
                f"person: {interaction.person.name if interaction.person else ''}",
                f"community: {community_path or ''}",
                f"topic: {topic_path or ''}",
                f"content: {interaction.content or ''}",
                f"note: {interaction.note or ''}",
                f"occurred_at: {interaction.occurred_at.isoformat() if interaction.occurred_at else ''}",
            ]
        )
        self._upsert_document(
            db=db,
            account_id=account_id,
            target_type=TARGET_INTERACTION,
            target_id=interaction.id,
            title=title[:200],
            summary=summary,
            search_text=search_text,
            occurred_at=interaction.occurred_at,
            person_id=interaction.person_id,
            community_id=interaction.community_id
            if interaction.community and not interaction.community.is_hidden
            else None,
            topic_id=interaction.topic_id,
        )

    def _index_person(
        self,
        db: Session,
        account_id: UUID,
        person: Person,
    ) -> None:
        if person.is_hidden:
            return

        interactions = (
            self._visible_interactions_query(db, account_id)
            .filter(Interaction.person_id == person.id)
            .limit(20)
            .all()
        )
        primary_community_path = self._build_path(person.primary_community)
        latest_occurred_at = next(
            (item.occurred_at for item in interactions if item.occurred_at),
            None,
        )
        interaction_lines = [
            self._build_interaction_line(interaction)
            for interaction in interactions[:12]
        ]
        title = person.name
        summary = primary_community_path or compact_text(person.description)
        search_text = join_search_parts(
            [
                "type: person",
                f"name: {person.name}",
                f"canonical_name: {person.canonical_name or ''}",
                f"primary_community: {primary_community_path or ''}",
                f"description: {person.description or ''}",
                "recent_interactions:",
                *interaction_lines,
            ]
        )
        self._upsert_document(
            db=db,
            account_id=account_id,
            target_type=TARGET_PERSON,
            target_id=person.id,
            title=title[:200],
            summary=summary,
            search_text=search_text,
            occurred_at=latest_occurred_at or person.updated_at,
            person_id=person.id,
            community_id=person.primary_community_id
            if person.primary_community and not person.primary_community.is_hidden
            else None,
            topic_id=None,
        )

    def _index_community(
        self,
        db: Session,
        account_id: UUID,
        community: Community,
    ) -> None:
        if community.is_hidden:
            return

        path = self._build_path(community)
        interactions = (
            self._visible_interactions_query(db, account_id)
            .filter(Interaction.community_id == community.id)
            .limit(20)
            .all()
        )
        people = (
            db.query(Person)
            .filter(
                Person.account_id == account_id,
                Person.is_hidden.is_(False),
                Person.primary_community_id == community.id,
            )
            .order_by(Person.name.asc())
            .limit(30)
            .all()
        )
        latest_occurred_at = next(
            (item.occurred_at for item in interactions if item.occurred_at),
            None,
        )
        search_text = join_search_parts(
            [
                "type: community",
                f"name: {community.name}",
                f"path: {path or community.name}",
                f"description: {community.description or ''}",
                "people:",
                ", ".join(person.name for person in people),
                "recent_interactions:",
                *[self._build_interaction_line(interaction) for interaction in interactions[:12]],
            ]
        )
        self._upsert_document(
            db=db,
            account_id=account_id,
            target_type=TARGET_COMMUNITY,
            target_id=community.id,
            title=(path or community.name)[:200],
            summary=compact_text(community.description) or path,
            search_text=search_text,
            occurred_at=latest_occurred_at or community.updated_at,
            person_id=None,
            community_id=community.id,
            topic_id=None,
        )

    def _index_topic(
        self,
        db: Session,
        account_id: UUID,
        topic: Topic,
    ) -> None:
        path = self._build_path(topic)
        interactions = (
            self._visible_interactions_query(db, account_id)
            .filter(Interaction.topic_id == topic.id)
            .limit(20)
            .all()
        )
        latest_occurred_at = next(
            (item.occurred_at for item in interactions if item.occurred_at),
            None,
        )
        people = []
        seen_people = set()
        for interaction in interactions:
            if not interaction.person or interaction.person_id in seen_people:
                continue
            seen_people.add(interaction.person_id)
            people.append(interaction.person.name)

        search_text = join_search_parts(
            [
                "type: topic",
                f"name: {topic.name}",
                f"path: {path or topic.name}",
                f"description: {topic.description or ''}",
                "people:",
                ", ".join(people),
                "recent_interactions:",
                *[self._build_interaction_line(interaction) for interaction in interactions[:12]],
            ]
        )
        self._upsert_document(
            db=db,
            account_id=account_id,
            target_type=TARGET_TOPIC,
            target_id=topic.id,
            title=(path or topic.name)[:200],
            summary=compact_text(topic.description) or path,
            search_text=search_text,
            occurred_at=latest_occurred_at or topic.updated_at,
            person_id=None,
            community_id=None,
            topic_id=topic.id,
        )

    def _index_task(
        self,
        db: Session,
        account_id: UUID,
        task: Task,
    ) -> None:
        if task.candidate_status == "dismissed":
            return

        links = list(task.links)
        person_ids = [
            link.target_id for link in links if link.target_type == TARGET_PERSON
        ]
        community_ids = [
            link.target_id for link in links if link.target_type == TARGET_COMMUNITY
        ]
        topic_ids = [
            link.target_id for link in links if link.target_type == TARGET_TOPIC
        ]

        people = (
            db.query(Person)
            .filter(
                Person.account_id == account_id,
                Person.id.in_(person_ids),
                Person.is_hidden.is_(False),
            )
            .all()
            if person_ids
            else []
        )
        communities = (
            db.query(Community)
            .filter(
                Community.account_id == account_id,
                Community.id.in_(community_ids),
                Community.is_hidden.is_(False),
            )
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
        people_by_id = {person.id: person for person in people}
        communities_by_id = {community.id: community for community in communities}
        topics_by_id = {topic.id: topic for topic in topics}

        primary_person = next(
            (people_by_id[person_id] for person_id in person_ids if person_id in people_by_id),
            None,
        )
        primary_community = next(
            (
                communities_by_id[community_id]
                for community_id in community_ids
                if community_id in communities_by_id
            ),
            None,
        )
        primary_topic = next(
            (topics_by_id[topic_id] for topic_id in topic_ids if topic_id in topics_by_id),
            None,
        )
        people_names = ", ".join(person.name for person in people)
        community_paths = ", ".join(
            path for path in (self._build_path(community) for community in communities) if path
        )
        topic_paths = ", ".join(
            path for path in (self._build_path(topic) for topic in topics) if path
        )
        status_label = task_status_label(task.status)
        candidate_label = "候補" if task.is_candidate else "確定"
        due_text = task.due_at.isoformat() if task.due_at else ""
        search_text = join_search_parts(
            [
                "type: task",
                f"title: {task.title}",
                f"description: {task.description or ''}",
                f"status: {status_label}",
                f"candidate: {candidate_label}",
                f"due_at: {due_text}",
                f"source_type: {task.source_type}",
                f"people: {people_names}",
                f"communities: {community_paths}",
                f"topics: {topic_paths}",
            ]
        )
        self._upsert_document(
            db=db,
            account_id=account_id,
            target_type=TARGET_TASK,
            target_id=task.id,
            title=task.title[:200],
            summary=compact_text(task.description) or f"{candidate_label} / {status_label}",
            search_text=search_text,
            occurred_at=task.due_at or task.updated_at,
            person_id=primary_person.id if primary_person else None,
            community_id=primary_community.id if primary_community else None,
            topic_id=primary_topic.id if primary_topic else None,
        )

    def _index_calendar_event(
        self,
        db: Session,
        account_id: UUID,
        calendar_event: CalendarEvent,
    ) -> None:
        participants = list(calendar_event.participants)
        people = [
            participant.person
            for participant in participants
            if participant.person and not participant.person.is_hidden
        ]
        participant_labels = [
            participant.person.name
            if participant.person
            else first_non_empty(participant.display_name, participant.email)
            for participant in participants
        ]
        participant_text = ", ".join(label for label in participant_labels if label)
        primary_person = people[0] if people else None
        search_text = join_search_parts(
            [
                "type: calendar_event",
                f"title: {calendar_event.title}",
                f"description: {calendar_event.description or ''}",
                f"location: {calendar_event.location or ''}",
                f"participants: {participant_text}",
                f"start_at: {calendar_event.start_at.isoformat()}",
                f"end_at: {calendar_event.end_at.isoformat()}",
                f"source: {calendar_event.source or ''}",
            ]
        )
        summary = first_non_empty(
            compact_text(calendar_event.description),
            calendar_event.location,
            participant_text,
        )
        self._upsert_document(
            db=db,
            account_id=account_id,
            target_type=TARGET_CALENDAR_EVENT,
            target_id=calendar_event.id,
            title=calendar_event.title[:200],
            summary=summary,
            search_text=search_text,
            occurred_at=calendar_event.start_at,
            person_id=primary_person.id if primary_person else None,
            community_id=None,
            topic_id=None,
        )

    def _upsert_document(
        self,
        db: Session,
        account_id: UUID,
        target_type: str,
        target_id: UUID,
        title: str,
        summary: str | None,
        search_text: str,
        occurred_at: datetime | None,
        person_id: UUID | None,
        community_id: UUID | None,
        topic_id: UUID | None,
    ) -> None:
        source_text_hash = hashlib.sha256(search_text.encode("utf-8")).hexdigest()
        document = (
            db.query(SearchDocument)
            .filter(
                SearchDocument.account_id == account_id,
                SearchDocument.target_type == target_type,
                SearchDocument.target_id == target_id,
            )
            .first()
        )
        should_embed = (
            document is None
            or document.source_text_hash != source_text_hash
            or not document.embedding_json
            or document.embedding_model != self.embedding_provider.preferred_model
        )
        if should_embed:
            embedding, embedding_model = self.embedding_provider.embed(search_text)
            embedding_json = json.dumps(embedding, separators=(",", ":"))
        else:
            embedding_model = document.embedding_model
            embedding_json = document.embedding_json

        now = datetime.now(timezone.utc)
        if document is None:
            document = SearchDocument(
                account_id=account_id,
                target_type=target_type,
                target_id=target_id,
            )
            db.add(document)

        document.person_id = person_id
        document.community_id = community_id
        document.topic_id = topic_id
        document.title = title or target_type
        document.summary = summary
        document.search_text = search_text
        document.source_text_hash = source_text_hash
        document.embedding_model = embedding_model
        document.embedding_json = embedding_json
        document.occurred_at = occurred_at
        document.indexed_at = now

    def _visible_interactions_query(self, db: Session, account_id: UUID):
        return (
            db.query(Interaction)
            .join(Person, Interaction.person_id == Person.id)
            .filter(
                Interaction.account_id == account_id,
                Person.account_id == account_id,
                Person.is_hidden.is_(False),
            )
            .options(
                joinedload(Interaction.person).joinedload(Person.primary_community),
                joinedload(Interaction.community).joinedload(Community.parent),
                joinedload(Interaction.topic).joinedload(Topic.parent),
            )
            .order_by(
                Interaction.occurred_at.desc().nullslast(),
                Interaction.created_at.desc(),
            )
        )

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
        db: Session = SessionLocal()
        try:
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
        finally:
            db.close()

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
        if record is None:
            return None

        nodes = []
        current = record
        seen_ids = set()
        while current is not None and current.id not in seen_ids:
            seen_ids.add(current.id)
            if not getattr(current, "is_hidden", False):
                nodes.append(current.name)
            parent_id = getattr(current, "parent_id", None)
            current = records_by_id.get(parent_id) if parent_id else None
        if not nodes:
            return None
        return " / ".join(reversed(nodes))

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

    def _delete_target_document(
        self,
        db: Session,
        account_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> None:
        db.execute(
            sa_delete(SearchDocument).where(
                SearchDocument.account_id == account_id,
                SearchDocument.target_type == target_type,
                SearchDocument.target_id == target_id,
            )
        )

    def _build_interaction_line(self, interaction: Interaction) -> str:
        topic_path = self._build_path(interaction.topic)
        community_path = self._build_path(interaction.community)
        happened = interaction.occurred_at.date().isoformat() if interaction.occurred_at else ""
        text = compact_text(first_non_empty(interaction.content, interaction.note), 160)
        return join_search_parts(
            [
                f"- {happened}",
                f"person: {interaction.person.name if interaction.person else ''}",
                f"community: {community_path or ''}",
                f"topic: {topic_path or ''}",
                f"text: {text}",
            ]
        )

    def _build_path(self, record) -> str | None:
        if record is None:
            return None

        nodes = []
        current = record
        while current is not None:
            if not getattr(current, "is_hidden", False):
                nodes.append(current.name)
            current = current.parent
        if not nodes:
            return None
        return " / ".join(reversed(nodes))

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
