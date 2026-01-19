from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column

from models.base.base import BaseModel


class AIMetadata(BaseModel):
    """
    AI 推定メタ情報
    - 信頼度・モデル情報・推定元
    """

    __tablename__ = "ai_metadata"

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="使用した AI モデル名"
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="推定信頼度（0.0〜1.0）"
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="推定元（interaction / manual など）"
    )
