from sqlalchemy import Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel
from models.base.enums import InteractionType


class Interaction(BaseModel):
    """
    会話・接触ログ（文脈付き）
    """

    __tablename__ = "interactions"

    person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
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
