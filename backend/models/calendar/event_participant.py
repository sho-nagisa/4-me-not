from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class EventParticipant(BaseModel):
    __tablename__ = "event_participants"
    __table_args__ = (
        UniqueConstraint(
            "calendar_event_id",
            "person_id",
            "email",
            name="uq_event_participants_identity",
        ),
        {"schema": "formegot"},
    )

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    calendar_event_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.calendar_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    person_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.persons.id", ondelete="SET NULL"),
        nullable=True,
    )

    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="attendee")
    is_inferred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    calendar_event = relationship("CalendarEvent", back_populates="participants")
    person = relationship("Person")
