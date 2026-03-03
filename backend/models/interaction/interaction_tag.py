from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class InteractionTag(BaseModel):
    """
    Interaction × Tag 中間
    """

    __tablename__ = "interaction_tags"
    __table_args__ = (
        UniqueConstraint("interaction_id", "tag_id", name="uq_interaction_tag"),
        {"schema": "formegot"},
    )

    interaction_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.interactions.id", ondelete="CASCADE"),
        nullable=False
    )

    tag_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.tags.id", ondelete="CASCADE"),
        nullable=False
    )

    interaction = relationship("Interaction", backref="interaction_tags")
    tag = relationship("Tag", backref="interaction_tags")
