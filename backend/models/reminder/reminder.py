from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from models.base.base import BaseModel


class Reminder(BaseModel):
    """
    リマインド定義
    - 行動・確認・フォローアップ用
    """

    __tablename__ = "reminders"

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    remind_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="通知予定時刻"
    )
