from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class PersonTag(SQLModel, table=True):
    __tablename__ = "person_tags"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    person_id: UUID = Field(foreign_key="persons.id")
    tag_id: UUID = Field(foreign_key="tags.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
