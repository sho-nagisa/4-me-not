from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session, joinedload

from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument
from backend.models.task.task import Task
from backend.services.hierarchy_path import build_hierarchy_path
from backend.services.search.constants import (
    TARGET_CALENDAR_EVENT,
    TARGET_COMMUNITY,
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_TASK,
    TARGET_TOPIC,
)
from backend.services.search.utils import (
    compact_text,
    first_non_empty,
    join_search_parts,
    task_status_label,
)


class SearchIndexingMixin:
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
        interactions: list[Interaction] | None = None,
    ) -> None:
        if person.is_hidden:
            return

        if interactions is None:
            interactions = (
                self._visible_interactions_query(db, account_id)
                .filter(Interaction.person_id == person.id)
                .limit(20)
                .all()
            )
        else:
            interactions = interactions[:20]

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
        interactions: list[Interaction] | None = None,
        people: list[Person] | None = None,
    ) -> None:
        if community.is_hidden:
            return

        path = self._build_path(community)
        if interactions is None:
            interactions = (
                self._visible_interactions_query(db, account_id)
                .filter(Interaction.community_id == community.id)
                .limit(20)
                .all()
            )
        else:
            interactions = interactions[:20]

        if people is None:
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
        else:
            people = people[:30]

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
        interactions: list[Interaction] | None = None,
    ) -> None:
        path = self._build_path(topic)
        if interactions is None:
            interactions = (
                self._visible_interactions_query(db, account_id)
                .filter(Interaction.topic_id == topic.id)
                .limit(20)
                .all()
            )
        else:
            interactions = interactions[:20]

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
        link_reference_maps: dict[str, dict[UUID, object]] | None = None,
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

        if link_reference_maps is None:
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
        else:
            people = [
                link_reference_maps[TARGET_PERSON][person_id]
                for person_id in person_ids
                if person_id in link_reference_maps[TARGET_PERSON]
            ]
            communities = [
                link_reference_maps[TARGET_COMMUNITY][community_id]
                for community_id in community_ids
                if community_id in link_reference_maps[TARGET_COMMUNITY]
            ]
            topics = [
                link_reference_maps[TARGET_TOPIC][topic_id]
                for topic_id in topic_ids
                if topic_id in link_reference_maps[TARGET_TOPIC]
            ]

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
        return build_hierarchy_path(record)
