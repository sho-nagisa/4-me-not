from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class Person(BaseModel):
    __tablename__ = "persons"
    __table_args__ = {"schema": "formegot"}

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="表示名",
    )

    canonical_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="一意に扱うための名前",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="人物メモ",
    )

    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="管理画面から非表示にするフラグ",
    )

    primary_community_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="SET NULL"),
        nullable=True,
        comment="主な所属コミュニティ",
    )

    primary_community = relationship(
        "Community",
        foreign_keys=[primary_community_id],
        backref="primary_members",
    )
