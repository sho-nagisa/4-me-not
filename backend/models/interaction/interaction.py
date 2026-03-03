from sqlalchemy import Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel
from backend.models.base.enums import InteractionType


class Interaction(BaseModel):
    """
    会話・接触ログ（文脈付き）
    """

    __tablename__ = "interactions"
    __table_args__ = {"schema": "formegot"}

    person_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.persons.id", ondelete="CASCADE"),
        nullable=False
    )

    type: Mapped[InteractionType] = mapped_column(
        Integer,
        nullable=False,
        comment="接触タイプ"
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="会話内容・出来事"
    )

    person = relationship("Person", backref="interactions")
