from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class Trigger(BaseModel):
    """
    Reminder の発火条件
    """

    __tablename__ = "reminder_triggers"
    __table_args__ = {"schema": "formegot"}

    reminder_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.reminders.id", ondelete="CASCADE"),
        nullable=False
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="time / calendar など"
    )

    reminder = relationship("Reminder", backref="triggers")
