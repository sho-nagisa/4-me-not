from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base.base import BaseModel


class Person(BaseModel):
    """
    Person（人の不変コア）
    - 実在人物・キャラクター・抽象的対象を含めた最小単位
    - 状態や印象は持たない（Profile / Insight に分離）
    """

    __tablename__ = "persons"

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
