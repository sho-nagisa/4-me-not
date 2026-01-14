from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from backend.models.community.community_tree import CommunityTree
from sqlmodel import SQLModel, Field, Relationship


class Community(SQLModel, table=True):
    __tablename__ = "communities"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(index=True)
    description: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    tree: Optional["CommunityTree"] = Relationship(
        back_populates="community",
        sa_relationship_kwargs={"uselist": False}
    )
