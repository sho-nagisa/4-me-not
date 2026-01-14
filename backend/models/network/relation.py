from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class Relation(SQLModel, table=True):
    __tablename__ = "relations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 誰と誰の関係か（向きあり）
    from_person_id: UUID = Field(foreign_key="persons.id", index=True)
    to_person_id: UUID = Field(foreign_key="persons.id", index=True)

    # どの文脈での関係か（任意）
    community_id: Optional[UUID] = Field(
        default=None,
        foreign_key="communities.id",
        index=True
    )

    # 関係タイプ
    relation_type: str = Field(index=True)
    # 例:
    # - introduced_by
    # - close_friend
    # - mentor
    # - coworker
    # - family
    # - good_terms
    # - conflict

    strength: Optional[int] = Field(
        default=None, ge=1, le=5
    )  # 関係の強さ（主観）

    note: Optional[str] = None  # 補足（なぜそう思うか）

    source: str = Field(default="human")
    # human / ai / inferred

    created_at: datetime = Field(default_factory=datetime.utcnow)
