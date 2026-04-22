from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID

from backend.models.base.base import BaseModel
from backend.models.base.enums import InteractionType, ShareLevel


class Interaction(BaseModel):
    __tablename__ = "interactions"
    __table_args__ = {"schema": "formegot"}

    person_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.persons.id", ondelete="CASCADE"),
        nullable=False
    )

    community_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="SET NULL"),
        nullable=True
    )

    topic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.topics.id", ondelete="SET NULL"),
        nullable=True
    )

    type: Mapped[InteractionType] = mapped_column(
        Integer,
        nullable=False,
        comment="やり取りの種類"
    )

    share_level: Mapped[ShareLevel] = mapped_column(
        Integer,
        nullable=False,
        default=ShareLevel.SHARED,
        comment="どこまで話したか"
    )

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="実際にやり取りした日時"
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="やり取り内容"
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="補足メモ"
    )

    person = relationship("Person", backref="interactions")
    community = relationship("Community", backref="interactions")
    topic = relationship("Topic", backref="interactions")
