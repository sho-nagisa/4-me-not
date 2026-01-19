from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class PersonTag(BaseModel):
    """
    Person × Tag 中間テーブル
    - 人に付与されたタグ
    - 強度・理由などは持たせない（必要なら拡張）
    """

    __tablename__ = "person_tags"
    __table_args__ = (
        UniqueConstraint("person_id", "tag_id", name="uq_person_tag"),
    )

    person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False,
        comment="対象 Person"
    )

    tag_id: Mapped[str] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        comment="付与された Tag"
    )

    person = relationship(
        "Person",
        backref="person_tags",
        lazy="joined"
    )

    tag = relationship(
        "Tag",
        backref="person_tags",
        lazy="joined"
    )
