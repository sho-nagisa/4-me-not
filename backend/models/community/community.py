from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class Community(BaseModel):
    __tablename__ = "communities"
    __table_args__ = {"schema": "formegot"}

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="コミュニティ名",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="コミュニティ説明",
    )

    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="管理画面から非表示にするフラグ",
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="SET NULL"),
        nullable=True,
        comment="親コミュニティ",
    )

    parent: Mapped["Community | None"] = relationship(
        "Community",
        remote_side="Community.id",
        backref="children",
    )
