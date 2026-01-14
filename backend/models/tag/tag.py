from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(index=True, unique=True)
    color: str = Field(default="#999999")   # UI用（任意）

    created_at: datetime = Field(default_factory=datetime.utcnow)
