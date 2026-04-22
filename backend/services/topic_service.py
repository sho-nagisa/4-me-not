from uuid import UUID

from fastapi import HTTPException

from backend.db.session import SessionLocal
from backend.models.interaction.topic import Topic


class TopicService:
    def create_topic(
        self,
        name: str,
        description: str | None = None,
        parent_id: str | None = None,
    ):
        db = SessionLocal()
        try:
            normalized_parent_id = self._validate_parent_id(db, parent_id)
            topic = Topic(
                title=name,
                name=name,
                description=description,
                parent_id=normalized_parent_id,
            )
            db.add(topic)
            db.commit()
            db.refresh(topic)
            return topic
        finally:
            db.close()

    def list_topics(self):
        db = SessionLocal()
        try:
            topics = db.query(Topic).all()
            topics.sort(key=lambda item: self.get_path(item))
            return topics
        finally:
            db.close()

    def get_path(self, topic: Topic) -> str:
        db = SessionLocal()
        try:
            nodes = []
            current = db.get(Topic, topic.id)
            while current is not None:
                nodes.append(current.name)
                current = db.get(Topic, current.parent_id) if current.parent_id else None
            return " / ".join(reversed(nodes))
        finally:
            db.close()

    def _validate_parent_id(self, db, parent_id: str | None):
        if not parent_id:
            return None

        try:
            normalized_id = UUID(str(parent_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Parent topic is invalid") from exc

        parent = db.get(Topic, normalized_id)
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent topic not found")
        return normalized_id
