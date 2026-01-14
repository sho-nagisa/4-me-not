from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship


class Person(SQLModel, table=True):
    __tablename__ = "persons"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(index=True)
    gender: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    profile: Optional["PersonProfile"] = Relationship(
        back_populates="person",
        sa_relationship_kwargs={"uselist": False}
    )
