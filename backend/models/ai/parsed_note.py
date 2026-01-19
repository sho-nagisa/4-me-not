from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class ParsedNote(BaseModel):
    """
    AI パース結果（構造化メモ）
    - Interaction / Note 等の解析結果
    """

    __tablename__ = "parsed_notes"

    source_id: Mapped[str] = mapped_column(
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        comment="解析元（例: Interaction）"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI による構造化結果（JSON / 要約文など）"
    )

    metadata_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_metadata.id", ondelete="SET NULL"),
        nullable=True
    )

    metadata = relationship("AIMetadata", backref="parsed_notes")
