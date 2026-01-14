from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, date

from sqlmodel import SQLModel, Field, Relationship


class Interaction(SQLModel, table=True):
    __tablename__ = "interactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 文脈の核
    person_id: UUID = Field(foreign_key="persons.id", index=True)
    community_id: UUID = Field(foreign_key="communities.id", index=True)

    # 内容
    occurred_on: date = Field(index=True)
    summary: str                          # 何を話したか（要約）
    memo: Optional[str] = None            # 生メモ（AI前）

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    topics: list["Topic"] = Relationship(back_populates="interaction")
