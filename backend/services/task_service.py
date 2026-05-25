from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.base.enums import TaskStatus
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.task.task import Task
from backend.models.task.task_link import TaskLink


TASK_TARGET_PERSON = "person"
TASK_TARGET_COMMUNITY = "community"
TASK_TARGET_TOPIC = "topic"
TASK_TARGET_INTERACTION = "interaction"
TASK_TARGET_CALENDAR_EVENT = "calendar_event"

TASK_ROLE_SOURCE = "source"
TASK_ROLE_RELATED = "related"
TASK_ROLE_DEADLINE_FROM = "deadline_from"


TASK_KEYWORDS = (
    "todo",
    "to do",
    "タスク",
    "やること",
    "宿題",
    "対応",
    "確認",
    "返信",
    "連絡",
    "提出",
    "送る",
    "送付",
    "共有",
    "準備",
    "作成",
    "修正",
    "調整",
    "予約",
    "締め切り",
    "締切",
    "期限",
    "までに",
)


WEEKDAYS = {
    "月": 0,
    "火": 1,
    "水": 2,
    "木": 3,
    "金": 4,
    "土": 5,
    "日": 6,
}


@dataclass(frozen=True)
class ExtractedTaskCandidate:
    title: str
    description: str | None
    due_at: datetime | None
    confidence: float


class TaskService:
    def extract_candidates_from_interaction(self, interaction_id: str) -> list[str]:
        db: Session = SessionLocal()
        created_task_ids: list[str] = []
        try:
            account_id = get_current_account_id()
            interaction_uuid = self._normalize_uuid(interaction_id, "Interaction is invalid")
            interaction = (
                db.query(Interaction)
                .options(
                    joinedload(Interaction.person),
                    joinedload(Interaction.community),
                    joinedload(Interaction.topic),
                )
                .filter(
                    Interaction.id == interaction_uuid,
                    Interaction.account_id == account_id,
                )
                .first()
            )
            if interaction is None:
                return []

            text = "\n".join(
                item for item in (interaction.content, interaction.note) if item
            )
            candidates = extract_task_candidates(text, interaction.occurred_at)
            for candidate in candidates:
                if self._candidate_exists(
                    db=db,
                    account_id=account_id,
                    source_id=interaction.id,
                    title=candidate.title,
                ):
                    continue

                task = Task(
                    account_id=account_id,
                    title=candidate.title,
                    description=candidate.description,
                    status=TaskStatus.TODO,
                    due_at=candidate.due_at,
                    source_type=TASK_TARGET_INTERACTION,
                    source_id=interaction.id,
                    is_candidate=True,
                    candidate_status="pending",
                    confidence=candidate.confidence,
                )
                db.add(task)
                db.flush()

                self._add_link(
                    db,
                    task=task,
                    target_type=TASK_TARGET_INTERACTION,
                    target_id=interaction.id,
                    role=TASK_ROLE_SOURCE,
                    confidence=1.0,
                )
                self._add_link(
                    db,
                    task=task,
                    target_type=TASK_TARGET_PERSON,
                    target_id=interaction.person_id,
                    role=TASK_ROLE_RELATED,
                    confidence=0.85,
                )
                if interaction.community_id:
                    self._add_link(
                        db,
                        task=task,
                        target_type=TASK_TARGET_COMMUNITY,
                        target_id=interaction.community_id,
                        role=TASK_ROLE_RELATED,
                        confidence=0.65,
                    )
                if interaction.topic_id:
                    self._add_link(
                        db,
                        task=task,
                        target_type=TASK_TARGET_TOPIC,
                        target_id=interaction.topic_id,
                        role=TASK_ROLE_RELATED,
                        confidence=0.65,
                    )
                if candidate.due_at:
                    self._add_link(
                        db,
                        task=task,
                        target_type=TASK_TARGET_INTERACTION,
                        target_id=interaction.id,
                        role=TASK_ROLE_DEADLINE_FROM,
                        confidence=0.75,
                    )

                created_task_ids.append(str(task.id))

            db.commit()
            return created_task_ids
        finally:
            db.close()

    def list_tasks(
        self,
        include_candidates: bool = True,
        candidate_status: str | None = None,
        status: str | None = None,
        open_only: bool = False,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        db: Session = SessionLocal()
        try:
            account_id = get_current_account_id()
            query = (
                db.query(Task)
                .options(joinedload(Task.links))
                .filter(Task.account_id == account_id)
            )
            if not include_candidates:
                query = query.filter(Task.is_candidate.is_(False))
            if candidate_status:
                query = query.filter(Task.candidate_status == candidate_status)
            if open_only:
                query = query.filter(Task.status == TaskStatus.TODO)
            if status:
                query = query.filter(Task.status == self._normalize_status(status))
            if search and search.strip():
                pattern = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Task.title.ilike(pattern),
                        Task.description.ilike(pattern),
                    )
                )

            tasks = (
                query.order_by(
                    Task.due_at.asc().nullslast(),
                    Task.created_at.desc(),
                )
                .limit(limit)
                .all()
            )
            link_label_maps = self._build_link_label_maps(db, account_id, tasks)
            return [
                self.serialize_task(task, link_label_maps=link_label_maps)
                for task in tasks
            ]
        finally:
            db.close()

    def create_task(
        self,
        title: str,
        description: str | None = None,
        due_at: str | datetime | None = None,
        priority: int | None = None,
    ) -> dict:
        db: Session = SessionLocal()
        task_id: str | None = None
        try:
            account_id = get_current_account_id()
            task = Task(
                account_id=account_id,
                title=self._normalize_title(title),
                description=self._normalize_optional_text(description),
                status=TaskStatus.TODO,
                due_at=self._parse_optional_datetime(due_at),
                priority=self._normalize_priority(priority),
                source_type="manual",
                source_id=None,
                is_candidate=False,
                candidate_status="accepted",
                confidence=None,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            task_id = str(task.id)
            payload = self.serialize_task(task)
        finally:
            db.close()

        if task_id:
            self._index_task(task_id)
        return payload

    def update_task(
        self,
        task_id: str,
        changes: dict,
    ) -> dict:
        db: Session = SessionLocal()
        normalized_task_id: str | None = None
        try:
            account_id = get_current_account_id()
            task_uuid = self._normalize_uuid(task_id, "Task is invalid")
            task = (
                db.query(Task)
                .options(joinedload(Task.links))
                .filter(Task.id == task_uuid, Task.account_id == account_id)
                .first()
            )
            if task is None:
                raise HTTPException(status_code=404, detail="Task not found")

            if "title" in changes:
                task.title = self._normalize_title(changes["title"])
            if "description" in changes:
                task.description = self._normalize_optional_text(changes["description"])
            if "due_at" in changes:
                task.due_at = self._parse_optional_datetime(changes["due_at"])
            if "priority" in changes:
                task.priority = self._normalize_priority(changes["priority"])
            if "status" in changes:
                task.status = self._normalize_status(changes["status"])

            db.commit()
            db.refresh(task)
            normalized_task_id = str(task.id)
            payload = self.serialize_task(task)
        finally:
            db.close()

        if normalized_task_id:
            self._index_task(normalized_task_id)
        return payload

    def complete_task(self, task_id: str) -> dict:
        return self.update_task(task_id, {"status": "DONE"})

    def reopen_task(self, task_id: str) -> dict:
        return self.update_task(task_id, {"status": "TODO"})

    def accept_candidate(self, task_id: str) -> dict:
        return self._set_candidate_status(
            task_id=task_id,
            candidate_status="accepted",
            is_candidate=False,
        )

    def dismiss_candidate(self, task_id: str) -> dict:
        return self._set_candidate_status(
            task_id=task_id,
            candidate_status="dismissed",
            is_candidate=True,
        )

    def serialize_task(
        self,
        task: Task,
        link_label_maps: dict[str, dict[UUID, str]] | None = None,
    ) -> dict:
        label_maps = link_label_maps or {}
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": TaskStatus(task.status).name,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "priority": task.priority,
            "source_type": task.source_type,
            "source_id": str(task.source_id) if task.source_id else None,
            "is_candidate": bool(task.is_candidate),
            "candidate_status": task.candidate_status,
            "confidence": task.confidence,
            "links": [
                {
                    "target_type": link.target_type,
                    "target_id": str(link.target_id),
                    "target_label": label_maps.get(link.target_type, {}).get(
                        link.target_id
                    ),
                    "role": link.role,
                    "confidence": link.confidence,
                }
                for link in task.links
            ],
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }

    def _build_link_label_maps(
        self,
        db: Session,
        account_id: UUID,
        tasks: list[Task],
    ) -> dict[str, dict[UUID, str]]:
        ids_by_type: dict[str, set[UUID]] = {}
        for task in tasks:
            for link in task.links:
                ids_by_type.setdefault(link.target_type, set()).add(link.target_id)

        people = (
            db.query(Person)
            .filter(
                Person.account_id == account_id,
                Person.id.in_(ids_by_type.get(TASK_TARGET_PERSON, set())),
            )
            .all()
            if ids_by_type.get(TASK_TARGET_PERSON)
            else []
        )
        communities = (
            db.query(Community)
            .filter(
                Community.account_id == account_id,
                Community.id.in_(ids_by_type.get(TASK_TARGET_COMMUNITY, set())),
            )
            .all()
            if ids_by_type.get(TASK_TARGET_COMMUNITY)
            else []
        )
        topics = (
            db.query(Topic)
            .filter(
                Topic.account_id == account_id,
                Topic.id.in_(ids_by_type.get(TASK_TARGET_TOPIC, set())),
            )
            .all()
            if ids_by_type.get(TASK_TARGET_TOPIC)
            else []
        )

        return {
            TASK_TARGET_PERSON: {person.id: person.name for person in people},
            TASK_TARGET_COMMUNITY: {
                community.id: community.name for community in communities
            },
            TASK_TARGET_TOPIC: {topic.id: topic.name for topic in topics},
            TASK_TARGET_INTERACTION: {
                interaction_id: "会話記録"
                for interaction_id in ids_by_type.get(TASK_TARGET_INTERACTION, set())
            },
        }

    def _set_candidate_status(
        self,
        task_id: str,
        candidate_status: str,
        is_candidate: bool,
    ) -> dict:
        db: Session = SessionLocal()
        task: Task | None = None
        try:
            account_id = get_current_account_id()
            task_uuid = self._normalize_uuid(task_id, "Task is invalid")
            task = (
                db.query(Task)
                .options(joinedload(Task.links))
                .filter(Task.id == task_uuid, Task.account_id == account_id)
                .first()
            )
            if task is None:
                raise HTTPException(status_code=404, detail="Task not found")

            task.candidate_status = candidate_status
            task.is_candidate = is_candidate
            db.commit()
            db.refresh(task)
            payload = self.serialize_task(task)
        finally:
            db.close()

        if task is not None:
            self._index_task(str(task.id))
        return payload

    def _candidate_exists(
        self,
        db: Session,
        account_id: UUID,
        source_id: UUID,
        title: str,
    ) -> bool:
        return (
            db.query(Task.id)
            .filter(
                Task.account_id == account_id,
                Task.source_type == TASK_TARGET_INTERACTION,
                Task.source_id == source_id,
                Task.title == title,
                Task.candidate_status != "dismissed",
            )
            .first()
            is not None
        )

    def _add_link(
        self,
        db: Session,
        task: Task,
        target_type: str,
        target_id: UUID,
        role: str,
        confidence: float | None,
    ) -> None:
        db.add(
            TaskLink(
                account_id=task.account_id,
                task_id=task.id,
                target_type=target_type,
                target_id=target_id,
                role=role,
                confidence=confidence,
            )
        )

    def _normalize_uuid(self, value: str, detail: str) -> UUID:
        try:
            return UUID(str(value))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=detail) from exc

    def _index_task(self, task_id: str) -> None:
        from backend.services.search import SearchService

        SearchService().index_task(task_id)

    def _normalize_title(self, title: str | None) -> str:
        normalized = (title or "").strip()
        if not normalized:
            raise HTTPException(status_code=400, detail="Task title is required")
        if len(normalized) > 200:
            raise HTTPException(status_code=400, detail="Task title is too long")
        return normalized

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _normalize_priority(self, priority: int | None) -> int | None:
        if priority is None:
            return None
        if priority < 1 or priority > 5:
            raise HTTPException(status_code=400, detail="Task priority is invalid")
        return priority

    def _normalize_status(self, status: str | TaskStatus | int) -> TaskStatus:
        if isinstance(status, TaskStatus):
            return status
        if isinstance(status, int):
            try:
                return TaskStatus(status)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Task status is invalid") from exc
        value = str(status).strip().upper()
        try:
            return TaskStatus[value]
        except KeyError as exc:
            raise HTTPException(status_code=400, detail="Task status is invalid") from exc

    def _parse_optional_datetime(self, value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            parsed = value
        else:
            text = str(value).strip()
            if not text:
                return None
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Task due time is invalid") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed


def extract_task_candidates(
    text: str,
    base_at: datetime | None = None,
) -> list[ExtractedTaskCandidate]:
    if not text.strip():
        return []

    candidates: list[ExtractedTaskCandidate] = []
    seen_titles: set[str] = set()
    base = base_at or datetime.now(timezone.utc)
    for sentence in split_candidate_sentences(text):
        normalized = sentence.casefold()
        if not any(keyword in normalized for keyword in TASK_KEYWORDS):
            continue

        title = normalize_candidate_title(sentence)
        if not title or title in seen_titles:
            continue

        due_at = parse_due_at(sentence, base)
        confidence = 0.62
        if due_at:
            confidence += 0.18
        if any(marker in normalized for marker in ("todo", "タスク", "やること")):
            confidence += 0.12
        if any(marker in normalized for marker in ("締め切り", "締切", "期限", "までに")):
            confidence += 0.08

        seen_titles.add(title)
        candidates.append(
            ExtractedTaskCandidate(
                title=title,
                description=sentence,
                due_at=due_at,
                confidence=round(min(confidence, 0.95), 2),
            )
        )
        if len(candidates) >= 5:
            break

    return candidates


def split_candidate_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"[。！？!?。\n]+", normalized)
    return [part.strip(" ・-") for part in parts if len(part.strip()) >= 4]


def normalize_candidate_title(sentence: str) -> str:
    title = re.sub(r"^(TODO|ToDo|todo|タスク|やること)[:：\s-]*", "", sentence).strip()
    title = re.sub(r"\s+", " ", title)
    if len(title) > 120:
        title = title[:117].rstrip() + "..."
    return title


def parse_due_at(sentence: str, base_at: datetime) -> datetime | None:
    base = base_at
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    iso_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", sentence)
    if iso_match:
        year, month, day = (int(value) for value in iso_match.groups())
        return base.replace(year=year, month=month, day=day, hour=23, minute=59, second=0)

    jp_match = re.search(r"(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日", sentence)
    if jp_match:
        year_text, month_text, day_text = jp_match.groups()
        year = int(year_text) if year_text else base.year
        month = int(month_text)
        day = int(day_text)
        due_at = base.replace(year=year, month=month, day=day, hour=23, minute=59, second=0)
        if not year_text and due_at < base:
            due_at = due_at.replace(year=base.year + 1)
        return due_at

    if "明日" in sentence:
        return end_of_day(base + timedelta(days=1))
    if "あさって" in sentence or "明後日" in sentence:
        return end_of_day(base + timedelta(days=2))
    if "今日" in sentence or "本日" in sentence:
        return end_of_day(base)

    weekday_match = re.search(r"(来週)?([月火水木金土日])曜", sentence)
    if weekday_match:
        is_next_week = bool(weekday_match.group(1))
        target_weekday = WEEKDAYS[weekday_match.group(2)]
        days_ahead = (target_weekday - base.weekday()) % 7
        if days_ahead == 0 or is_next_week:
            days_ahead += 7
        return end_of_day(base + timedelta(days=days_ahead))

    if "来週" in sentence:
        return end_of_day(base + timedelta(days=7))

    return None


def end_of_day(value: datetime) -> datetime:
    return value.replace(hour=23, minute=59, second=0, microsecond=0)
