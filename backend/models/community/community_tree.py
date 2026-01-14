from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship


class CommunityTree(SQLModel, table=True):
    __tablename__ = "community_trees"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    community_id: UUID = Field(
        foreign_key="communities.id",
        unique=True
    )

    parent_id: Optional[UUID] = Field(
        default=None,
        foreign_key="communities.id"
    )

    # relationships
    community: "Community" = Relationship(back_populates="tree")
