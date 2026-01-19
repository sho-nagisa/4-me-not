from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class Tag(BaseModel):
    """
    汎用タグ
    - Person / Interaction / Insight などに横断的に付与される
    - 意味は持つが、文脈は持たない
    """

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="タグ名（表示用）"
    )

    slug: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        comment="正規化タグ名（検索・統合用）"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="タグの説明・意味"
    )
