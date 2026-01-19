from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class InteractionTag(BaseModel):
    """
    Interaction × Tag 中間
    """

    __tablename__ = "interaction_tags"
    __table_args__ = (
        UniqueConstraint("interaction_id", "tag_id", name="uq_interaction_tag"),
    )

    interaction_id: Mapped[str] = mapped_column(
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False
    )

    tag_id: Mapped[str] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False
    )

    interaction = relationship("Interaction", backref="interaction_tags")
    tag = relationship("Tag", backref="interaction_tags")
