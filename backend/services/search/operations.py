from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import db_session
from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.calendar.event_participant import EventParticipant
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument
from backend.models.task.task import Task
from backend.services.search.constants import (
    TARGET_CALENDAR_EVENT,
    TARGET_COMMUNITY,
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_TASK,
    TARGET_TOPIC,
)
from backend.services.search.utils import normalize_uuid


class SearchIndexOperationsMixin:
    def index_interaction(self, interaction_id: str) -> None:
        account_id: UUID | None = None
        try:
            with db_session() as db:
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
            if account_id is not None:
                self.invalidate_cache(account_id)

    def index_task(self, task_id: str) -> None:
        account_id: UUID | None = None
        try:
            with db_session() as db:
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
            if account_id is not None:
                self.invalidate_cache(account_id)

    def index_calendar_event(self, calendar_event_id: str) -> None:
        account_id: UUID | None = None
        try:
            with db_session() as db:
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
            if account_id is not None:
                self.invalidate_cache(account_id)

    def rebuild_account_index(self) -> dict[str, int]:
        account_id: UUID | None = None
        try:
            with db_session() as db:
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
