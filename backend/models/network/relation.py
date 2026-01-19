from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel
from models.base.enums import RelationType


class Relation(BaseModel):
    """
    Person × Person の相関ネットワーク
    - 客観・主観どちらも扱える
    - 人間関係の「構造」を表す
    """

    __tablename__ = "relations"
    __table_args__ = (
        UniqueConstraint("from_person_id", "to_person_id", name="uq_relation_pair"),
    )

    from_person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False
    )

    to_person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False
    )

    type: Mapped[RelationType] = mapped_column(
        Integer,
        nullable=False,
        comment="関係タイプ"
    )

    strength: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="関係強度（例: 1〜5）"
    )

    from_person = relationship(
        "Person",
        foreign_keys=[from_person_id],
        backref="outgoing_relations"
    )

    to_person = relationship(
        "Person",
        foreign_keys=[to_person_id],
        backref="incoming_relations"
    )
