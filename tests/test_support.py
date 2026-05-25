from __future__ import annotations

from datetime import datetime, timezone
import time
from uuid import UUID, uuid4

from sqlalchemy import delete as sa_delete, or_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload

from backend.app.account_context import DEFAULT_ACCOUNT_EMAIL, get_current_account_id
from backend.db.session import SessionLocal, engine
from backend.models.account.account import Account
from backend.models.base.enums import InteractionType, ShareLevel, TaskStatus
from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.calendar.event_participant import EventParticipant
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.reminder.reminder import Reminder
from backend.models.search.search_document import SearchDocument
from backend.models.search.search_log import SearchLog
from backend.models.task.task import Task
from backend.models.task.task_link import TaskLink
from backend.services.search import SearchService


def unique_prefix(label: str) -> str:
    return f"[TEST:{label}:{uuid4().hex[:8]}]"


def ensure_default_account() -> UUID:
    account_id = get_current_account_id()
    last_error: OperationalError | None = None
    for attempt in range(5):
        try:
            _ensure_default_account_once(account_id)
            return account_id
        except OperationalError as exc:
            last_error = exc
            engine.dispose()
            time.sleep(1 + attempt)
    if last_error is not None:
        raise last_error
    return account_id


def _ensure_default_account_once(account_id: UUID) -> None:
    db = SessionLocal()
    try:
        account = db.get(Account, account_id)
        if account is None:
            db.add(Account(id=account_id, email=DEFAULT_ACCOUNT_EMAIL))
            db.commit()
    finally:
        db.close()


def cleanup_test_data(prefix: str) -> None:
    last_error: OperationalError | None = None
    for attempt in range(5):
        try:
            _cleanup_test_data_once(prefix)
            return
        except OperationalError as exc:
            last_error = exc
            engine.dispose()
            time.sleep(1 + attempt)
    if last_error is not None:
        print(f"cleanup skipped after database connection failures for {prefix}: {last_error}")


def _cleanup_test_data_once(prefix: str) -> None:
    db = SessionLocal()
    try:
        account_id = get_current_account_id()
        people = (
            db.query(Person)
            .filter(Person.account_id == account_id)
            .filter(
                or_(
                    Person.name.like(f"{prefix}%"),
                    Person.canonical_name.like(f"{prefix}%"),
                    Person.description.like(f"{prefix}%"),
                )
            )
            .all()
        )
        communities = (
            db.query(Community)
            .filter(Community.account_id == account_id)
            .filter(
                or_(
                    Community.name.like(f"{prefix}%"),
                    Community.description.like(f"{prefix}%"),
                )
            )
            .all()
        )
        topics = (
            db.query(Topic)
            .filter(Topic.account_id == account_id)
            .filter(
                or_(
                    Topic.name.like(f"{prefix}%"),
                    Topic.description.like(f"{prefix}%"),
                )
            )
            .all()
        )
        reminders = (
            db.query(Reminder)
            .filter(Reminder.account_id == account_id)
            .filter(
                or_(
                    Reminder.title.like(f"{prefix}%"),
                    Reminder.message.like(f"{prefix}%"),
                )
            )
            .all()
        )
        calendar_events = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.account_id == account_id)
            .filter(
                or_(
                    CalendarEvent.title.like(f"{prefix}%"),
                    CalendarEvent.description.like(f"{prefix}%"),
                    CalendarEvent.external_id.like(f"{prefix}%"),
                )
            )
            .all()
        )
        tasks = (
            db.query(Task)
            .filter(Task.account_id == account_id)
            .filter(
                or_(
                    Task.title.like(f"{prefix}%"),
                    Task.description.like(f"{prefix}%"),
                )
            )
            .all()
        )

        person_ids = [item.id for item in people]
        community_ids = [item.id for item in communities]
        topic_ids = [item.id for item in topics]
        event_ids = [item.id for item in calendar_events]
        task_ids = [item.id for item in tasks]

        interaction_filters = [Interaction.note.like(f"{prefix}%"), Interaction.content.like(f"{prefix}%")]
        if person_ids:
            interaction_filters.append(Interaction.person_id.in_(person_ids))
        if community_ids:
            interaction_filters.append(Interaction.community_id.in_(community_ids))
        if topic_ids:
            interaction_filters.append(Interaction.topic_id.in_(topic_ids))

        interactions = (
            db.query(Interaction)
            .filter(Interaction.account_id == account_id)
            .filter(or_(*interaction_filters))
            .all()
        )
        interaction_ids = [item.id for item in interactions]

        search_target_filters = [
            SearchDocument.title.like(f"{prefix}%"),
            SearchDocument.summary.like(f"{prefix}%"),
            SearchDocument.search_text.like(f"%{prefix}%"),
        ]
        for target_type, ids in (
            ("person", person_ids),
            ("community", community_ids),
            ("topic", topic_ids),
            ("interaction", interaction_ids),
            ("calendar_event", event_ids),
            ("task", task_ids),
        ):
            if ids:
                search_target_filters.append(
                    (SearchDocument.target_type == target_type)
                    & SearchDocument.target_id.in_(ids)
                )
        db.execute(
            sa_delete(SearchDocument).where(
                SearchDocument.account_id == account_id,
                or_(*search_target_filters),
            )
        )
        search_log_filters = [SearchLog.query.like(f"%{prefix}%")]
        for ids in (person_ids, community_ids, topic_ids, interaction_ids, event_ids, task_ids):
            if ids:
                search_log_filters.append(SearchLog.top_result_id.in_(ids))
        db.execute(
            sa_delete(SearchLog).where(
                SearchLog.account_id == account_id,
                or_(*search_log_filters),
            )
        )

        if task_ids:
            db.execute(sa_delete(TaskLink).where(TaskLink.task_id.in_(task_ids)))
        if event_ids:
            db.execute(
                sa_delete(EventParticipant).where(
                    EventParticipant.calendar_event_id.in_(event_ids)
                )
            )

        for item in interactions:
            db.delete(item)
        for item in tasks:
            db.delete(item)
        for item in calendar_events:
            db.delete(item)
        for item in reminders:
            db.delete(item)
        for item in people:
            db.delete(item)
        db.flush()
        for item in topics:
            db.delete(item)
        db.flush()
        for item in communities:
            db.delete(item)

        db.commit()
    finally:
        db.close()
        SearchService.invalidate_cache()


class DbFixture:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.account_id = ensure_default_account()

    def create_community(
        self,
        name: str = "Community",
        parent: Community | None = None,
        hidden: bool = False,
    ) -> Community:
        db = SessionLocal()
        try:
            item = Community(
                account_id=self.account_id,
                name=f"{self.prefix} {name}",
                description=f"{self.prefix} community",
                parent_id=parent.id if parent else None,
                is_hidden=hidden,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def create_topic(self, name: str = "Topic", parent: Topic | None = None) -> Topic:
        db = SessionLocal()
        try:
            item = Topic(
                account_id=self.account_id,
                title=f"{self.prefix} {name}",
                name=f"{self.prefix} {name}",
                description=f"{self.prefix} topic",
                parent_id=parent.id if parent else None,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def create_person(
        self,
        name: str = "Person",
        primary_community: Community | None = None,
        hidden: bool = False,
        canonical: str | None = None,
    ) -> Person:
        db = SessionLocal()
        try:
            item = Person(
                account_id=self.account_id,
                name=f"{self.prefix} {name}",
                canonical_name=canonical or f"{self.prefix}:{name}:{uuid4().hex[:6]}",
                description=f"{self.prefix} person",
                primary_community_id=primary_community.id if primary_community else None,
                is_hidden=hidden,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def create_interaction(
        self,
        person: Person,
        community: Community | None = None,
        topic: Topic | None = None,
        content: str = "follow up by 2026-05-25",
        note: str | None = None,
        occurred_at: datetime | None = None,
        share_level: ShareLevel = ShareLevel.SHARED,
        interaction_type: InteractionType = InteractionType.MEETING,
    ) -> Interaction:
        db = SessionLocal()
        try:
            item = Interaction(
                account_id=self.account_id,
                person_id=person.id,
                community_id=community.id if community else None,
                topic_id=topic.id if topic else None,
                type=interaction_type,
                share_level=share_level,
                occurred_at=occurred_at or datetime.now(timezone.utc),
                content=f"{self.prefix} {content}",
                note=note if note is not None else f"{self.prefix} note",
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def create_task(
        self,
        title: str = "Task",
        description: str | None = None,
        is_candidate: bool = True,
        candidate_status: str = "pending",
        status: TaskStatus = TaskStatus.TODO,
        due_at: datetime | None = None,
        source_type: str = "manual_note",
        source_id=None,
        links: list[tuple[str, UUID, str, float | None]] | None = None,
    ) -> Task:
        db = SessionLocal()
        try:
            task = Task(
                account_id=self.account_id,
                title=f"{self.prefix} {title}",
                description=description or f"{self.prefix} task description",
                status=status,
                due_at=due_at,
                source_type=source_type,
                source_id=source_id,
                is_candidate=is_candidate,
                candidate_status=candidate_status,
                confidence=0.9,
            )
            db.add(task)
            db.flush()
            for target_type, target_id, role, confidence in links or []:
                db.add(
                    TaskLink(
                        account_id=self.account_id,
                        task_id=task.id,
                        target_type=target_type,
                        target_id=target_id,
                        role=role,
                        confidence=confidence,
                    )
                )
            db.commit()
            db.refresh(task)
            return task
        finally:
            db.close()

    def load_task(self, task_id: UUID) -> Task:
        db = SessionLocal()
        try:
            normalized_id = UUID(str(task_id))
            return (
                db.query(Task)
                .options(joinedload(Task.links))
                .filter(Task.id == normalized_id, Task.account_id == self.account_id)
                .one()
            )
        finally:
            db.close()

    def create_calendar_event(
        self,
        title: str = "Event",
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        external_id: str | None = None,
    ) -> CalendarEvent:
        db = SessionLocal()
        try:
            start = start_at or datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc)
            end = end_at or datetime(2026, 5, 23, 11, 0, tzinfo=timezone.utc)
            item = CalendarEvent(
                account_id=self.account_id,
                external_id=external_id or f"{self.prefix}:event:{uuid4().hex[:6]}",
                title=f"{self.prefix} {title}",
                description=f"{self.prefix} event",
                location=f"{self.prefix} room",
                start_at=start,
                end_at=end,
                source="manual",
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def search_documents(self, target_type: str | None = None) -> list[SearchDocument]:
        db = SessionLocal()
        try:
            query = db.query(SearchDocument).filter(
                SearchDocument.account_id == self.account_id,
                SearchDocument.search_text.like(f"%{self.prefix}%"),
            )
            if target_type:
                query = query.filter(SearchDocument.target_type == target_type)
            return query.all()
        finally:
            db.close()
