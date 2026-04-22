from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.db.session import SessionLocal
from backend.models.base.enums import InteractionType, ShareLevel
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person


class InteractionService:
    TYPE_MAP = {
        "TALK": InteractionType.TALK,
        "CHAT": InteractionType.TALK,
        "MEETING": InteractionType.MEETING,
        "CALL": InteractionType.MESSAGE,
        "MESSAGE": InteractionType.MESSAGE,
        "OBSERVATION": InteractionType.EVENT,
        "EVENT": InteractionType.EVENT,
    }

    SHARE_LEVEL_MAP = {
        "SHARED": ShareLevel.SHARED,
        "PARTIAL": ShareLevel.PARTIAL,
        "WITHHELD": ShareLevel.WITHHELD,
    }

    TYPE_LABELS = {
        InteractionType.TALK: "会話",
        InteractionType.MEETING: "対面",
        InteractionType.MESSAGE: "メッセージ / 通話",
        InteractionType.EVENT: "出来事メモ",
    }

    SHARE_LEVEL_LABELS = {
        ShareLevel.SHARED: "話した",
        ShareLevel.PARTIAL: "一部だけ話した",
        ShareLevel.WITHHELD: "話していない",
    }

    def record_interaction(
        self,
        person_id: str,
        interaction_type,
        content: str | None = None,
        note: str | None = None,
        community_id: str | None = None,
        topic_id: str | None = None,
        share_level: str | int = ShareLevel.SHARED,
        occurred_at: datetime | None = None,
        tag_ids: list[str] | None = None,
    ):
        db: Session = SessionLocal()
        try:
            person = db.get(Person, person_id)
            if person is None:
                raise HTTPException(status_code=404, detail="Person not found")

            community_uuid = self._validate_optional_reference(
                db=db,
                model=Community,
                record_id=community_id,
                detail="Community not found",
            )
            topic_uuid = self._validate_optional_reference(
                db=db,
                model=Topic,
                record_id=topic_id,
                detail="Topic not found",
            )

            interaction = Interaction(
                person_id=person_id,
                community_id=community_uuid,
                topic_id=topic_uuid,
                type=self._normalize_interaction_type(interaction_type),
                share_level=self._normalize_share_level(share_level),
                occurred_at=occurred_at or datetime.now(timezone.utc),
                content=content.strip() if content else None,
                note=note.strip() if note else None,
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            return interaction
        finally:
            db.close()

    def list_interactions(
        self,
        person_id: str | None = None,
        community_id: str | None = None,
        topic_id: str | None = None,
        share_level: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
    ):
        db: Session = SessionLocal()
        try:
            query = self._base_query(db)

            if person_id:
                person = db.get(Person, person_id)
                if person is None:
                    raise HTTPException(status_code=404, detail="Person not found")
                query = query.filter(Interaction.person_id == person_id)

            if community_id:
                community_uuid = self._validate_optional_reference(
                    db=db,
                    model=Community,
                    record_id=community_id,
                    detail="Community not found",
                )
                query = query.filter(Interaction.community_id == community_uuid)

            if topic_id:
                topic_uuid = self._validate_optional_reference(
                    db=db,
                    model=Topic,
                    record_id=topic_id,
                    detail="Topic not found",
                )
                query = query.filter(Interaction.topic_id == topic_uuid)

            if share_level:
                query = query.filter(
                    Interaction.share_level == self._normalize_share_level(share_level)
                )

            if search and search.strip():
                keyword = f"%{search.strip()}%"
                query = query.filter(
                    Interaction.content.ilike(keyword) | Interaction.note.ilike(keyword)
                )

            if date_from:
                query = query.filter(Interaction.occurred_at >= date_from)

            if date_to:
                query = query.filter(Interaction.occurred_at <= date_to)

            if limit:
                query = query.limit(limit)

            interactions = query.all()
            return [self.serialize_interaction(interaction) for interaction in interactions]
        finally:
            db.close()

    def get_person_dashboard(self, person_id: str):
        db: Session = SessionLocal()
        try:
            person = (
                db.query(Person)
                .options(joinedload(Person.primary_community))
                .filter(Person.id == person_id)
                .first()
            )
            if person is None:
                raise HTTPException(status_code=404, detail="Person not found")

            interactions = (
                self._base_query(db)
                .filter(Interaction.person_id == person.id)
                .all()
            )
            serialized = [self.serialize_interaction(interaction) for interaction in interactions]
            share_counts = Counter(item["share_level"] for item in serialized)

            return {
                "person": {
                    "id": str(person.id),
                    "name": person.name,
                    "primary_community_id": (
                        str(person.primary_community_id) if person.primary_community_id else None
                    ),
                    "primary_community_path": self._build_path(person.primary_community)
                    if person.primary_community
                    else None,
                },
                "overview": {
                    "interaction_count": len(serialized),
                    "latest_occurred_at": serialized[0]["occurred_at"] if serialized else None,
                    "shared_count": share_counts.get("SHARED", 0),
                    "partial_count": share_counts.get("PARTIAL", 0),
                    "withheld_count": share_counts.get("WITHHELD", 0),
                },
                "share_summary": [
                    {
                        "share_level": level.name,
                        "label": self.SHARE_LEVEL_LABELS[level],
                        "count": share_counts.get(level.name, 0),
                    }
                    for level in (ShareLevel.SHARED, ShareLevel.PARTIAL, ShareLevel.WITHHELD)
                ],
                "top_topics": self._summarize_dimension(
                    interactions=serialized,
                    id_key="topic_id",
                    label_key="topic_path",
                ),
                "top_communities": self._summarize_dimension(
                    interactions=serialized,
                    id_key="community_id",
                    label_key="community_path",
                ),
                "recent_interactions": serialized[:6],
                "conversation_prep": {
                    "shared_topics": self._collect_topic_examples(serialized, "SHARED"),
                    "partial_topics": self._collect_topic_examples(serialized, "PARTIAL"),
                    "withheld_topics": self._collect_topic_examples(serialized, "WITHHELD"),
                    "recent_notes": self._collect_recent_notes(serialized),
                },
            }
        finally:
            db.close()

    def serialize_interaction(self, interaction: Interaction):
        interaction_type = InteractionType(interaction.type)
        share_level = ShareLevel(interaction.share_level)
        return {
            "id": str(interaction.id),
            "person_id": str(interaction.person_id),
            "person_name": interaction.person.name if interaction.person else "",
            "community_id": str(interaction.community_id) if interaction.community_id else None,
            "community_name": interaction.community.name if interaction.community else None,
            "community_path": self._build_path(interaction.community) if interaction.community else None,
            "topic_id": str(interaction.topic_id) if interaction.topic_id else None,
            "topic_name": interaction.topic.name if interaction.topic else None,
            "topic_path": self._build_path(interaction.topic) if interaction.topic else None,
            "interaction_type": interaction_type.name,
            "interaction_type_label": self.TYPE_LABELS.get(interaction_type, interaction_type.name),
            "share_level": share_level.name,
            "share_level_label": self.SHARE_LEVEL_LABELS.get(share_level, share_level.name),
            "occurred_at": interaction.occurred_at.isoformat() if interaction.occurred_at else None,
            "content": interaction.content,
            "note": interaction.note,
            "created_at": interaction.created_at.isoformat(),
        }

    def _base_query(self, db: Session):
        return (
            db.query(Interaction)
            .options(
                joinedload(Interaction.person),
                joinedload(Interaction.community).joinedload(Community.parent),
                joinedload(Interaction.topic).joinedload(Topic.parent),
            )
            .order_by(
                Interaction.occurred_at.desc().nullslast(),
                Interaction.created_at.desc(),
            )
        )

    def _build_path(self, record):
        nodes = []
        current = record
        while current is not None:
            nodes.append(current.name)
            current = current.parent
        return " / ".join(reversed(nodes))

    def _summarize_dimension(self, interactions, id_key: str, label_key: str):
        buckets: dict[str, dict[str, int | str]] = {}
        for item in interactions:
            bucket_id = item.get(id_key)
            bucket_label = item.get(label_key)
            if not bucket_id or not bucket_label:
                continue

            if bucket_id not in buckets:
                buckets[bucket_id] = {
                    "id": bucket_id,
                    "label": bucket_label,
                    "count": 0,
                    "shared_count": 0,
                    "partial_count": 0,
                    "withheld_count": 0,
                }

            buckets[bucket_id]["count"] += 1
            if item["share_level"] == "SHARED":
                buckets[bucket_id]["shared_count"] += 1
            elif item["share_level"] == "PARTIAL":
                buckets[bucket_id]["partial_count"] += 1
            elif item["share_level"] == "WITHHELD":
                buckets[bucket_id]["withheld_count"] += 1

        return sorted(
            buckets.values(),
            key=lambda bucket: (-int(bucket["count"]), str(bucket["label"])),
        )[:5]

    def _collect_topic_examples(self, interactions, share_level: str):
        seen = set()
        examples = []
        for item in interactions:
            if item["share_level"] != share_level:
                continue

            topic_label = item["topic_path"] or "話題未設定"
            community_label = item["community_path"] or "場未設定"
            dedupe_key = (topic_label, community_label)
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            examples.append(
                {
                    "topic": topic_label,
                    "community": community_label,
                    "occurred_at": item["occurred_at"],
                }
            )
            if len(examples) >= 5:
                break

        return examples

    def _collect_recent_notes(self, interactions):
        notes = []
        for item in interactions:
            note_text = item["note"] or item["content"]
            if not note_text:
                continue

            notes.append(
                {
                    "text": note_text,
                    "topic": item["topic_path"] or "話題未設定",
                    "share_level": item["share_level"],
                    "share_level_label": item["share_level_label"],
                    "occurred_at": item["occurred_at"],
                }
            )
            if len(notes) >= 5:
                break

        return notes

    def _normalize_interaction_type(self, interaction_type):
        if isinstance(interaction_type, int):
            return interaction_type

        key = str(interaction_type).strip().upper()
        if key not in self.TYPE_MAP:
            raise HTTPException(status_code=400, detail="Unsupported interaction type")
        return self.TYPE_MAP[key]

    def _normalize_share_level(self, share_level):
        if isinstance(share_level, int):
            return share_level

        key = str(share_level).strip().upper()
        if key not in self.SHARE_LEVEL_MAP:
            raise HTTPException(status_code=400, detail="Unsupported share level")
        return self.SHARE_LEVEL_MAP[key]

    def _validate_optional_reference(self, db: Session, model, record_id: str | None, detail: str):
        if not record_id:
            return None

        try:
            normalized_id = UUID(str(record_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=detail) from exc

        record = db.get(model, normalized_id)
        if record is None:
            raise HTTPException(status_code=404, detail=detail)
        return normalized_id
