from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base.base import BaseModel


class Reminder(BaseModel):
    """
    リマインド定義
    - 行動・確認・フォローアップ用
    """

    __tablename__ = "reminders"
    __table_args__ = {"schema": "formegot"}

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

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
