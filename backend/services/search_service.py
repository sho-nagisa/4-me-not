from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import os
import re
import unicodedata
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session, joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument


logger = logging.getLogger(__name__)


TARGET_INTERACTION = "interaction"
TARGET_PERSON = "person"
TARGET_COMMUNITY = "community"
TARGET_TOPIC = "topic"
ALLOWED_TARGET_TYPES = {
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_COMMUNITY,
    TARGET_TOPIC,
}
GROUP_KEYS = {
    TARGET_INTERACTION: "interactions",
    TARGET_PERSON: "people",
    TARGET_COMMUNITY: "communities",
    TARGET_TOPIC: "topics",
}


class SearchEmbeddingProvider:
    fallback_model = "local-hash-v1"

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_model = os.environ.get(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        )
        self.dimension = int(os.environ.get("SEARCH_FALLBACK_EMBEDDING_DIM", "384"))

    @property
    def preferred_model(self) -> str:
        return self.openai_model if self.api_key else self.fallback_model

    def embed(self, text: str) -> tuple[list[float], str]:
        if self.api_key:
            try:
                return self._embed_with_openai(text), self.openai_model
            except Exception:
                logger.exception("OpenAI embedding failed; using local fallback")

        return self._embed_locally(text), self.fallback_model

    def _embed_with_openai(self, text: str) -> list[float]:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.openai_model,
                "input": text[:12000],
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        embedding = payload["data"][0]["embedding"]
        return [float(value) for value in embedding]

    def _embed_locally(self, text: str) -> list[float]:
        normalized = normalize_text(text)
        features: Counter[str] = Counter()

        for token in re.findall(r"[\w]+", normalized):
            if len(token) > 1:
                features[token] += 2

        compact = re.sub(r"\s+", "", normalized)
        for width, weight in ((2, 1), (3, 2), (4, 1)):
            if len(compact) < width:
                continue
            for index in range(len(compact) - width + 1):
                features[compact[index : index + width]] += weight

        vector = [0.0] * self.dimension
        for feature, weight in features.items():
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            vector[bucket] += float(weight)

        return normalize_vector(vector)


class SearchService:
    def __init__(self, embedding_provider: SearchEmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or SearchEmbeddingProvider()

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

        db: Session = SessionLocal()
        try:
            account_id = get_current_account_id()
            documents = self._load_candidate_documents(
                db=db,
                account_id=account_id,
                target_types=selected_target_types,
                limit=max(limit * 50, 300),
            )
            reference_maps = self._build_reference_maps(db, account_id, documents)
            results = []

            for document in documents:
                if not self._document_is_visible(document, reference_maps):
                    continue

                semantic_score = cosine_similarity(
                    query_embedding,
                    parse_embedding(document.embedding_json),
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
                    self._serialize_result(
                        document=document,
                        score=score,
                        semantic_score=semantic_score,
                        keyword_score=keyword_score,
                        recency_score=recency_score,
                        reference_maps=reference_maps,
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

            return {
                "query": query,
                "embedding_model": query_embedding_model,
                "results": limited_results,
                "groups": self._group_results(limited_results),
            }
        finally:
            db.close()

    def index_interaction(self, interaction_id: str) -> None:
        db: Session = SessionLocal()
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

    def rebuild_account_index(self) -> dict[str, int]:
        db: Session = SessionLocal()
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

            for person in people:
                self._index_person(db, account_id, person)
            for community in communities:
                self._index_community(db, account_id, community)
            for topic in topics:
                self._index_topic(db, account_id, topic)
            for interaction in interactions:
                self._index_interaction(db, account_id, interaction)

            db.commit()
            return {
                "people": len(people),
                "communities": len(communities),
                "topics": len(topics),
                "interactions": len(interactions),
            }
        finally:
            db.close()

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

    def _group_results(self, results: list[dict]) -> dict[str, list[dict]]:
        grouped = {
            "people": [],
            "interactions": [],
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
                "communities": [],
                "topics": [],
            },
        }


def normalize_uuid(value: str, detail: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=detail) from exc


def normalize_text(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").casefold()


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def parse_embedding(value: str | None) -> list[float]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [float(item) for item in parsed if isinstance(item, int | float)]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    score = sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
    return max(0.0, min(1.0, score))


def calculate_keyword_score(query: str, document: SearchDocument) -> float:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return 0.0

    title = normalize_text(document.title)
    summary = normalize_text(document.summary)
    body = normalize_text(document.search_text)
    combined = "\n".join([title, summary, body])
    terms = build_query_terms(normalized_query)
    if not terms:
        return 0.0

    matched_terms = sum(1 for term in terms if term in combined)
    coverage = matched_terms / len(terms)
    exact_boost = 0.35 if normalized_query in combined else 0.0
    title_boost = 0.20 if normalized_query in title else 0.0
    if not title_boost and any(term in title for term in terms):
        title_boost = 0.10

    return min(1.0, exact_boost + title_boost + 0.55 * coverage)


def build_query_terms(query: str) -> set[str]:
    terms = {token for token in re.findall(r"[\w]+", query) if len(token) > 1}
    compact = re.sub(r"\s+", "", query)
    for width in (2, 3):
        if len(compact) < width:
            continue
        for index in range(len(compact) - width + 1):
            terms.add(compact[index : index + width])
            if len(terms) >= 80:
                return terms
    return terms


def calculate_recency_score(occurred_at: datetime | None) -> float:
    if occurred_at is None:
        return 0.0
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    days = max(0, (datetime.now(timezone.utc) - occurred_at).days)
    return 1 / (1 + days / 180)


def extract_snippet(query: str, document: SearchDocument, length: int = 180) -> str:
    source = document.summary or document.search_text
    compact_source = compact_text(source, 1000)
    folded_source = normalize_text(compact_source)
    folded_query = normalize_text(query)
    index = folded_source.find(folded_query) if folded_query else -1
    if index < 0:
        return compact_text(compact_source, length)

    start = max(0, index - 50)
    end = min(len(compact_source), index + len(query) + 100)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(compact_source) else ""
    return f"{prefix}{compact_source[start:end]}{suffix}"


def compact_text(value: str | None, max_length: int = 200) -> str | None:
    if not value:
        return None
    compacted = re.sub(r"\s+", " ", value).strip()
    if len(compacted) <= max_length:
        return compacted
    return compacted[: max_length - 1].rstrip() + "..."


def first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def join_search_parts(parts: list[str | None]) -> str:
    return "\n".join(part.strip() for part in parts if part and part.strip())
