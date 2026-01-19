from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from models.base.base import BaseModel


class CalendarEvent(BaseModel):
    """
    外部カレンダー予定（同期スナップショット）
    - Google Calendar 等との連携結果
    """

    __tablename__ = "calendar_events"

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="外部カレンダーのイベントID"
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    start_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="google / apple など"
    )
