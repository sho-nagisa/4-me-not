from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime

from pyparsing import Optional
from sqlmodel import SQLModel, Field, Relationship

from backend.models.task.relationship_task import RelationshipTask


class TaskHistory(SQLModel, table=True):
    __tablename__ = "task_histories"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    task_id: UUID = Field(foreign_key="relationship_tasks.id", index=True)

    action: str                              # created / done / skipped / updated
    note: Optional[str] = None               # 補足（なぜスキップ等）

    acted_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    task: "RelationshipTask" = Relationship(back_populates="histories")
