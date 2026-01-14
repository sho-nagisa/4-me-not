from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, date

from sqlmodel import SQLModel, Field, Relationship


class RelationshipTask(SQLModel, table=True):
    __tablename__ = "relationship_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 文脈の核（必須）
    person_id: UUID = Field(foreign_key="persons.id", index=True)
    community_id: UUID = Field(foreign_key="communities.id", index=True)

    # タスク内容
    title: str                               # 例：論文の進捗を聞く
    description: Optional[str] = None
    due_date: Optional[date] = Field(index=True)

    # 状態管理
    status: str = Field(default="todo", index=True)  # todo / done / skipped
    priority: int = Field(default=3, ge=1, le=5)

    # 由来（AIか人か）
    source: str = Field(default="human")     # human / ai

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    histories: list["TaskHistory"] = Relationship(back_populates="task")
