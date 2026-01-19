from sqlalchemy import Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel
from models.base.enums import InsightType


class Insight(BaseModel):
    """
    Insight（気づき・好き嫌い・直感的評価）
    - Interaction などから生まれる内省結果
    - 事実ではなく「解釈・印象」
    """

    __tablename__ = "insights"

    person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False
    )

    type: Mapped[InsightType] = mapped_column(
        Integer,
        nullable=False,
        comment="インサイト種別"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="気づきの内容"
    )

    confidence: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="確信度（例: 1〜5）"
    )

    person = relationship("Person", backref="insights")
