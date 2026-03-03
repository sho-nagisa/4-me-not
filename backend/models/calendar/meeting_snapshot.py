from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class MeetingSnapshot(BaseModel):
    """
    直前あらすじ用スナップショット
    - 会う前に確認するための要約情報
    """

    __tablename__ = "meeting_snapshots"
    __table_args__ = {"schema": "formegot"}

    calendar_event_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.calendar_events.id", ondelete="CASCADE"),
        nullable=False
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="直前確認用の要約"
    )

    calendar_event = relationship(
        "CalendarEvent",
        backref="snapshots"
    )
