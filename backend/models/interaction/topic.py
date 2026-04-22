from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID

from backend.models.base.base import BaseModel


class Topic(BaseModel):
    __tablename__ = "topics"
    __table_args__ = {"schema": "formegot"}

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="旧カラム互換用タイトル"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="話題名"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="話題の補足"
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.topics.id", ondelete="SET NULL"),
        nullable=True,
        comment="親話題"
    )

    parent: Mapped["Topic | None"] = relationship(
        "Topic",
        remote_side="Topic.id",
        backref="children"
    )
