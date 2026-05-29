from uuid import UUID

from fastapi import HTTPException

from backend.app.account_context import get_current_account_id
from backend.db.session import db_session
from backend.models.interaction.topic import Topic
from backend.services.hierarchy_path import (
    build_hierarchy_path,
    build_hierarchy_path_from_map,
)
from backend.services.search import SearchService


class TopicService:
    def __init__(self):
        self._path_cache: dict[str, str] = {}

    def create_topic(
        self,
        name: str,
        description: str | None = None,
        parent_id: str | None = None,
    ):
        with db_session() as db:
            account_id = get_current_account_id()
            normalized_parent_id = self._validate_parent_id(db, parent_id, account_id)
            topic = Topic(
                account_id=account_id,
                title=name,
                name=name,
                description=description,
                parent_id=normalized_parent_id,
            )
            db.add(topic)
            db.commit()
            db.refresh(topic)
            SearchService.invalidate_cache(account_id)
            return topic

    def list_topics(self):
        with db_session() as db:
            topics = (
                db.query(Topic)
                .filter(Topic.account_id == get_current_account_id())
                .all()
            )
            topics_by_id = {topic.id: topic for topic in topics}
            self._path_cache = {
                str(topic.id): build_hierarchy_path_from_map(topic, topics_by_id) or ""
                for topic in topics
            }
            topics.sort(key=lambda item: self._path_cache[str(item.id)])
            return topics

    def get_path(self, topic: Topic) -> str:
        cache_key = str(topic.id)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        with db_session() as db:
            account_id = get_current_account_id()
            current = db.get(Topic, topic.id)
            return (
                build_hierarchy_path(
                    current,
                    parent_getter=lambda item: (
                        db.get(Topic, item.parent_id) if item.parent_id else None
                    ),
                    scope_filter=lambda item: item.account_id == account_id,
                )
                or ""
            )

    def _validate_parent_id(self, db, parent_id: str | None, account_id: UUID):
        if not parent_id:
            return None

        try:
            normalized_id = UUID(str(parent_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Parent topic is invalid") from exc

        parent = db.get(Topic, normalized_id)
        if parent is None or parent.account_id != account_id:
            raise HTTPException(status_code=404, detail="Parent topic not found")
        return normalized_id
