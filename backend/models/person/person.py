from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID

from backend.models.base.base import BaseModel


class Person(BaseModel):
    """
    Person（人の不変コア）
    - 実在人物・キャラクター・抽象的対象を含めた最小単位
    - 状態や印象は持たない（Profile / Insight に分離）
    """

    __tablename__ = "persons"
    __table_args__ = {"schema": "formegot"}

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="表示名・呼称"
    )

    canonical_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="正規化名（重複防止・検索用）"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="人物の概要・補足説明"
    )

    primary_community_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="SET NULL"),
        nullable=True,
        comment="主な所属コミュニティ"
    )

    primary_community = relationship(
        "Community",
        foreign_keys=[primary_community_id],
        backref="primary_members"
    )
