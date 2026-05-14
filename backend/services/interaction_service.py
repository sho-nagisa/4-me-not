from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from backend.app.account_context import get_current_account_id
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
            account_id = get_current_account_id()
            person_uuid = self._normalize_uuid(person_id, "Person is invalid")
            person = (
                db.query(Person)
                .filter(Person.id == person_uuid, Person.account_id == account_id)
                .first()
            )
            if person is None or person.is_hidden:
                raise HTTPException(status_code=404, detail="Person not found")

            community_uuid = self._validate_optional_reference(
                db=db,
                model=Community,
                record_id=community_id,
                detail="Community not found",
                account_id=account_id,
            )
            topic_uuid = self._validate_optional_reference(
                db=db,
                model=Topic,
                record_id=topic_id,
                detail="Topic not found",
                account_id=account_id,
            )

            interaction = Interaction(
                account_id=account_id,
                person_id=person_uuid,
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
            account_id = get_current_account_id()
            query = self._base_query(db, account_id=account_id)

            if person_id:
                person_uuid = self._normalize_uuid(person_id, "Person is invalid")
                person = (
                    db.query(Person)
                    .filter(Person.id == person_uuid, Person.account_id == account_id)
                    .first()
                )
                if person is None or person.is_hidden:
                    raise HTTPException(status_code=404, detail="Person not found")
                query = query.filter(Interaction.person_id == person_uuid)

            if community_id:
                community_uuid = self._validate_optional_reference(
                    db=db,
                    model=Community,
                    record_id=community_id,
                    detail="Community not found",
                    account_id=account_id,
                )
                query = query.filter(Interaction.community_id == community_uuid)

            if topic_id:
                topic_uuid = self._validate_optional_reference(
                    db=db,
                    model=Topic,
                    record_id=topic_id,
                    detail="Topic not found",
                    account_id=account_id,
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
            path_cache = {}
            return [
                self.serialize_interaction(interaction, path_cache=path_cache)
                for interaction in interactions
            ]
        finally:
            db.close()

    def get_interaction_overview(self, recent_limit: int = 4, person_limit: int = 7):
        db: Session = SessionLocal()
        try:
            account_id = get_current_account_id()
            visible_query = (
                db.query(Interaction)
                .join(Person, Interaction.person_id == Person.id)
                .filter(
                    Interaction.account_id == account_id,
                    Person.account_id == account_id,
                    Person.is_hidden.is_(False),
                )
            )
            total_count = visible_query.count()

            recent_interactions = (
                self._base_query(db, account_id=account_id)
                .limit(recent_limit)
                .all()
            )
            path_cache = {}
            serialized_recent = [
                self.serialize_interaction(interaction, path_cache=path_cache)
                for interaction in recent_interactions
            ]

            interaction_count = func.count(Interaction.id)
            person_counts = (
                db.query(
                    Person.id.label("person_id"),
                    interaction_count.label("interaction_count"),
                )
                .outerjoin(
                    Interaction,
                    and_(
                        Interaction.person_id == Person.id,
                        Interaction.account_id == account_id,
                    ),
                )
                .filter(Person.account_id == account_id, Person.is_hidden.is_(False))
                .group_by(Person.id, Person.name)
                .order_by(interaction_count.desc(), Person.name.asc())
                .limit(person_limit)
                .all()
            )

            return {
                "total_count": total_count,
                "recent_interactions": serialized_recent,
                "person_counts": [
                    {
                        "person_id": str(row.person_id),
                        "count": int(row.interaction_count),
                    }
                    for row in person_counts
                ],
            }
        finally:
            db.close()

    def get_person_dashboard(self, person_id: str):
        db: Session = SessionLocal()
        try:
            account_id = get_current_account_id()
            person_uuid = self._normalize_uuid(person_id, "Person is invalid")
            person = (
                db.query(Person)
                .options(joinedload(Person.primary_community))
                .filter(
                    Person.id == person_uuid,
                    Person.account_id == account_id,
                    Person.is_hidden.is_(False),
                )
                .first()
            )
            if person is None:
                raise HTTPException(status_code=404, detail="Person not found")

            interactions = (
                self._base_query(db, account_id=account_id)
                .filter(Interaction.person_id == person.id)
                .all()
            )
            path_cache = {}
            serialized = [
                self.serialize_interaction(interaction, path_cache=path_cache)
                for interaction in interactions
            ]
            share_counts = Counter(item["share_level"] for item in serialized)

            return {
                "person": {
                    "id": str(person.id),
                    "name": person.name,
                    "primary_community_id": (
                        str(person.primary_community_id)
                        if person.primary_community_id and person.primary_community and not person.primary_community.is_hidden
                        else None
                    ),
                    "primary_community_path": self._build_path(person.primary_community)
                    if person.primary_community and not person.primary_community.is_hidden
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

    def serialize_interaction(self, interaction: Interaction, path_cache: dict | None = None):
        interaction_type = InteractionType(interaction.type)
        share_level = ShareLevel(interaction.share_level)
        visible_community = interaction.community if interaction.community and not interaction.community.is_hidden else None

        return {
            "id": str(interaction.id),
            "person_id": str(interaction.person_id),
            "person_name": interaction.person.name if interaction.person else "",
            "community_id": str(interaction.community_id) if visible_community else None,
            "community_name": visible_community.name if visible_community else None,
            "community_path": self._build_path(visible_community, path_cache) if visible_community else None,
            "topic_id": str(interaction.topic_id) if interaction.topic_id else None,
            "topic_name": interaction.topic.name if interaction.topic else None,
            "topic_path": self._build_path(interaction.topic, path_cache) if interaction.topic else None,
            "interaction_type": interaction_type.name,
            "interaction_type_label": self.TYPE_LABELS.get(interaction_type, interaction_type.name),
            "share_level": share_level.name,
            "share_level_label": self.SHARE_LEVEL_LABELS.get(share_level, share_level.name),
            "occurred_at": interaction.occurred_at.isoformat() if interaction.occurred_at else None,
            "content": interaction.content,
            "note": interaction.note,
            "created_at": interaction.created_at.isoformat(),
        }

    def _base_query(self, db: Session, account_id: UUID | None = None):
        scoped_account_id = account_id or get_current_account_id()
        return (
            db.query(Interaction)
            .join(Person, Interaction.person_id == Person.id)
            .filter(
                Interaction.account_id == scoped_account_id,
                Person.account_id == scoped_account_id,
                Person.is_hidden.is_(False),
            )
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

    def _build_path(self, record, path_cache: dict | None = None):
        if record is None:
            return None

        cache_key = (record.__class__.__name__, str(record.id))
        if path_cache is not None and cache_key in path_cache:
            return path_cache[cache_key]

        nodes = []
        current = record
        while current is not None:
            if hasattr(current, "is_hidden") and current.is_hidden:
                current = current.parent
                continue
            nodes.append(current.name)
            current = current.parent
        path = " / ".join(reversed(nodes))
        if path_cache is not None:
            path_cache[cache_key] = path
        return path

    def _normalize_uuid(self, record_id: str, detail: str) -> UUID:
        try:
            return UUID(str(record_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=detail) from exc

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

    def _validate_optional_reference(
        self,
        db: Session,
        model,
        record_id: str | None,
        detail: str,
        account_id: UUID,
    ):
        if not record_id:
            return None

        try:
            normalized_id = UUID(str(record_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=detail) from exc

        record = db.get(model, normalized_id)
        if record is None:
            raise HTTPException(status_code=404, detail=detail)
        if getattr(record, "account_id", None) != account_id:
            raise HTTPException(status_code=404, detail=detail)
        if hasattr(record, "is_hidden") and record.is_hidden:
            raise HTTPException(status_code=404, detail=detail)
        return normalized_id
