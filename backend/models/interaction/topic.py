from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from models.base.base import BaseModel


class Topic(BaseModel):
    """
    話題（賞味期限あり）
    """

    __tablename__ = "topics"

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    expires_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="話題の有効期限"
    )
