from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, date

from sqlmodel import SQLModel, Field, Relationship

from backend.models.interaction.interaction import Interaction


class Topic(SQLModel, table=True):
    __tablename__ = "topics"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    interaction_id: UUID = Field(foreign_key="interactions.id", index=True)

    title: str                            # 話題（例：転職活動）
    expires_on: Optional[date] = None     # 賞味期限

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    interaction: "Interaction" = Relationship(back_populates="topics")
