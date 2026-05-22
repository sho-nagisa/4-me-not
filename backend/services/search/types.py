from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


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
