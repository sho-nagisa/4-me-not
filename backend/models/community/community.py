from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class Community(BaseModel):
    """
    Community（集団・組織・グループ）
    - 階層構造を前提
    - 意味・役割は持つが、所属情報は持たない
    """

    __tablename__ = "communities"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="コミュニティ名"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="概要・説明"
    )

    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
        comment="親コミュニティ"
    )

    parent = relationship(
        "Community",
        remote_side="Community.id",
        backref="children"
    )
